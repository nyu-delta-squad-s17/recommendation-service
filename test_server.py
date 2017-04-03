# run with:
# python -m unittest discover

import unittest
import logging
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
        server.initialize_testmysql()
        server.conn.execute("INSERT INTO `recommendations` VALUES (1,1,2,'x-sell',5),(2,1,3,'up-sell',5),(3,2,4,'up-sell',5)")
        server.initialize_index()

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
        self.assertTrue( resp.status_code == HTTP_200_OK )
        self.assertTrue( len(resp.data) > 0 )

    def test_get_recommendation(self):
        resp = self.app.get('/recommendations/3')
        self.assertEqual( resp.status_code, HTTP_200_OK )
        data = json.loads(resp.data)
        self.assertEqual (data['parent_product_id'], 2)

    def test_get_recommendation_not_found(self):
        resp = self.app.get('/recommendations/0')
        self.assertEqual( resp.status_code, HTTP_404_NOT_FOUND )

    def test_delete_recommendation_pass(self):
        # save the current number of recommendations for later comparison
        recommendation_count = self.get_recommendation_count()
        # delete a recommendation that doesn't exist
        resp = self.app.delete('/recommendations/1', content_type='application/json')
        self.assertTrue( resp.status_code == HTTP_204_NO_CONTENT )
        self.assertTrue( len(resp.data) == 0 )
        new_count = self.get_recommendation_count()
        self.assertTrue ( new_count == recommendation_count - 1)

    def test_delete_recommendation_fail(self):
        resp_get = self.app.get('/recommendations/2')
        self.assertTrue ( resp_get.status_code == HTTP_200_OK )
        resp_delete = self.app.delete('/recommendations/2', content_type='application/json')
        self.assertTrue( resp_delete.status_code == HTTP_204_NO_CONTENT )
        resp_get_deleted = self.app.get('recommendations/2')
        self.assertTrue ( resp_get_deleted.status_code == HTTP_404_NOT_FOUND )
        
    def test_get_recommendation_by_type(self):
        log = logging.getLogger("Test GET recommendations by type")
        resp = self.app.get('/recommendations?type=x-sell')
        self.assertTrue(resp.status_code == HTTP_200_OK)
        data = json.loads(resp.data)
        for data_point in data:
            log.debug(data_point)
            self.assertTrue(data_point["type"] == "x-sell",
                            msg=data_point["type"])

    def test_clicked_recommendation_pass(self):
        resp = self.app.get('/recommendations/3')
        data = json.loads(resp.data)
        old_priority = data['priority']
        resp = self.app.put('/recommendations/3/clicked', content_type='application/json')
        self.assertTrue( resp.status_code == HTTP_200_OK )
        resp = self.app.get('/recommendations/3')
        data = json.loads(resp.data)
        new_priority = data['priority']
        if (old_priority == 1):
            self.assertTrue( new_priority == old_priority )
        else: 
            self.assertTrue( new_priority == old_priority - 1 )

    def test_clicked_recommendation_id_not_found(self):
        resp = self.app.put('/recommendations/0/clicked', content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_404_NOT_FOUND )

    def test_get_recommendation_by_non_existent_type(self):
        resp = self.app.get('/recommendations?type=foo')
        self.assertTrue(resp.status_code == HTTP_200_OK)
        data = json.loads(resp.data)
        self.assertFalse(data)

    def test_get_recommendation_by_parent_id(self):
        log = logging.getLogger("Test GET recommendations by parent_product_id")

        resp = self.app.get('/recommendations?product-id=1')
        data = json.loads(resp.data)
        self.assertTrue(resp.status_code == HTTP_200_OK, msg=data)
        test_result = all(data_point["parent_product_id"] == 1 for data_point in data)
        self.assertTrue(test_result)

    def test_get_recommendation_by_non_existent_parent_id(self):
        resp = self.app.get('/recommendations?product-id=foo')
        data = json.loads(resp.data)
        self.assertTrue(resp.status_code == HTTP_200_OK, msg=data)
        self.assertFalse(data)

    def test_get_recommendation_by_type_and_parent_id(self):
        log = logging.getLogger("Test GET recommendations by parent_product_id and type")
        log.warning("result with spaces between queries are errorneous.")

        resp = self.app.get('/recommendations?product-id=1&type=up-sell')
        data = json.loads(resp.data)
        self.assertTrue(resp.status_code == HTTP_200_OK, msg=data)
        self.assertFalse(data)

    def test_get_recommendation_by_type_and_non_existent_parent_id(self):
        resp = self.app.get('/recommendations?product-id=foo&type=up-sell')
        data = json.loads(resp.data)
        self.assertTrue(resp.status_code == HTTP_200_OK, msg=data)
        self.assertFalse(data)

    def test_get_recommendation_by_parent_id_and_non_existent_type(self):
        resp = self.app.get('/recommendations?product-id=1&type=bar')
        data = json.loads(resp.data)
        self.assertTrue(resp.status_code == HTTP_200_OK, msg=data)
        self.assertFalse(data)

    def test_get_recommendation_by_non_existent_parent_id_and_non_existent_type(self):
        resp = self.app.get('/recommendations?product-id=foo&type=bar')
        data = json.loads(resp.data)
        self.assertTrue(resp.status_code == HTTP_200_OK, msg=data)
        self.assertFalse(data)

    def test_create_recommendation(self):
        recommendation_count = self.get_recommendation_count()
        new_recommendation = {'parent_product_id': '2', 'priority': '5', 'related_product_id':'2', 'type': 'x-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertTrue( resp.status_code == HTTP_201_CREATED )
        new_json = json.loads(resp.data)
        self.assertEqual (new_json['parent_product_id'], 2)
        self.assertEqual (new_json['priority'], 5)
        self.assertEqual (new_json['related_product_id'], 2)
        self.assertEqual (new_json['type'], 'x-sell')
        resp = self.app.get('/recommendations')
        data = json.loads(resp.data)
        self.assertEqual( resp.status_code, HTTP_200_OK )
        self.assertEqual( len(data), recommendation_count + 1 )
        self.assertIn( new_json, data )

    def test_create_recommendation_with_no_data(self):
        resp = self.app.post('/recommendations', content_type='application/json')
        data = json.loads(resp.data)
        self.assertTrue( resp.status_code == HTTP_400_BAD_REQUEST )

    def test_create_recommendation_with_no_parent_product_id(self):
        new_recommendation = {'priority': '5', 'related_product_id':'2', 'type': 'x-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_create_recommendation_with_no_related_product_id(self):
        new_recommendation = {'parent_product_id': '2', 'priority': '5', 'type': 'x-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_create_recommendation_with_no_priority(self):
        new_recommendation = {'parent_product_id': '2', 'related_product_id':'2', 'type': 'x-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_create_recommendation_with_no_type(self):
        new_recommendation = {'parent_product_id': '2', 'priority': '5', 'related_product_id':'2'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_create_recommendation_with_no_parent_product_id_and_related_product_id(self):
        new_recommendation = {'priority': '5', 'type': 'x-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_create_recommendation_with_no_parent_product_id_and_priority(self):
        new_recommendation = {'related_product_id':'2', 'type': 'x-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_create_recommendation_with_no_priority_and_related_product_id(self):
        new_recommendation = {'parent_product_id': '2', 'type': 'x-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_create_recommendation_with_no_priority_and_type(self):
        new_recommendation = {'parent_product_id': '2', 'related_product_id':'2'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_create_recommendation_with_no_related_product_id_and_type(self):
        new_recommendation = {'parent_product_id': '2', 'priority': '5'}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_update_recommendation(self):
        new_recommendation = {'parent_product_id': '2', 'priority': '5', 'related_product_id':'4', 'type': 'up-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.put('/recommendations/3', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_200_OK )
        new_json = json.loads(resp.data)
        self.assertEqual (new_json['type'], 'up-sell')

    def test_update_recommendation_with_no_data(self):
        resp = self.app.put('/recommendations/3', data=None, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_update_recommendation_with_no_parent_product_id(self):
        new_recommendation = {'priority': '5', 'related_product_id':'4', 'type': 'x-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.put('/recommendations/2', data=data, content_type='application/json')
        self.assertEqual( resp.status_code, HTTP_400_BAD_REQUEST )

    def test_update_recommendation_not_found(self):
        new_recommendation = {'parent_product_id': '2', 'priority': '5', 'related_product_id':'4', 'type': 'up-sell'}
        data = json.dumps(new_recommendation)
        resp = self.app.put('/recommendations/0', data=data, content_type='application/json')
        self.assertEquals( resp.status_code, status.HTTP_404_NOT_FOUND )

    def test_initialize_db(self):
        server.initialize_mysql()
        self.assertTrue(server.conn != None)
        
######################################################################
# Utility functions
######################################################################

    def get_recommendation_count(self):
        # save the current number of recommendations
        resp = self.app.get('/recommendations')
        self.assertTrue( resp.status_code == HTTP_200_OK )
        data = json.loads(resp.data)
        return len(data)

######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
