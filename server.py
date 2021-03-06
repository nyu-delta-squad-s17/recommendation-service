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
#from simplejson import JSONDecodeError
from sqlalchemy import *
from sqlalchemy.exc import *
from flasgger import Swagger

# Create Flask application
app = Flask(__name__)

# Configure Swagger before initilaizing it
app.config['SWAGGER'] = {
    "swagger_version": "2.0",
    "specs": [
        {
            "version": "1.0.0",
            "title": "DevOps Swagger Recommendations App",
            "description": "This is a sample server Recommendations server.",
            "endpoint": 'v1_spec',
            "route": '/v1/spec'
        }
    ]
}

# Initialize Swagger after configuring it
Swagger(app)

# Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409

debug = (os.getenv('DEBUG', 'False') == 'True')
port = os.getenv('PORT', '5000')

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
    Retrieve a list of Recommendations
    This endpoint will return all Recommendations unless a query parameter is specificed
    ---
    tags:
      - Recommendations
    description: The Recommendations endpoint allows you to query Recommendations
    parameters:
      - name: type
        in: query
        description: the type of Recommendation you are looking for
        required: false
        type: string
      - name: product-id
        in: query
        description: the id of the product you would like recommendations for
        required: false
        type: int
    responses:
      200:
        description: An array of Recommendations
        schema:
          type: array
          items:
            schema:
              id: Recommendation
              properties:
                id:
                  type: integer
                  description: unique id assigned internally by service
                parent_product_id:
                  type: integer
                  description: unique id of the parent product
                related_product_id:
                  type: integer
                  description: unique id of the recommended product
                type:
                  type: string
                  description: the category of recommendation (e.g., up-sell, x-sell, etc.)
                priority:
                  type: integer
                  description: the priority of the recommendation (a lower number means higher priority)
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
@app.route('/recommendations/<int:id>', methods=['GET'])
def get_recommendations(id):
    """
    Retrieve a single Recommendation given a ID
    This endpoint will return a Recommendation based on it's id
    ---
    tags:
      - Recommendations
    produces:
      - application/json
    parameters:
      - name: id
        in: path
        description: ID of Recommendation to retrieve
        type: integer
        required: true
    responses:
      200:
        description: Recommendation returned
        schema:
          id: Recommendation
          properties:
            id:
              type: integer
              description: unique id assigned internally by service
            parent_product_id:
              type: integer
              description: unique id of the parent product
            related_product_id:
              type: integer
              description: unique id of the recommended product
            type:
              type: string
              description: the category of recommendation (e.g., up-sell, x-sell, etc.)
            priority:
              type: integer
              description: the priority of the recommendation (a lower number means higher priority)
      404:
        description: Recommendation not found
    """
    message = retrieve_by_id(id)
    rc = HTTP_200_OK
    if not message:
        message = {'error': 'Recommendation with id: %s was not found' % str(id)}
        rc = HTTP_404_NOT_FOUND
    return reply(message, rc)

######################################################################
# ADD A NEW PRODUCT RECOMMENDATION RELATIONSHIP
######################################################################
@app.route('/recommendations', methods=['POST'])
def create_recommendations():
    """
    Create a new product recommendation relationship
    This endpoint will create a recommendation based the data in the body that is posted
    ---
    tags:
      - Recommendations
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: data
          required:
            - priority
            - related_product_id
            - type
            - parent_product_id
          properties:
            parent_product_id:
              type: integer
              description: unique id of the parent product
            related_product_id:
              type: integer
              description: unique id of the recommended product
            type:
              type: string
              description: the category of recommendation (e.g., up-sell, x-sell, etc.)
            priority:
              type: integer
              description: the priority of the recommendation (a lower number means higher priority)
    responses:
      201:
        description: Recommendation created
        schema:
          id: Recommendation
          properties:
            id:
              type: integer
              description: unique id assigned internally by service
            parent_product_id:
              type: integer
              description: unique id of the parent product
            related_product_id:
              type: integer
              description: unique id of the recommended product
            type:
              type: string
              description: the category of recommendation (e.g., up-sell, x-sell, etc.)
            priority:
              type: integer
              description: the priority of the recommendation (a lower number means higher priority)
      400:
        description: Bad Request (the posted data was not valid)
    """
    message, valid = is_valid(request.get_data())
    if valid:
        payload = json.loads(request.get_data())
        id = next_index()
        conn.execute("INSERT INTO recommendations VALUES (%s, %s, %s, \"%s\", %s)" % \
                    (id, \
                    payload['parent_product_id'], \
                    payload['related_product_id'], \
                    payload['type'], \
                    payload['priority']))
        message = retrieve_by_id(id)
        rc = HTTP_201_CREATED
    else:
        # message = { 'error' : 'Data is not valid' }
        rc = HTTP_400_BAD_REQUEST
    return reply(message, rc)

