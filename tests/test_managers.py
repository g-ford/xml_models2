import unittest
import xml_models


class Simple(xml_models.Model):
    field1 = xml_models.CharField(xpath='/root/field1')

    finders = {
        (field1,): "http://foo.com/simple/%s"
    }
    headers = {'user': 'user1', 'password': 'pwd1'}


class QueryManagerTestCases(unittest.TestCase):
    def test_headers_specified_on_model_is_added_to_the_query_manager(self):
        self.assertTrue(Simple.objects.headers != None)
        self.assertEquals('user1', Simple.objects.headers['user'])
        query = Simple.objects.filter(field1="Rhubarb")
        self.assertTrue(query.headers != None)
        self.assertEquals('pwd1', query.headers['password'])