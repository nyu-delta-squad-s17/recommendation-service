# Copyright 2016, 2017 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from threading import Lock
from flask import Flask, Response, jsonify, request, json
from sqlalchemy import *
from sqlalchemy.exc import *
import uuid

# Create Flask application
app = Flask(__name__)

# Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409

# Lock for thread-safe counter increment
lock = Lock()

######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
    recommendations_url = request.base_url + "recommendations"
    return jsonify(name='Recommendations REST API Service',
                   version='0.1',
                   url=recommendations_url
                   ), HTTP_200_OK

######################################################################
# LIST ALL PRODUCT RECOMMENDATIONS
# CAN USE type AND product-id KEYWORDS TO QUERY THE LIST
######################################################################
@app.route('/recommendations', methods=['GET'])
def list_recommendations():
    """
    Basically prints out all the recommendations.
    """
    message = []
    request_type = request.args.get('type')
    request_product_id = request.args.get('product-id')
    # To mitigate query limit issues consider using session in sqlalchemy
    query_str = 'SELECT * FROM recommendations'
    if request_type and request_product_id:
        query_str += (' WHERE type=%s AND parent_product_id=%s' \
                      % (request_type, request_product_id))
    elif request_type:
        query_str += (' WHERE type=%s' % request_type)
    elif request_product_id:
        query_str += (' WHERE parent_product_id=%s' % request_product_id)
    try:
        results = conn.execute(query_str)
    except OperationalError:
        results = []
    for rec in results:
        message.append({'id': rec[0],
                        'parent_product_id': rec[1],
                        'related_product_id': rec[2],
                        'type': rec[3],
                        'priority': rec[4]})
    return reply(message, HTTP_200_OK)

######################################################################
# RETRIEVE Recommendations for a given recommendations ID
######################################################################
@app.route('/recommendations/<id>', methods=['GET'])
def get_recommendations(id):
    '''
    Given a ID, Output a single row of recommendations.
    '''

    message = {}
    results = conn.execute("SELECT * FROM recommendations WHERE id=%d" % (int(id)))
    for rec in results:
        message = {"id": rec[0],
                   "parent_product_id": rec[1],
                   "related_product_id": rec[2],
                   "type": rec[3],
                   "priority": rec[4]}
        rc = HTTP_200_OK
    if not message:
        message = {'error': 'Recommendation with id: %s was not found' % str(id)}
        rc = HTTP_404_NOT_FOUND

    return reply(message, rc)

######################################################################
# ADD A NEW PRODUCT RECOMMENDATIONS RELATIONSHIP
######################################################################
@app.route('/recommendations', methods=['POST'])
def create_recommendations():
    payload = request.get_json()
    if is_valid(payload):
        id = new_index()
        data[id] = {'id': id, 'name': payload['name'], 'recommendations': payload['recommendations']}
        message = data[id]
        rc = HTTP_201_CREATED
    else:
        message = { 'error' : 'Data is not valid' }
        rc = HTTP_400_BAD_REQUEST

    return reply(message, rc)

######################################################################
# UPDATE AN EXISTINT RECOMMENDATION RELATIONSHIP
######################################################################

@app.route('/recommendations/<int:id>', methods=['PUT'])
def update_recommendations(id):
    '''
    Given a Recommendation ID, update all the columns as from the payload
    '''

    if get_recommendations(id).status_code == 404:
        message = {'error': 'Recommendation with id: %s was not found' % str(id)}
        return reply(message, HTTP_404_NOT_FOUND)

    payload = json.loads(request.get_data())

    def validate(data):
        # Custom basic validation, should be refactored with is_valid
        valid = True
        if set(data.keys()) != set(['priority', 'related_product_id',
                                    'parent_product_id', 'type', 'id']):
            app.logger.error('Error: missing parameter')
            valid = False

        if id != data['id']:
            app.logger.error('Error: id does not match')
            valid = False

        for _id in (data['related_product_id'], data['related_product_id']):
            # Currently we cannot validate product_ID
            pass

        return valid

    if validate(payload):
        conn.execute("UPDATE recommendations \
                      SET type=\"%s\", priority=%d \
                      WHERE parent_product_id=%d \
                      AND related_product_id=%d AND id=%d"
                     % (payload['type'],
                        payload['priority'],
                        payload['parent_product_id'],
                        payload['related_product_id'],
                        payload['id']
                        ))
        return get_recommendations(id)

    else:
        message = {'error': 'Invalid Request'}
        rc = HTTP_400_BAD_REQUEST
        return reply(message, rc)

######################################################################
# DELETE A PRODUCT RECOMMENDATION
######################################################################
@app.route('/recommendations/<id>', methods=['DELETE'])
def delete_recommendations(id):
    if id in data:
        del data[id]
    return '', HTTP_204_NO_CONTENT

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def new_index():
    global data
    with lock:
        new_id = str(uuid.uuid4())[:8]
        if data.has_key(new_id):
            return new_index()
        else:
            return new_id

def reply(message, rc):
    print "message = " + str(message);
    response = Response(json.dumps(message))
    response.headers['Content-Type'] = 'application/json'
    response.status_code = rc
    return response

def is_valid(data):
    valid = False
    try:
        name = data['name']
        recomm = data['recommendations']
        valid = True
    except KeyError as err:
        app.logger.error('Missing parameter error: %s', err)
    return valid


######################################################################
# Connect to MySQL and catch connection exceptions
######################################################################
def connect_mysql(user, passwd, server, port, database):
    engine = create_engine("mysql://%s:%s@%s:%s/%s" % (user, passwd, server, port,  database), echo = False)
    try:
        conn = engine.connect()
    except OperationalError:
        conn = None
    return conn


######################################################################
# INITIALIZE MySQL
# This method will work in the following conditions:
#   1) In Bluemix with cleardb bound through VCAP_SERVICES
#   2) With MySQL --linked in a Docker container in virtual machine
######################################################################
def inititalize_mysql():
    global conn
    conn = None
    # Get the crdentials from the Bluemix environment
    if 'VCAP_SERVICES' in os.environ:
        print("Using VCAP_SERVICES...")
        VCAP_SERVICES = os.environ['VCAP_SERVICES']
        services = json.loads(VCAP_SERVICES)
        creds = services['cleardb'][0]['credentials']
        print("Conecting to Mysql on host %s port %s" % (creds['hostname'], creds['port']))
        conn = connect_mysql(creds['username'], creds['password'], creds['hostname'], creds['port'], creds['name'])
    else:
        print("VCAP_SERVICES not found, checking localhost for MySQL")
        conn = connect_mysql('root', '', '127.0.0.1', 3306, 'nyudevops')
    if not conn:
        # if you end up here, mysql instance is down.
        print('*** FATAL ERROR: Could not connect to the MySQL Service')
        exit(1)


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    print "Recommendations Service Starting..."
    inititalize_mysql()
    global current_largest_id
    result = conn.execute("select max(id) from recommendations")
    current_largest_id = list(result)[0][0]

    #-----------------------------------------------------------------
    # TODO!!!
    # The following code should be removed once APIs are updated to use
    # database connections
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    dummy_json_url = os.path.join(SITE_ROOT, "dummy/",
        "dummy_product_recomm.json")
    data = json.load(open(dummy_json_url))
    #-----------------------------------------------------------------

    # Pull options from environment
    debug = (os.getenv('DEBUG', 'False') == 'True')
    port = os.getenv('PORT', '5000')
    app.run(host='0.0.0.0', port=int(port), debug=debug)