######################################################################
# UPDATE AN EXISTINT RECOMMENDATION RELATIONSHIP
######################################################################
@app.route('/recommendations/<int:id>', methods=['PUT'])
def update_recommendations(id):
    """
    Given a Recommendation ID, update the columns as from the payload
    This endpoint will update a Recommendation based the body that is posted
    ---
    tags:
      - Recommendations
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: id
        in: path
        description: ID of recommendation to retrieve
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          id: data
          required:
            - priority
            - related_product_id
            - type
            - parent_product_id
          properties:
            parent_product_id:
              type: integer
              description: unique id of the parent product
            related_product_id:
              type: integer
              description: unique id of the recommended product
            type:
              type: string
              description: the category of recommendation (e.g., up-sell, x-sell, etc.)
            priority:
              type: integer
              description: the priority of the recommendation (a lower number means higher priority)
    responses:
      200:
        description: Recommendation Updated
        schema:
           id: Recommendation
           properties:
             id:
               type: integer
               description: unique id assigned internally by service
             parent_product_id:
               type: integer
               description: unique id of the parent product
             related_product_id:
               type: integer
               description: unique id of the recommended product
             type:
               type: string
               description: the category of recommendation (e.g., up-sell, x-sell, etc.)
             priority:
               type: integer
               description: the priority of the recommendation (a lower number means higher priority)
      400:
        description: Bad Request (the posted data was not valid)
    """
    if get_recommendations(id).status_code == 404:
        message = {'error': 'Recommendation with id: %s was not found' % str(id)}
        return reply(message, HTTP_404_NOT_FOUND)
    message, valid = is_valid(request.get_data())
    if valid:
        payload = json.loads(request.get_data())
        conn.execute("UPDATE recommendations \
                      SET type=\"%s\", priority=%s \
                      WHERE parent_product_id=%s \
                      AND related_product_id=%s AND id=%s"
                     % (payload['type'],
                        payload['priority'],
                        payload['parent_product_id'],
                        payload['related_product_id'],
                        id
                        ))
        return get_recommendations(id)
    else:
        #message = {'error': 'Invalid Request'}
        rc = HTTP_400_BAD_REQUEST
        return reply(message, rc)

######################################################################
# DELETE A PRODUCT RECOMMENDATION
######################################################################
@app.route('/recommendations/<int:id>', methods=['DELETE'])
def delete_recommendations(id):
    """
    Delete a single recommendation
    This endpoint will delete a recommendation based on the id that is specificed
    ---
    tags:
      - Recommendations
    description: Delete a recommendation
    parameters:
      - name: id
        in: path
        description: ID of recommendation to be delete_recommendations
        type: integer
        required: true
    responses:
      204:
        description: recommendation deleted
    """
    if get_recommendations(id).status_code == 200:
        conn.execute("DELETE FROM recommendations WHERE id=%d" % id)
    return '', HTTP_204_NO_CONTENT

