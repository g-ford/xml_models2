"""
Copyright 2009 Chris Tarttelin and Point2 Technologies

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of
conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this list
of conditions and the following disclaimer in the documentation and/or other materials
provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE FREEBSD PROJECT ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE FREEBSD PROJECT OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of the FreeBSD Project.
"""

import unittest
from xml_models import *
from models_stub import stub
import xml_models.xpath_twister as xpath
import rest_client
from mock import patch
from StringIO import StringIO
from stubserver import StubServer

class Address(Model):
    number = IntField(xpath='/address/number')
    street = CharField(xpath='/address/street')
    city = CharField(xpath='/address/city')
    foobars = Collection(CharField, xpath='/address/foobar')

    finders = { (number,): "http://address/number/%s",
                (number, street): "http://address/number/%s/street/%s",
                (city,): "http://localhost:8998/address/%s",
                (street, 'stringfield'): "http://address/street/%s/stringfield/%s"
              }

class MyModel(Model):
    muppet_name = CharField(xpath='/root/kiddie/value')
    muppet_type = CharField(xpath='/root/kiddie/type', default='frog')
    muppet_names = Collection(CharField, xpath='/root/kiddie/value')
    muppet_ages = Collection(IntField, xpath='/root/kiddie/age')
    muppet_addresses = Collection(Address, xpath='/root/kiddie/address', order_by='number')

    finders = { 
                (muppet_name,): "http://foo.com/muppets/%s"
              }

