# run with:
# python -m unittest discover

import unittest
import json
import server
from flask_api import status    # HTTP Status Codes

# Status Codes
HTTP_200_OK = status.HTTP_200_OK
HTTP_201_CREATED = status.HTTP_201_CREATED
HTTP_204_NO_CONTENT = status.HTTP_204_NO_CONTENT
HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
HTTP_409_CONFLICT = status.HTTP_409_CONFLICT

######################################################################
#  T E S T   C A S E S
######################################################################
class TestRecommendationServer(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        server.inititalize_mysql()

    @classmethod
    def tearDownClass(self):
        server.conn.close()

    def setUp(self):
        server.app.debug = True
        self.app = server.app.test_client()

    def test_index(self):
        resp = self.app.get('/')
        self.assertTrue ('Recommendations REST API Service' in resp.data)
        self.assertTrue( resp.status_code == HTTP_200_OK )

    def test_get_recommendation_list(self):
        resp = self.app.get('/recommendations')
        #print 'resp_data: ' + resp.data
        self.assertTrue( resp.status_code == HTTP_200_OK )
        self.assertTrue( len(resp.data) > 0 )

    def test_get_recommendation(self):
        resp = self.app.get('/recommendations/1')
        self.assertEqual( resp.status_code, HTTP_200_OK )
        data = json.loads(resp.data)
        self.assertEqual (data['parent_product_id'], 1)

    def test_get_recommendation_not_found(self):
        resp = self.app.get('/recommendations/0')
        self.assertEqual( resp.status_code, HTTP_404_NOT_FOUND )


######################################################################
# Utility functions
######################################################################

    def get_recommendation_count(self):
        # save the current number of pets
        resp = self.app.get('/recommendations')
        self.assertTrue( resp.status_code == HTTP_200_OK )
        # print 'resp_data: ' + resp.data
        data = json.loads(resp.data)
        return len(data)


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