######################################################################
# ACTION - UPDATE PRIORITY WHEN RECOMMENDATION IS CLICKED
######################################################################
@app.route('/recommendations/<int:id>/clicked', methods=['PUT'])
def increase_priority(id):
    """
    Given a recommendation ID, update the priority as from the payload
    This endpoint will increase the priority of a recommmendation based on the ID specificed
    ---
    tags:
      - Recommendations
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: id
        in: path
        description: ID of recommendation to retrieve
        type: integer
        required: true
    responses:
      200:
        description: Recommendation priority Updated
        schema:
          id: Recommendation
          properties:
            id:
              type: integer
              description: unique id assigned to recommendation
            priority:
              type: integer
              description: priority of the recommendation (lower the number, higher the priority)
      404:
        description: Recommendation not found
    """
    if get_recommendations(id).status_code == 404:
        message = {'error': 'Recommendation with id: %s was not found' % str(id)}
        return reply(message, HTTP_404_NOT_FOUND)
    """
    Decrements the priority from low to high of the recommendations_id until 1
    """
    conn.execute("UPDATE recommendations \
                  SET priority= priority - 1 \
                  WHERE id=%d \
                  AND priority>1"
                 % (id))
    return reply(None, HTTP_200_OK)

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def next_index():
    max_id_result = conn.execute("select max(id) from recommendations")
    return list(max_id_result)[0][0] + 1

def reply(message, rc):
    # print "message = " + str(message);
    response = Response(json.dumps(message))
    response.headers['Content-Type'] = 'application/json'
    response.status_code = rc
    return response

def is_valid(raw_data):
    try:
        data = json.loads(raw_data)
    except:
        message = {'error': 'JSON decoding error'}
        return message, False
    if set(data.keys()) != set(['priority', 'related_product_id', 'parent_product_id', 'type']):
        # app.logger.error('key set does not match')
        message = {'error': 'key set does not match'}
        return message, False
    try:
        # Not sure if we should check data type or exceptions
        # If we check exceptions, input 1 and "1" will be treated as the same
        priority = int(data['priority'])
        related_pid = int(data['related_product_id'])
        parent_pid = int(data['parent_product_id'])
    except ValueError as err:
        # app.logger.error('Data value error: %s', err)
        message = {'error': 'Data value error: %s' % err}
        return message, False
    except TypeError as err:
        # app.logger.error('Data type error: %s', err)
        message = {'error': 'Data type error: %s' % err}
        return message, False
    return "", True

def retrieve_by_id(id):
    message = {}
    results = conn.execute("SELECT * FROM recommendations WHERE id=%d" % (int(id)))
    for rec in results:
        message = {"id": rec[0],
                   "parent_product_id": rec[1],
                   "related_product_id": rec[2],
                   "type": rec[3],
                   "priority": rec[4]}
    return message


######################################################################
# Connect to MySQL and catch connection exceptions
######################################################################
def connect_mysql(user, passwd, server, port, database):
    engine = create_engine("mysql://%s:%s@%s:%s/%s" % (user, passwd, server, port, database), echo = False)
    return engine.connect()


######################################################################
# INITIALIZE MySQL
# This method will work in the following conditions:
#   1) In Bluemix with cleardb bound through VCAP_SERVICES
#   2) With MySQL --linked in a Docker container in virtual machine
######################################################################
def initialize_mysql(test=False):
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
        response = os.system("ping -c 1 mysql")
        if response == 0:
            mysql_hostname = 'mysql'
        else:
            mysql_hostname = '127.0.0.1'
        if test:
            engine = create_engine("mysql://%s:%s@%s:%s/%s" % ('root', '', mysql_hostname, 3306, 'tdd'), echo = False)
            meta = MetaData()
            recommendations = Table('recommendations', meta,
                Column('id', Integer, nullable=False, primary_key=True),
                Column('parent_product_id', Integer, nullable=False),
                Column('related_product_id', Integer, nullable=False),
                Column('type', String(20), nullable=False),
                Column('priority', Integer, nullable=True)
            )
            try:
                recommendations.drop(engine, checkfirst=True)
            except:
                pass
            recommendations.create(engine, checkfirst=True)
            conn = engine.connect()
        else:
            conn = connect_mysql('root', '', mysql_hostname, 3306, 'nyudevops')


######################################################################
#   M A I N
######################################################################

if __name__ == "__main__":
    print "Recommendations Service Starting..."
    initialize_mysql()
    # Pull options from environment
    app.run(host='0.0.0.0', port=int(port), debug=debug)
