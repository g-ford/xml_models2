import unittest
import xml_models
from mock import patch
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from lxml import objectify
import datetime
from xml_models.xpath_finder import MultipleNodesReturnedException

XML = objectify.fromstring("""
    <root>
      <kiddie>
        <char comment="Nice">Muppets rock</char>
        <int>11</int>
        <float>11.11</float>
        <bools many="True">
          <bool>False</bool>
        </bools>
        <empty />
      </kiddie>
    </root>""")


class BaseFieldTests(unittest.TestCase):
    def test_raises_when_xpath_is_missing(self):
        with self.assertRaises(Exception):
            xml_models.BaseField()

    def test_can_read_from_innertext(self):
        field = xml_models.BaseField(xpath='/root/kiddie/char')
        response = field._fetch_by_xpath(XML, None)
        self.assertEquals('Muppets rock', response)

    def test_can_read_from_attribute(self):
        field = xml_models.BaseField(xpath='/root/kiddie/char/@comment')
        response = field._fetch_by_xpath(XML, None)
        self.assertEquals('Nice', response)

    def test_returns_default_when_value_is_empty(self):
        field = xml_models.BaseField(xpath='/root/kiddie/empty', default='DEFAULT')
        response = field._fetch_by_xpath(XML, None)
        self.assertEquals('DEFAULT', response)

    def test_returns_none_when_value_is_empty_and_no_deafult(self):
        field = xml_models.BaseField(xpath='/root/kiddie/empty')
        response = field._fetch_by_xpath(XML, None)
        self.assertEquals(None, response)


class CharFieldTests(unittest.TestCase):
    @patch.object(xml_models.BaseField, '_fetch_by_xpath')
    def test_uses_base(self, mock_base):
        field = xml_models.CharField(xpath='/root/kiddie/char')
        response = field.parse(XML, None)

        mock_base.assert_called_once


class IntFieldTests(unittest.TestCase):
    @patch.object(xml_models.BaseField, '_fetch_by_xpath')
    def test_uses_base(self, mock_base):
        field = xml_models.CharField(xpath='/root/kiddie/int')
        response = field.parse(XML, None)

        mock_base.assert_called_once

    def test_casts_to_int(self):
        field = xml_models.IntField(xpath='/root/kiddie/int')
        response = field.parse(XML, None)
        self.assertEquals(11, response)

    def test_raises_error_if_not_an_int(self):
        with self.assertRaises(ValueError):
            field = xml_models.IntField(xpath='/root/kiddie/char')
            response = field.parse(XML, None)

    def test_may_have_a_default(self):
        field = xml_models.CharField(xpath='/root/kiddie/int2', default=-1)
        response = field.parse(XML, None)
        self.assertEquals(-1, response)


class FloatFieldTests(unittest.TestCase):
    @patch.object(xml_models.BaseField, '_fetch_by_xpath')
    def test_uses_base(self, mock_base):
        field = xml_models.FloatField(xpath='/root/kiddie/int')
        response = field.parse(XML, None)

        mock_base.assert_called_once

    def test_casts_to_int(self):
        field = xml_models.FloatField(xpath='/root/kiddie/float')
        response = field.parse(XML, None)
        self.assertEquals(11.11, response)

    def test_raises_error_if_not_an_int(self):
        with self.assertRaises(ValueError):
            field = xml_models.FloatField(xpath='/root/kiddie/char')
            response = field.parse(XML, None)


class BoolFieldTests(unittest.TestCase):
    @patch.object(xml_models.BaseField, '_fetch_by_xpath')
    def test_uses_base(self, mock_base):
        field = xml_models.BoolField(xpath='/root/kiddie/bools/@many')
        response = field.parse(XML, None)

        mock_base.assert_called_once

    def test_can_cast_trues(self):
        field = xml_models.BoolField(xpath='/root/kiddie/bools/@many')
        response = field.parse(XML, None)
        self.assertTrue(response)

    def test_can_cast_false(self):
        field = xml_models.BoolField(xpath='/root/kiddie/bools/bool')
        response = field.parse(XML, None)
        self.assertFalse(response)


