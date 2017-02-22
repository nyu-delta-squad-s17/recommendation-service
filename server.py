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
# LIST ALL PETS
######################################################################
@app.route('/recommendations', methods=['GET'])
def list_recommendations():
    """
    Basically prints out all the recommendations.
    """

    result_dict = {}
    for prod_id in data:
        result_dict[prod_id] = {'data': [{'id': x['id'],
                                          'name': x['name']} for x in
                                         data[prod_id]['recommendations']],
                                'id': prod_id,
                                'name': data[prod_id]['name']}
    return reply(result_dict, HTTP_200_OK)

######################################################################
# RETRIEVE A PET
######################################################################
@app.route('/recommendations/<id>', methods=['GET'])
def get_recommendations(id):
    '''
    Given a Product ID, Output a list of it's reccommendations.
    '''

    if id in data:
        recomms = data[id]['recommendations']
        rc = HTTP_200_OK
    else:
        recomms = {'error': 'Product with id: %s was not found' % str(id)}
        rc = HTTP_404_NOT_FOUND

    return reply(recomms, rc)

######################################################################
# ADD A NEW PET
######################################################################
@app.route('/pets', methods=['POST'])
def create_pets():
    payload = request.get_json()
    if is_valid(payload):
        id = next_index()
        pets[id] = {'id': id, 'name': payload['name'], 'kind': payload['kind']}
        message = pets[id]
        rc = HTTP_201_CREATED
    else:
        message = { 'error' : 'Data is not valid' }
        rc = HTTP_400_BAD_REQUEST

    return reply(message, rc)

######################################################################
# UPDATE AN EXISTING PET
######################################################################
@app.route('/pets/<int:id>', methods=['PUT'])
def update_pets(id):
    if pets.has_key(id):
        payload = request.get_json()
        if is_valid(payload):
            pets[id] = {'id': id, 'name': payload['name'], 'kind': payload['kind']}
            message = pets[id]
            rc = HTTP_200_OK
        else:
            message = { 'error' : 'Pet data was not valid' }
            rc = HTTP_400_BAD_REQUEST
    else:
        message = { 'error' : 'Pet %s was not found' % id }
        rc = HTTP_404_NOT_FOUND

    return reply(message, rc)

######################################################################
# DELETE A PET
######################################################################
@app.route('/pets/<int:id>', methods=['DELETE'])
def delete_pets(id):
    del pets[id];
    return '', HTTP_204_NO_CONTENT

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def next_index():
    global current_pet_id
    with lock:
        current_pet_id += 1
    return current_pet_id

def reply(message, rc):
    response = Response(json.dumps(message))
    response.headers['Content-Type'] = 'application/json'
    response.status_code = rc
    return response

def is_valid(data):
    valid = False
    try:
        name = data['name']
        kind = data['kind']
        valid = True
    except KeyError as err:
        app.logger.error('Missing parameter error: %s', err)
    return valid


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    dummy_json_url = os.path.join(SITE_ROOT, "dummy/",
        "dummy_product_recomm.json")
    data = json.load(open(dummy_json_url))
    # Pull options from environment
    debug = (os.getenv('DEBUG', 'False') == 'True')
    port = os.getenv('PORT', '5000')
    app.run(host='0.0.0.0', port=int(port), debug=debug)