class XmlModelsTest(unittest.TestCase):
    
    def test_char_field_returns_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><kiddie><value>Muppets rock</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = CharField(xpath='/root/kiddie/value')
        response = field.parse(xml, None)
        self.assertEquals('Muppets rock', response) 
        
    def test_char_field_reads_from_attribute(self):
        xml_string = '<Listing><Details><Bathrooms comment="Nice Baths">6</Bathrooms></Details></Listing>'
        xml = xpath.domify(xml_string)
        field = CharField(xpath='/Listing/Details/Bathrooms/@comment')
        response = field.parse(xml, None)
        self.assertEquals('Nice Baths', response)
        
    def test_int_field_returns_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><kiddie><value>123</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = IntField(xpath='/root/kiddie/value')
        response = field.parse(xml, None)
        self.assertEquals(123, response)
        
    def test_int_field_raises_exception_when_non_int_value_is_parsed(self):
        xml_string = '<root><kiddie><value>NaN</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = IntField(xpath='/root/kiddie/value')
        try:
            response = field.parse(xml, None)
            self.fail('Should have raised an exception')
        except:
            pass
            # Exception raised, all is right with the world
            
    def test_int_field_reads_from_attribute(self):
        xml_string = '<Listing id="123"/>'
        xml = xpath.domify(xml_string)
        field = IntField(xpath='/Listing/@id')
        response = field.parse(xml, None)
        self.assertEquals(123, response)
    
    def test_date_field_returns_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><kiddie><value>2008-06-21T10:36:12</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = DateField(xpath='/root/kiddie/value')
        response = field.parse(xml,None)
        date = datetime.datetime(2008,06,21,10,36,12)
        self.assertEquals(date, response)
            
    def test_date_field_strips_utc_offset_from_xpathed_value_for_the_node_passed_in(self):
        xml_string = '<root><kiddie><value>2008-06-21T10:36:12-06:00</value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = DateField(xpath='/root/kiddie/value')
        response = field.parse(xml,None)
        date = datetime.datetime(2008,06,21,10,36,12)
        self.assertEquals(date, response)
        
    def test_date_field_returns_none_when_xpathed_value_for_the_node_is_none(self):
        xml_string = '<root><kiddie><value></value></kiddie></root>'
        xml = xpath.domify(xml_string)
        field = DateField(xpath='/root/kiddie/value')
        response = field.parse(xml, None)
        self.assertEquals(None, response)
    
    def test_bool_field_returns_false_when_xpathed_value_for_the_node_is_false(self):
        xml_string = '<root><kiddie1><value1>false</value1></kiddie1></root>'
        xml = xpath.domify(xml_string)
        field = BoolField(xpath='/root/kiddie1/value1')
        response = field.parse(xml, None)
        self.assertEquals(False, response)

    def test_bool_field_returns_true_when_xpathed_value_for_the_node_is_true(self):
        xml_string = '<root><kiddie1><value>true</value></kiddie1></root>'
        xml = xpath.domify(xml_string)
        field = BoolField(xpath='/root/kiddie1/value')
        response = field.parse(xml, None)
        self.assertEquals(True, response)
    
    def test_can_retrieve_attribute_value_from_xml_model(self):
        my_model = MyModel('<root><kiddie><value>Rowlf</value></kiddie></root>')
        self.assertEquals('Rowlf', my_model.muppet_name)
        
    def test_returns_none_if_non_required_attribute_not_in_xml_and_no_default(self):
        my_model = MyModel('<root><kiddie><valuefoo>Rolf</valuefoo></kiddie></root>')
        self.assertEquals(None, my_model.muppet_name)
    
    def test_returns_default_if_non_required_attribute_not_in_xml_and_default_specified(self):
        my_model = MyModel('<root><kiddie><value>Rowlf</value></kiddie></root>')
        self.assertEquals('frog', my_model.muppet_type)
        
    def test_one_to_one_returns_sub_component(self):
        my_model = MasterModel(xml="<master><sub><name>fred</name></sub></master>")
        self.assertEquals("fred", my_model.sub_model.name)
        
    def test_collection_returns_expected_number_of_correcty_typed_results(self):
        my_model = MyModel('<root><kiddie><value>Rowlf</value><value>Kermit</value><value>Ms.Piggy</value></kiddie></root>')
        self.assertTrue('Rowlf' in my_model.muppet_names)
        self.assertTrue('Kermit' in my_model.muppet_names)
        self.assertTrue('Ms.Piggy' in my_model.muppet_names)    
        
    def test_collection_returns_expected_number_of_integer_results(self):
        my_model = MyModel('<root><kiddie><age>10</age><age>5</age><age>7</age></kiddie></root>')
        self.assertTrue(5 in my_model.muppet_ages)
        self.assertTrue(7 in my_model.muppet_ages)
        self.assertTrue(10 in my_model.muppet_ages)
        
    def test_collection_returns_user_model_types(self):
        my_model = MyModel('<root><kiddie><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city><foobar>foo</foobar><foobar>bar</foobar></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
        self.assertEquals(2,len(my_model.muppet_addresses))
        address1 = my_model.muppet_addresses[0]
        self.assertEquals(5, address1.number)
        self.assertEquals('Mockingbird Lane', address1.street)
        self.assertEquals('Bedrock', address1.city)
        address2 = my_model.muppet_addresses[1]
        self.assertEquals(10, address2.number)
        self.assertEquals('1st Ave. South', address2.street)
        self.assertEquals('MuppetVille', address2.city)
        self.assertEquals('foo', address2.foobars[0])
        self.assertEquals('bar', address2.foobars[1])
        
    def test_collection_orders_by_supplied_attribute_of_user_model_types(self):
        my_model = MyModel('<root><kiddie><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city><foobar>foo</foobar><foobar>bar</foobar></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
        self.assertEquals(2,len(my_model.muppet_addresses))
        address1 = my_model.muppet_addresses[0]
        self.assertEquals(5, address1.number)
        address2 = my_model.muppet_addresses[1]
        self.assertEquals(10, address2.number)
        
    def test_collection_empty_collection_returned_when_xml_not_found(self):
        my_model = MyModel('<root><kiddie><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
        self.assertEquals([], my_model.muppet_addresses[0].foobars)
        
    def test_use_a_default_namespace(self):
        nsModel = NsModel("<root xmlns='urn:test:namespace'><name>Finbar</name><age>47</age></root>")
        self.assertEquals('Finbar', nsModel.name)
        self.assertEquals(47, nsModel.age)
        
    def test_model_fields_are_settable(self):
        my_model = MyModel('<root><kiddie><value>Gonzo</value><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
        my_model.muppet_name = 'Fozzie'
        self.assertEquals('Fozzie', my_model.muppet_name)
        
    def test_collection_fields_can_be_appended_to(self):
        my_model = MyModel('<root><kiddie><value>Gonzo</value><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>')
        my_model.muppet_names.append('Fozzie')
        self.assertTrue('Fozzie' in my_model.muppet_names)
        self.assertTrue('Gonzo' in my_model.muppet_names)

    def test_manager_noregisteredfindererror_raised_when_filter_on_non_existent_field(self):
        try:
            MyModel.objects.filter(foo="bar").count()
            self.fail("expected NoRegisteredFinderError")
        except NoRegisteredFinderError, e:
            self.assertTrue("foo" in str(e))

    def test_should_handle_models_with_no_data(self):
        my_model = MyModel()
        my_model.muppet_name

    @patch.object(rest_client.Client, "GET")
    def test_manager_queries_rest_service_when_filtering_for_a_registered_finder(self, mock_get):
        class t:
            content = StringIO("<elems><root><kiddie><value>Gonzo</value><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root></elems>")
        mock_get.return_value = t()
        count = MyModel.objects.filter(muppet_name="baz").count()
        self.assertEquals(1, count)
        self.assertTrue(mock_get.called)
        
    @patch.object(rest_client.Client, "GET")
    def test_manager_counts_child_nodes_when_filtering_a_collection_of_results(self, mock_get):
        class t:
            content = StringIO("<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>")
        mock_get.return_value = t()
        count = Simple.objects.filter(field1="baz").count()
        self.assertEquals(2, count)
        self.assertTrue(mock_get.called)
        
    @patch.object(rest_client.Client, "GET")
    def test_manager_queries_rest_service_when_getting_for_a_registered_finder(self, mock_get):
        class t:
            content = StringIO("<root><kiddie><value>Gonzo</value><address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address><address><number>5</number><street>Mockingbird Lane</street><city>Bedrock</city></address></kiddie></root>")
            response_code = 200
        mock_get.return_value = t()
        val = MyModel.objects.get(muppet_name="baz")
        self.assertEquals("Gonzo", val.muppet_name)
        self.assertTrue(mock_get.called)
        
    @patch.object(rest_client.Client, "GET")
    def test_manager_queries_rest_service_when_getting_for_a_multi_field_registered_finder(self, mock_get):
        class t:
            content = StringIO("<address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address>")
            response_code = 200
        mock_get.return_value = t()
        val = Address.objects.get(street="foo", number="bar")
        self.assertEquals("1st Ave. South", val.street)
        self.assertTrue(mock_get.called)
        self.assertEquals("http://address/number/bar/street/foo", mock_get.call_args[0][0])
        
    @patch.object(rest_client.Client, "GET")
    def test_manager_queries_rest_service_accepting_strings_as_finder_keys(self, mock_get):
        class t:
            content = StringIO("<address><number>10</number><street>1st Ave. South</street><city>MuppetVille</city></address>")
            response_code = 200
        mock_get.return_value = t()
        val = Address.objects.get(street="foo", stringfield="bar")
        self.assertEquals("1st Ave. South", val.street)
        self.assertTrue(mock_get.called)
        self.assertEquals("http://address/street/foo/stringfield/bar", mock_get.call_args[0][0])
    

    @patch.object(rest_client.Client, "GET")
    def test_manager_raises_error_when_getting_for_a_registered_finder_and_repsonse_empty(self, mock_get):
        class t:
            content = StringIO('')
            response_code = 200
        mock_get.return_value = t()
        try:
            MyModel.objects.get(muppet_name="baz")
            self.fail("Expected DoesNotExist")
        except DoesNotExist, e:    
            self.assertTrue("DoesNotExist" in str(e))
    
    @patch.object(rest_client.Client, "GET")
    def test_manager_raises_error_when_getting_for_a_registered_finder_and_repsonse_code_404(self, mock_get):
        class t:
            content = StringIO('<HTML><body>Nothing to see here</body></HTML>')
            response_code = 404
        mock_get.return_value = t()
        try:
            MyModel.objects.get(muppet_name="baz")
            self.fail("Expected DoesNotExist")
        except DoesNotExist, e:
            self.assertTrue("DoesNotExist" in str(e))
            
    @patch.object(rest_client.Client, "GET")
    def test_manager_raises_validation_error_on_load_when_validation_test_fails(self, mock_get):
        class t:
            content = StringIO('<HTML><body>Nothing to see here</body></HTML>')
            response_code = 200
        mock_get.return_value = t()   
        try:
            MyValidatingModel.objects.get(muppet_name="baz")
            self.fail("Expected XmlValidationError")
        except XmlValidationError, e:
            self.assertEquals("What, no muppet name?", str(e))

    @patch.object(rest_client.Client, "GET")
    def test_manager_returns_iterator_for_collection_of_results(self, mock_get):
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
    def test_manager_returns_iterator_for_collection_of_results_from_custom_query(self, mock_get):
        class t:
            content = StringIO("<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>")
        mock_get.return_value = t()
        qry = SimpleWithoutFinder.objects.filter_custom("http://hard_coded_url")
        results = []
        for mod in qry:
            results.append(mod)
        self.assertEquals(2, len(results))
        self.assertEquals("hello", results[0].field1)
        self.assertEquals("goodbye", results[1].field1)

    @patch.object(rest_client.Client, "GET")
    def test_manager_returns_count_of_collection_of_results_when_len_is_called(self, mock_get):
        class t:
            content = StringIO("<elems><root><field1>hello</field1></root><root><field1>goodbye</field1></root></elems>")
        mock_get.return_value = t()
        qry = Simple.objects.filter(field1="baz")
        self.assertEquals(2, len(qry))
        
    @stub(MyModel)
    def test_stub_allows_stubbing_return_values_for_queries(self):
        MyModel.stub().get(muppet_name='Kermit').returns(muppet_name='Kermit', muppet_type='toad', muppet_names=['Trevor', 'Kyle'])
        result = MyModel.objects.get(muppet_name='Kermit')
        self.assertEquals('toad', result.muppet_type)
        
    @stub(MyModel)
    def test_stub_allows_stubbing_filter_requests(self):
        MyModel.stub().filter(muppet_name='Kermit').returns(dict(muppet_name='Kermit', muppet_type='toad', muppet_names=['Trevor', 'Kyle']))
        result = MyModel.objects.filter(muppet_name='Kermit')
        self.assertEquals(1, len(result))
        self.assertEquals('toad',list(result)[0].muppet_type)
    
    @stub(MyModel)
    def test_stub_allows_stubbing_filter_custom_requests(self):
        MyModel.stub().filter_custom('http://anyurl.com').returns(dict(muppet_name='Kermit', muppet_type='toad', muppet_names=['Trevor', 'Kyle']))
        result = MyModel.objects.filter_custom('http://anyurl.com')
        self.assertEquals(1, len(result))
        self.assertEquals('toad',list(result)[0].muppet_type)
        
    def test_stub_allows_stubbing(self):
        @stub('MyModel')
        def test_something_to_do_with_mymodel(self):
            pass
        self.assertEquals('test_something_to_do_with_mymodel', test_something_to_do_with_mymodel.__name__)

    @stub(MyModel)
    def test_stub_allows_stubbing_to_raise_exception(self):
        class SesameStreetCharacter(Exception):
            pass
        MyModel.stub().get(muppet_name='Big Bird').raises(SesameStreetCharacter)
        try:
            result = MyModel.objects.get(muppet_name='Big Bird')
            self.fail("Stub should have raised exception")
        except SesameStreetCharacter:
            pass

    def test_headers_field_specified_on_model_is_added_to_the_query_manager(self):
        self.assertTrue(Simple.objects.headers != None)
        self.assertEquals('user1', Simple.objects.headers['user'])
        query = Simple.objects.filter(field1="Rhubarb")
        self.assertTrue(query.headers != None)
        self.assertEquals('pwd1', query.headers['password'])
    
class FunctionalTest(unittest.TestCase):
    def setUp(self):
        self.server = StubServer(8998)
        self.server.run()
        
    def tearDown(self):
        self.server.stop()
        self.server.verify()
        
    def test_get_with_file_call(self):
        self.server.expect(method="GET", url="/address/\w+$").and_return(mime_type="text/xml", content="<address><number>12</number><street>Early Drive</street><city>Calgary</city></address>")
        address = Address.objects.get(city="Calgary")
        self.assertEquals("Early Drive", address.street)


class MyValidatingModel(Model):
    muppet_name = CharField(xpath='/root/kiddie/value')
    muppet_type = CharField(xpath='/root/kiddie/type', default='frog')
    muppet_names = Collection(CharField, xpath='/root/kiddie/value')
    muppet_ages = Collection(IntField, xpath='/root/kiddie/age')
    muppet_addresses = Collection(Address, xpath='/root/kiddie/address', order_by='number')

    def validate_on_load(self):
        if not self.muppet_name:
            raise XmlValidationError("What, no muppet name?")

    finders = { 
                (muppet_name,): "http://foo.com/muppets/%s"
              }
              
class NsModel(Model):
    namespace='urn:test:namespace'
    name=CharField(xpath='/root/name')
    age=IntField(xpath='/root/age')

class Simple(Model):
    field1 = CharField(xpath='/root/field1')
    
    finders = {
               (field1,): "http://foo.com/simple/%s"
              }
    headers = {'user': 'user1', 'password': 'pwd1'}
class SimpleWithoutFinder(Model):
    field1 = CharField(xpath='/root/field1')

class SubModel(Model):
    name = CharField(xpath='/sub/name')

class MasterModel(Model):
    sub_model = OneToOneField(SubModel, xpath='/master/sub')

def main():
    unittest.main()    

if __name__=='__main__':
    main()