class DateFieldTests(unittest.TestCase):
    @patch.object(xml_models.BaseField, '_fetch_by_xpath')
    def test_uses_base(self, mock_base):
        mock_base.return_value = None
        field = xml_models.DateField(xpath='/root/kiddie/bools/@many')
        response = field.parse(XML, None)

        mock_base.assert_called_once

    def test_parses_basic_format(self):
        xml_string = '<root><kiddie><value>2008-06-21T10:36:12</value></kiddie></root>'
        xml = objectify.fromstring(xml_string)
        field = xml_models.DateField(xpath='/root/kiddie/value')
        response = field.parse(xml, None)
        date = datetime.datetime(2008, 6, 21, 10, 36, 12)
        self.assertEquals(date, response)

    def test_handles_utc_offset(self):
        import pytz

        xml_string = '<root><kiddie><value>2008-06-21T10:36:12-06:00</value></kiddie></root>'
        xml = objectify.fromstring(xml_string)
        field = xml_models.DateField(xpath='/root/kiddie/value')
        response = field.parse(xml, None)
        date = pytz.UTC.localize(datetime.datetime(2008, 6, 21, 16, 36, 12))
        self.assertEquals(date, response)

    def test_returns_none_when_the_node_is_empty(self):
        xml_string = '<root><kiddie><value></value></kiddie></root>'
        xml = objectify.fromstring(xml_string)
        field = xml_models.DateField(xpath='/root/kiddie/value')
        response = field.parse(xml, None)
        self.assertEquals(None, response)

    def test_allows_custom_date_fromat(self):
        xml_string = '<root><kiddie><value>20080621-10:36:12</value></kiddie></root>'
        xml = objectify.fromstring(xml_string)
        field = xml_models.DateField(xpath='/root/kiddie/value', date_format="%Y%m%d-%H:%M:%S")
        response = field.parse(xml, None)
        date = datetime.datetime(2008, 6, 21, 10, 36, 12)
        self.assertEquals(date, response)


class OneToOneFieldTests(unittest.TestCase):
    class SubModel(xml_models.Model):
        name = xml_models.CharField(xpath='/sub/name')

    def test_returns_sub_component(self):
        xml_string = "<master><sub><name>fred</name></sub></master>"
        xml = objectify.fromstring(xml_string)
        field = xml_models.OneToOneField(OneToOneFieldTests.SubModel, xpath='/master/sub')
        response = field.parse(xml, None)
        self.assertTrue(isinstance(response, OneToOneFieldTests.SubModel))
        self.assertEquals("fred", response.name)

    def test_throws_when_more_than_one(self):
        xml_string = "<master><sub><name>fred</name></sub><sub><name>jill</name></sub></master>"
        xml = objectify.fromstring(xml_string)
        field = xml_models.OneToOneField(OneToOneFieldTests.SubModel, xpath='/master/sub')
        with self.assertRaises(MultipleNodesReturnedException):
            field.parse(xml, None)

    def test_returns_default_when_empty(self):
        xml_string = "<master></master>"
        xml = objectify.fromstring(xml_string)

        field = xml_models.OneToOneField(OneToOneFieldTests.SubModel, xpath='/master/sub')
        response = field.parse(xml, None)
        self.assertIsNone(response)

        default = OneToOneFieldTests.SubModel()
        field = xml_models.OneToOneField(OneToOneFieldTests.SubModel, xpath='/master/sub',
                                         default=default)
        response = field.parse(xml, None)
        self.assertEqual(default, response)


class CollectionFieldTests(unittest.TestCase):
    class SubModel(xml_models.Model):
        name = xml_models.CharField(xpath='/sub/name')

    def test_returns_expected_number_of_correctly_typed_results(self):
        xml_string = '<master><sub><name>fred</name></sub><sub><name>jill</name></sub></master>'
        xml = objectify.fromstring(xml_string)

        field = xml_models.CollectionField(CollectionFieldTests.SubModel, xpath='/master/sub')
        response = field.parse(xml, None)

        self.assertEqual(2, len(response))
        for sub in response:
            self.assertTrue(isinstance(sub, CollectionFieldTests.SubModel))

    def test_orders_by_throws_if_unknown(self):
        xml_string = '<master><sub><name>fred</name></sub><sub><name>jill</name></sub><sub><name>alice</name></sub></master>'
        xml = objectify.fromstring(xml_string)

        field = xml_models.CollectionField(CollectionFieldTests.SubModel, xpath='/master/sub', order_by='not_real')
        with self.assertRaises(AttributeError):
            field.parse(xml, None)

    def test_order_by_supplied_attribute_of_user_model_types(self):
        xml_string = '<master><sub><name>fred</name></sub><sub><name>jill</name></sub><sub><name>alice</name></sub></master>'
        xml = objectify.fromstring(xml_string)

        field = xml_models.CollectionField(CollectionFieldTests.SubModel, xpath='/master/sub', order_by='name')
        response = field.parse(xml, None)

        self.assertEqual(3, len(response))
        self.assertEqual([e.name for e in response], ['alice', 'fred', 'jill'])

    def test_returns_empty_collection_when_empty(self):
        xml_string = '<master></master>'
        xml = objectify.fromstring(xml_string)

        field = xml_models.CollectionField(CollectionFieldTests.SubModel, xpath='/master/sub', order_by='name')
        response = field.parse(xml, None)

        self.assertEqual([], response)



