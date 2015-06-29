import unittest
from mock import Mock
import xml_models


class Muppet(xml_models.Model):
    name = xml_models.CharField(xpath='/root/kiddie/value')
    friends = xml_models.CollectionField(xml_models.CharField, xpath='/root/kiddie/friends/friend')

    finders = {
        (name,): "http://foo.com/muppets/%s"
    }


muppet = Muppet(
    """<root>
        <kiddie>
            <value>Gonzo</value>
            <friends>
              <friend>Fozzie</friend>
            </friends>
        </kiddie>
    </root>""")


class BaseModelTestCases(unittest.TestCase):
    def test_fields_are_settable(self):
        muppet.name = 'Fozzie'
        self.assertEquals('Fozzie', muppet.name)

    def test_may_validate_on_load(self):
        Muppet.validate_on_load = Mock(return_value=True)
        Muppet()
        Muppet.validate_on_load.assert_called_once

    def test_has_a_django_style_objects_attr(self):
        self.assertTrue(hasattr(muppet, 'objects'))

    def test_collection_fields_can_be_appended_to(self):
        self.assertEqual(1, len(muppet.friends))
        muppet.friends.append('Kermit')
        self.assertTrue('Fozzie' in muppet.friends)
        self.assertTrue('Kermit' in muppet.friends)


