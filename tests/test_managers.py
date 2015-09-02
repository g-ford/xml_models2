import unittest
from xml_models.xpath_finder import MultipleNodesReturnedException
from mock import patch
import xml_models
from xml_models.managers import ModelQuery, NoRegisteredFinderError, DoesNotExist
from xml_models.rest_client import rest_client


class SimpleModel(xml_models.Model):
    field1 = xml_models.CharField(xpath='/root/field1')

    finders = {
        (field1,): "http://foo.com/simple/%s",
        ('a', 'b'): "http://foo.com/simple/%s/%s"
    }


    headers = {'user': 'user1', 'password': 'pwd1'}


class NestedModel(xml_models.Model):
    field1 = xml_models.CharField(xpath='/root/field1')
    collection_node = 'elems'
    finders = {
        (field1,): "http://foo.com/simple/%s",
    }


class ModelManagerTestCases(unittest.TestCase):
    def test_returns_query_when_filtering(self):
        query = SimpleModel.objects.filter(field1="Rhubarb")
        self.assertIsInstance(query, ModelQuery)

    def test_returns_unique_query_when_filtering(self):
        query = SimpleModel.objects.filter(field1="Rhubarb")
        query2 = SimpleModel.objects.filter(field1="Rhubarb")
        self.assertNotEqual(query, query2)


