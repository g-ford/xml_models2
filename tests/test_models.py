import unittest
from mock import Mock
import xml_models


class Muppet(xml_models.Model):
    name = xml_models.CharField(xpath='/root/kiddie/value')
    friends = xml_models.CollectionField(xml_models.CharField, xpath='/root/kiddie/friends/friend')

    finders = {
        (name,): "http://foo.com/muppets/%s"
    }


class BaseModelTestCases(unittest.TestCase):
    def setUp(self):
        self.muppet = Muppet(
    """<root>
        <kiddie>
            <value>Gonzo</value>
            <friends>
              <friend>Fozzie</friend>
            </friends>
        </kiddie>
    </root>""")

    def test_fields_are_settable(self):
        self.muppet.name = 'Fozzie'
        self.assertEquals('Fozzie', self.muppet.name)

    def test_may_validate_on_load(self):
        Muppet.validate_on_load = Mock(return_value=True)
        Muppet()
        Muppet.validate_on_load.assert_called_once

    def test_has_a_django_style_objects_attr(self):
        self.assertTrue(hasattr(self.muppet, 'objects'))

    def test_collection_fields_can_be_appended_to(self):
        self.assertEqual(1, len(self.muppet.friends))
        self.muppet.friends.append('Kermit')
        self.assertTrue('Fozzie' in self.muppet.friends)
        self.assertTrue('Kermit' in self.muppet.friends)

    def test_can_get_xml_back_out(self):
        self.assertEqual(strip_whitespace(self.muppet.to_xml()), strip_whitespace("""<root>
        <kiddie>
            <value>Gonzo</value>
            <friends>
              <friend>Fozzie</friend>
            </friends>
        </kiddie>
    </root>""") + "\n")


    def test_can_get_altered_xml_back_out(self):
        self.muppet.name = 'Kermit'
        self.assertEqual(strip_whitespace(self.muppet.to_xml()), strip_whitespace("""<root>
        <kiddie>
            <value>Kermit</value>
            <friends>
              <friend>Fozzie</friend>
            </friends>
        </kiddie>
    </root>""") + "\n")

    def test_can_get_altered_attributes_xml_back_out(self):
        class AttrModel(xml_models.Model):
            field1 = xml_models.IntField(xpath='/root/child/value/@count')

        m = AttrModel('<root><child><value count="1">Fred</value></child></root>')
        m.field1 = 2
        self.assertEqual(strip_whitespace(m.to_xml()), '<root><child><value count="2">Fred</value></child></root>\n')



def strip_whitespace(xml):
    import re
    return re.sub('>\s*<', '><', xml)