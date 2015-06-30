import unittest
from StringIO import StringIO
from mock import patch, Mock
import xml_models
from xml_models.managers import ModelQuery, NoRegisteredFinderError, DoesNotExist
from xml_models.rest_client import rest_client
from xml_models.xml_models import XmlValidationError


class Simple(xml_models.Model):
    field1 = xml_models.CharField(xpath='/root/field1')

    finders = {
        (field1,): "http://foo.com/simple/%s",
        ('a', 'b'): "http://foo.com/simple/%s/%s"
    }


    headers = {'user': 'user1', 'password': 'pwd1'}


class ModelManagerTestCases(unittest.TestCase):
    def test_returns_query_when_filtering(self):
        query = Simple.objects.filter(field1="Rhubarb")
        self.assertIsInstance(query, ModelQuery)

    def test_returns_unique_query_when_filtering(self):
        query = Simple.objects.filter(field1="Rhubarb")
        query2 = Simple.objects.filter(field1="Rhubarb")
        self.assertNotEqual(query, query2)


class QueryManagerTestCases(unittest.TestCase):
    def test_headers_specified_on_model_is_added_to_the_query_manager(self):
        query = Simple.objects.filter(field1="Rhubarb")
        self.assertTrue(query.headers != None)
        self.assertEquals('pwd1', query.headers['password'])

    def test_can_use_multiple_keys(self):
        query = Simple.objects.filter(field1="Rhubarb", field2="Chocolate")

        self.assertIn('field1', query.args)
        self.assertIn('field2', query.args)

    def test_queries_are_chainable(self):
        query = Simple.objects.filter(field1="Rhubarb")
        query = query.filter(field2="Chocolate")

        self.assertIn('field1', query.args)
        self.assertIn('field2', query.args)

    def test_noregisteredfindererror_raised_when_filter_on_non_existent_field(self):
        with self.assertRaises(NoRegisteredFinderError):
            Simple.objects.filter(foo="bar").count()


    @patch.object(rest_client.Client, "GET")
    def test_filtering_for_a_registered_finder(self, mock_get):
        class api:
            content = StringIO("<root><field1>Hello</field1></root>")

        mock_get.return_value = api()
        count = Simple.objects.filter(field1="hello").count()
        self.assertEquals(1, count)
        self.assertTrue(mock_get.called)

    @patch.object(rest_client.Client, "GET")
    def test_manager_counts_child_nodes_when_filtering_a_collection_of_results(self, mock_get):
        class api:
            content = StringIO("<collection><root><field1>hello</field1></root><root><field1>goodbye</field1></root></collection>")

        mock_get.return_value = api()
        count = Simple.objects.filter(field1="baz").count()
        self.assertEquals(2, count)
        self.assertTrue(mock_get.called)

    @patch.object(rest_client.Client, "GET")
    def test_get_a_registered_finder(self, mock_get):
        class api:
            content = StringIO("<root><field1>Hello</field1></root>")
            response_code = 200

        mock_get.return_value = api()
        Simple.objects.get(field1="baz")
        self.assertTrue(mock_get.called)

    @patch.object(rest_client.Client, "GET")
    def test_get_for_a_multi_field_registered_finder(self, mock_get):
        class api:
            content = StringIO("<root><field1>Hello</field1></root>")
            response_code = 200

        mock_get.return_value = api()
        Simple.objects.get(a="foo", b="bar")
        self.assertTrue(mock_get.called)
        self.assertEquals("http://foo.com/simple/foo/bar", mock_get.call_args[0][0])

    @patch.object(rest_client.Client, "GET")
    def test_accepts_strings_as_finder_keys(self, mock_get):
        class api:
            content = StringIO("<root><field1>Hello</field1></root>")
            response_code = 200

        mock_get.return_value = api()
        Simple.objects.get(a="foo", b="bar")
        self.assertTrue(mock_get.called)
        self.assertEquals("http://foo.com/simple/foo/bar", mock_get.call_args[0][0])


    @patch.object(rest_client.Client, "GET")
    def test_raises_error_when_repsonse_empty(self, mock_get):
        class t:
            content = StringIO('')
            response_code = 200
        mock_get.return_value = t()

        with self.assertRaises(DoesNotExist):
            Simple.objects.get(field1="baz")

    @patch.object(rest_client.Client, "GET")
    def test_manager_raises_error_when_response_code_404(self, mock_get):
        class t:
            content = StringIO('<HTML><body>Nothing to see here</body></HTML>')
            response_code = 404
        mock_get.return_value = t()

        with self.assertRaises(DoesNotExist):
            Simple.objects.get(field1="baz")


    @patch.object(rest_client.Client, "GET")
    def test_returns_iterator_for_collection_of_results(self, mock_get):
        class t:
            content = StringIO("<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>")
        mock_get.return_value = t()
        qry = Simple.objects.filter(field1="baz")
        results = []
        for mod in qry:
            results.append(mod)
        self.assertEquals(2, len(results))
        self.assertEquals("hello", results[0].field1)
        self.assertEquals("goodbye", results[1].field1)

    @patch.object(rest_client.Client, "GET")
    def test_can_use_custom_query(self, mock_get):
        class t:
            content = StringIO("<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>")
            response_code = 200
        mock_get.return_value = t()

        Simple.objects.filter_custom("http://hard_coded_url").get()

        self.assertEquals("http://hard_coded_url", mock_get.call_args[0][0])

    @patch.object(rest_client.Client, "GET")
    def test_returns_iterator_for_collection_of_results_from_custom_query(self, mock_get):
        class t:
            content = StringIO("<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>")
        mock_get.return_value = t()
        qry = Simple.objects.filter_custom("http://hard_coded_url")
        results = []
        for mod in qry:
            results.append(mod)
        self.assertEquals(2, len(results))
        self.assertEquals("hello", results[0].field1)
        self.assertEquals("goodbye", results[1].field1)

    @patch.object(rest_client.Client, "GET")
    def test_returns_count_of_collection_of_results_when_len_is_called(self, mock_get):
        class t:
            content = StringIO("<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>")
        mock_get.return_value = t()
        qry = Simple.objects.filter(field1="baz")
        self.assertEquals(2, len(qry))