#     def test_use_a_default_namespace(self):
#         nsModel = NsModel("<root xmlns='urn:test:namespace'><name>Finbar</name><age>47</age></root>")
#         self.assertEquals('Finbar', nsModel.name)
#         self.assertEquals(47, nsModel.age)



#
#     @stub(MyModel)
#     def test_stub_allows_stubbing_return_values_for_queries(self):
#         MyModel.stub().get(muppet_name='Kermit').returns(muppet_name='Kermit', muppet_type='toad', muppet_names=['Trevor', 'Kyle'])
#         result = MyModel.objects.get(muppet_name='Kermit')
#         self.assertEquals('toad', result.muppet_type)

#     @stub(MyModel)
#     def test_stub_allows_stubbing_filter_requests(self):
#         MyModel.stub().filter(muppet_name='Kermit').returns(dict(muppet_name='Kermit', muppet_type='toad', muppet_names=['Trevor', 'Kyle']))
#         result = MyModel.objects.filter(muppet_name='Kermit')
#         self.assertEquals(1, len(result))
#         self.assertEquals('toad',list(result)[0].muppet_type)

#     @stub(MyModel)
#     def test_stub_allows_stubbing_filter_custom_requests(self):
#         MyModel.stub().filter_custom('http://anyurl.com').returns(dict(muppet_name='Kermit', muppet_type='toad', muppet_names=['Trevor', 'Kyle']))
#         result = MyModel.objects.filter_custom('http://anyurl.com')
#         self.assertEquals(1, len(result))
#         self.assertEquals('toad',list(result)[0].muppet_type)

#     def test_stub_allows_stubbing(self):
#         @stub('MyModel')
#         def test_something_to_do_with_mymodel(self):
#             pass
#         self.assertEquals('test_something_to_do_with_mymodel', test_something_to_do_with_mymodel.__name__)

#     @stub(MyModel)
#     def test_stub_allows_stubbing_to_raise_exception(self):
#         class SesameStreetCharacter(Exception):
#             pass
#         MyModel.stub().get(muppet_name='Big Bird').raises(SesameStreetCharacter)
#         try:
#             result = MyModel.objects.get(muppet_name='Big Bird')
#             self.fail("Stub should have raised exception")
#         except SesameStreetCharacter:
#             pass


# class FunctionalTest(unittest.TestCase):
#     def setUp(self):
#         self.server = StubServer(8998)
#         self.server.run()

#     def tearDown(self):
#         self.server.stop()
#         self.server.verify()

#     def test_get_with_file_call(self):
#         self.server.expect(method="GET", url="/address/\w+$").and_return(mime_type="text/xml", content="<address><number>12</number><street>Early Drive</street><city>Calgary</city></address>")
#         address = Address.objects.get(city="Calgary")
#         self.assertEquals("Early Drive", address.street)


# class MyValidatingModel(Model):
#     muppet_name = CharField(xpath='/root/kiddie/value')
#     muppet_type = CharField(xpath='/root/kiddie/type', default='frog')
#     muppet_names = Collection(CharField, xpath='/root/kiddie/value')
#     muppet_ages = Collection(IntField, xpath='/root/kiddie/age')
#     muppet_addresses = Collection(Address, xpath='/root/kiddie/address', order_by='number')

#     def validate_on_load(self):
#         if not self.muppet_name:
#             raise XmlValidationError("What, no muppet name?")

#     finders = { 
#                 (muppet_name,): "http://foo.com/muppets/%s"
#               }

class NsModel(xml_models.Model):
    namespace = 'urn:test:namespace'
    name = xml_models.CharField(xpath='/root/name')
    age = xml_models.IntField(xpath='/root/age')


class Simple(xml_models.Model):
    field1 = xml_models.CharField(xpath='/root/field1')

    finders = {
        (field1,): "http://foo.com/simple/%s"
    }
    headers = {'user': 'user1', 'password': 'pwd1'}


class SimpleWithoutFinder(xml_models.Model):
    field1 = xml_models.CharField(xpath='/root/field1')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