class QueryManagerTestCases(unittest.TestCase):
    def test_headers_specified_on_model_is_added_to_the_query_manager(self):
        query = SimpleModel.objects.filter(field1="Rhubarb")
        self.assertTrue(query.headers != None)
        self.assertEquals('pwd1', query.headers['password'])

    def test_can_use_multiple_keys(self):
        query = SimpleModel.objects.filter(field1="Rhubarb", field2="Chocolate")

        self.assertIn('field1', query.args)
        self.assertIn('field2', query.args)

    def test_queries_are_chainable(self):
        query = SimpleModel.objects.filter(field1="Rhubarb")
        query = query.filter(field2="Chocolate")

        self.assertIn('field1', query.args)
        self.assertIn('field2', query.args)

    def test_noregisteredfindererror_raised_when_filter_on_non_existent_field(self):
        with self.assertRaises(NoRegisteredFinderError):
            SimpleModel.objects.filter(foo="bar").count()


    @patch.object(rest_client.Client, "GET")
    def test_rasies_error_if_api_fails(self, mock_get):
        class api:
            content = None

        mock_get.return_value = api()

        with self.assertRaises(DoesNotExist):
            SimpleModel.objects.filter(field1="hello").count()

        with self.assertRaises(DoesNotExist):
            SimpleModel.objects.get(field1="hello")

    @patch.object(rest_client.Client, "GET")
    def test_filtering_for_a_registered_finder(self, mock_get):
        class api:
            content = "<root><field1>Hello</field1></root>"

        mock_get.return_value = api()
        count = SimpleModel.objects.filter(field1="hello").count()
        self.assertEquals(1, count)
        self.assertTrue(mock_get.called)

    @patch.object(rest_client.Client, "GET")
    def test_manager_counts_child_nodes_when_filtering_a_collection_of_results(self, mock_get):
        class api:
            content = "<collection><root><field1>hello</field1></root><root><field1>goodbye</field1></root></collection>"

        mock_get.return_value = api()
        count = SimpleModel.objects.filter(field1="baz").count()
        self.assertEquals(2, count)
        self.assertTrue(mock_get.called)

    @patch.object(rest_client.Client, "GET")
    def test_get_a_registered_finder(self, mock_get):
        class api:
            content = "<root><field1>Hello</field1></root>"
            response_code = 200

        mock_get.return_value = api()
        SimpleModel.objects.get(field1="baz")
        self.assertTrue(mock_get.called)

    @patch.object(rest_client.Client, "GET")
    def test_get_for_a_multi_field_registered_finder(self, mock_get):
        class api:
            content = "<root><field1>Hello</field1></root>"
            response_code = 200

        mock_get.return_value = api()
        SimpleModel.objects.get(a="foo", b="bar")
        self.assertTrue(mock_get.called)
        self.assertEquals("http://foo.com/simple/foo/bar", mock_get.call_args[0][0])

    @patch.object(rest_client.Client, "GET")
    def test_accepts_strings_as_finder_keys(self, mock_get):
        class api:
            content = "<root><field1>Hello</field1></root>"
            response_code = 200

        mock_get.return_value = api()
        SimpleModel.objects.get(a="foo", b="bar")
        self.assertTrue(mock_get.called)
        self.assertEquals("http://foo.com/simple/foo/bar", mock_get.call_args[0][0])


    @patch.object(rest_client.Client, "GET")
    def test_raises_error_when_repsonse_empty(self, mock_get):
        class api:
            content = ''
            response_code = 200
        mock_get.return_value = api()

        with self.assertRaises(DoesNotExist):
            SimpleModel.objects.get(field1="baz")

    @patch.object(rest_client.Client, "GET")
    def test_raises_error_when_response_code_404(self, mock_get):
        class api:
            content = '<HTML><body>Nothing to see here</body></HTML>'
            response_code = 404
        mock_get.return_value = api()

        with self.assertRaises(DoesNotExist):
            SimpleModel.objects.get(field1="baz")


    @patch.object(rest_client.Client, "GET")
    def test_returns_iterator_for_collection_of_results(self, mock_get):
        class api:
            content = "<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>"
        mock_get.return_value = api()
        qry = SimpleModel.objects.filter(field1="baz")
        results = []
        for mod in qry:
            results.append(mod)
        self.assertEquals(2, len(results))
        self.assertEquals("hello", results[0].field1)
        self.assertEquals("goodbye", results[1].field1)

    @patch.object(rest_client.Client, "GET")
    def test_can_use_custom_query(self, mock_get):
        class api:
            content = "<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>"
            response_code = 200
        mock_get.return_value = api()

        SimpleModel.objects.filter_custom("http://hard_coded_url").get()

        self.assertEquals("http://hard_coded_url", mock_get.call_args[0][0])

    @patch.object(rest_client.Client, "GET")
    def test_returns_iterator_for_collection_of_results_from_custom_query(self, mock_get):
        class api:
            content = "<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>"
        mock_get.return_value = api()
        qry = SimpleModel.objects.filter_custom("http://hard_coded_url")
        results = []
        for mod in qry:
            results.append(mod)
        self.assertEquals(2, len(results))
        self.assertEquals("hello", results[0].field1)
        self.assertEquals("goodbye", results[1].field1)

    @patch.object(rest_client.Client, "GET")
    def test_supports_listifying(self, mock_get):
        class api:
            content = "<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>"
        mock_get.return_value = api()
        qry = SimpleModel.objects.filter_custom("http://hard_coded_url")
        results = list(qry)
        self.assertEquals(2, len(results))
        self.assertEquals("hello", results[0].field1)
        self.assertEquals("goodbye", results[1].field1)

    @patch.object(rest_client.Client, "GET")
    def test_returns_count_of_collection_of_results_when_len_is_called(self, mock_get):
        class api:
            content = "<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>"
        mock_get.return_value = api()
        qry = SimpleModel.objects.filter(field1="baz")
        self.assertEquals(2, len(qry))

    @patch.object(rest_client.Client, "GET")
    def test_can_specify_collection_node_when_get(self, mock_get):
        class api:
            content = "<response><metadata /><elems><root><field1>hello</field1></root></elems></response>"
            response_code = 200
        mock_get.return_value = api()

        qry = NestedModel.objects.get(field1='a')
        self.assertIsInstance(qry, NestedModel)
        self.assertEqual('hello', qry.field1)

    @patch.object(rest_client.Client, "GET")
    def test_get_with_multiple_collection_node_results_raises(self, mock_get):
        class api:
            content = "<response><metadata /><elems><root><field1>hello</field1></root><root><field1>hello</field1></root></elems></response>"
            response_code = 200
        mock_get.return_value = api()

        with self.assertRaises(MultipleNodesReturnedException):
            qry = NestedModel.objects.get(field1='a')


    @patch.object(rest_client.Client, "GET")
    def test_can_specify_collection_node_when_filtering(self, mock_get):
        class api:
            content = "<response><metadata /><elems><root><field1>hello</field1></root></elems></response>"
            response_code = 200
        mock_get.return_value = api()

        qry = NestedModel.objects.filter(field1='a')
        results = []
        for mod in qry:
            results.append(mod)
        self.assertIsInstance(results[0], NestedModel)
        self.assertEqual('hello', results[0].field1)

        

