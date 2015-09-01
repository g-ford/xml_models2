from __future__ import absolute_import

import datetime
from xml_models import xpath_finder
from xml_models.managers import ModelManager
from dateutil.parser import parse as date_parser
from lxml import etree


# pylint: disable=too-few-public-methods
# Fields only need one public method
from xml_models.xpath_finder import MultipleNodesReturnedException


class BaseField:
    """
    Base class for Fields.  Should not be used directly
    """

    def __init__(self, **kw):
        """
        All fields must specify an ``xpath`` as a keyword argument in their constructor.  Fields may optionally specify
        a default value using the ``default`` keyword argument.

        :raises AttributeError: if xpath attribute is empty
        """
        if 'xpath' not in kw:
            raise AttributeError('No XPath supplied for xml field')
        self.xpath = kw['xpath']
        self._default = kw.pop('default', None)

    def _fetch_by_xpath(self, xml_doc, namespace):
        find = xpath_finder.find_unique(xml_doc, self.xpath, namespace)
        if find is None:
            return self._default
        return find


class CharField(BaseField):
    """
    Returns the single value found by the xpath expression, as a string
    """

    def parse(self, xml, namespace):
        """
        :param xml: the etree.Element to search in
        :param namespace: not used yet
        :rtype: string
        """
        return self._fetch_by_xpath(xml, namespace)


class IntField(BaseField):
    """
    Returns the single value found by the xpath expression, as an int
    """

    def parse(self, xml, namespace):
        """
        :param xml: the etree.Element to search in
        :param namespace: not used yet
        :rtype: DateTime, may be timezone aware or naive
        """
        value = self._fetch_by_xpath(xml, namespace)
        if value:
            return int(value)
        return self._default


class DateField(BaseField):
    """
    Returns the single value found by the xpath expression, as a ``datetime``.

    By default, expects dates that match the ISO8601 date format.  If a ``date_format`` keyword
    arg is supplied, that will be used instead. ``date_format`` should conform to ``strptime`` formatting options.

    If the XML contains UTC offsets then a timezone aware datetime object will be returned.
    """

    def __init__(self, date_format=None, **kw):
        BaseField.__init__(self, **kw)
        self.date_format = date_format

    def parse(self, xml, namespace):
        """
        :param xml: the etree.Element to search in
        :param namespace: not used yet
        :rtype: DateTime, may be timezone aware or naive
        """
        value = self._fetch_by_xpath(xml, namespace)
        if value:
            if self.date_format:
                return datetime.datetime.strptime(value, self.date_format)
            return date_parser(value)
        return self._default


class FloatField(BaseField):
    """
    Returns the single value found by the xpath expression, as a float
    """

    def parse(self, xml, namespace):
        """
        :param xml: the etree.Element to search in
        :param namespace: not used yet
        :rtype: float
        """
        value = self._fetch_by_xpath(xml, namespace)
        if value:
            return float(value)
        return self._default


class BoolField(BaseField):
    """
    Returns the single value found by the xpath expression, as a boolean
    """

    def parse(self, xml, namespace):
        """
        Recognises any-case TRUE or FALSE only i.e. wont parse 0 as False or 1 as True etc.

        :param xml: the etree.Element to search in
        :param namespace: not used yet
        :rtype: Bool
        """
        value = self._fetch_by_xpath(xml, namespace)
        if value is not None:
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
        return self._default


class CollectionField(BaseField):
    """
    Returns a collection found by the xpath expression.

    Requires a field_type to be supplied, which can either be a field type, e.g. :class:`IntField`, which returns a
    collection ints, or it can be a :class:`Model` type e.g. Person may contain a collection of Address objects.
    """

    def __init__(self, field_type, order_by=None, **kw):
        """
        :param field_type: class to cast to.  Should be a subclass of :class:`BaseField` or :class:`Model`
        :param order_by: the attribute in ``field_type`` to order the collection on. Asc only
        """
        self.field_type = field_type
        self.order_by = order_by
        BaseField.__init__(self, **kw)

    def parse(self, xml, namespace):
        """
        Find all nodes matching the xpath expression and create objects from each the matched node.

        If ``order_by`` has been defined then the resulting list will be ordered.

        :param xml: the etree.Element to search in
        :param namespace: not used yet
        :rtype: as defined by ``self.field_type``
        """
        matches = xpath_finder.find_all(xml, self.xpath, namespace)

        if BaseField not in self.field_type.__bases__:
            results = [self.field_type(xml=match) for match in matches]
        else:
            field = self.field_type(xpath='.')
            results = [field.parse(xpath_finder.domify(match), namespace) for match in matches]
        if self.order_by:
            from operator import attrgetter

            results.sort(key=attrgetter(self.order_by))
        return results


class OneToOneField(BaseField):
    """
    Returns a subclass of :class:`Model` from the xpath expression.
    """

    def __init__(self, field_type, **kw):
        """
        :param field_type: class to cast to.  Should be a subclass of :class:`BaseField` or :class:`Model`
        """
        self.field_type = field_type
        BaseField.__init__(self, **kw)

    def parse(self, xml, namespace):
        """
        :param xml: the etree.Element to search in
        :param namespace: not used yet
        :rtype: as defined by ``self.field_type``
        """
        match = xpath_finder.find_all(xml, self.xpath, namespace)
        if len(match) > 1:
            raise MultipleNodesReturnedException
        if len(match) == 1:
            return self.field_type(xml=match[0])
        return self._default


class ModelBase(type):
    """
    Meta class for declarative xml_model building
    """

    def __new__(mcs, name, bases, attrs):
        new_class = super(ModelBase, mcs).__new__(mcs, name, bases, attrs)
        xml_fields = [field_name for field_name in attrs.keys() if isinstance(attrs[field_name], BaseField)]
        setattr(new_class, 'xml_fields', xml_fields)
        for field_name in xml_fields:
            setattr(new_class, field_name, new_class._get_xpath(attrs[field_name]))
            attrs[field_name]._name = field_name
        if "finders" in attrs:
            setattr(new_class, "objects", ModelManager(new_class, attrs["finders"]))
        else:
            setattr(new_class, "objects", ModelManager(new_class, {}))
        if "headers" in attrs:
            setattr(new_class.objects, "headers", attrs["headers"])
        return new_class

    def _get_xpath(cls, field_impl):
        return property(fget=lambda cls: cls._parse_field(field_impl),
                        fset=lambda cls, value: cls._set_value(field_impl, value))


from future.utils import with_metaclass


class Model(with_metaclass(ModelBase)):
    """
    A model is a representation of the XML source, consisting of a number of Fields. It can be constructed with
    either an xml string, or an :class:`etree.Element`.

    :Example:

    .. code-block:: python

        class Person(xml_models.Model):
            namespace="urn:my.default.namespace"
            name = xml_models.CharField(xpath"/Person/@Name", default="John")
            nicknames = xml_models.CollectionField(CharField, xpath="/Person/Nicknames/Name")
            addresses = xml_models.CollectionField(Address, xpath="/Person/Addresses/Address")
            date_of_birth = xml_models.DateField(xpath="/Person/@DateOfBirth", date_format="%d-%m-%Y")

    If you define :ref:`finders` on your model you will also be able to retreive models from an API endpoint using
    a familiar Django-esque object manager style of access with chainable filtering etc.
    """

    def __init__(self, xml=None, dom=None):
        self._xml = xml
        self._dom = dom
        self._cache = {}
        self.validate_on_load()


    def validate_on_load(self):
        """
        Perform validation when the model is instantiated.

        Override on your model to perform validation when the XML data is first passed in.

        .. note:: You will need to raise appropriate exceptions as no checking of the return value occurs
        """
        pass

    def to_tree(self):
        """
        :class:`etree.Element` representation of :class:`Model`

        :rtype: :class:`lxml.etree.Element`
        """
        for field in self._cache:
            self._update_field(field)
        return self._get_tree()

    def to_xml(self):
        """
        XML representation of Model

        :rtype: string
        """
        return etree.tostring(self.to_tree(), pretty_print=True).decode('UTF-8')

    def _update_attribute(self, field):
        """
        Update the value of an attribute field.

        Assumes simple data type in the attribute that can be cast to string
        :param field: field to update
        """
        parts = field.xpath.split('/')
        xpath = "/".join(parts[:-1])  # I think it is safe to assume attributes are in the last place
        attr = parts[-1].replace('@', '')

        self._get_tree().xpath(xpath)[0].attrib[attr] = str(getattr(self, field._name))

    def _update_subtree(self, field):
        """
        Replace a whole subtree
        :param field: Model field with `to_tree`
        """
        new_tree = getattr(self, field._name).to_tree()
        old_tree = self._get_tree().xpath(field.xpath)[0]
        self._get_tree().replace(old_tree, new_tree)

    def _create_from_xpath(self, xpath, tree, value=None, extra_root_name=None):
        """
        Generates XML under `tree` that will satisfy `xpath`.  Will pre-populate `value` if given
        :param xpath: simple xpath only. Does not handle attributes, indexing etc.
        :param tree: parent tree
        :param value:
        :param value:
        :param extra_root_name: extra root node added for helping generating xml
        :return: Element node
        """
        # not handling attribute
        parts = [x for x in xpath.split('/') if x != '' and x[0] != '@']
        xpath = '' if extra_root_name is None else '/' + extra_root_name
        for part in parts[:-1]:  # save the last node
            xpath += '/' + part
            nodes = tree.xpath(xpath)

            if not nodes:
                node = etree.XML("<%s/>" % part)
                tree.append(node)
                tree = node
            else:
                tree = nodes[0]
        # now we create the missing last node
        node = etree.XML("<%s/>" % parts[-1])
        tree.append(node)

        if value:
            node.text = str(value)

        return node

    def _update_collection(self, field):
        """
        Update _dom with all the items in a CollectionField value

        :param field: CollectionField
        """
        try:
            from itertools import zip_longest
        except ImportError:
            from itertools import izip_longest as zip_longest

        new_values = getattr(self, field._name)
        old_values = self._get_tree().xpath(field.xpath)

        collection_xpath = "/".join(field.xpath.split('/')[:-1])
        collection_node = self._get_tree().xpath(collection_xpath)[0]

        for old, new in zip_longest(old_values, new_values):
            if not new:
                old.getparent().remove(old)
                continue

            if isinstance(field.field_type, ModelBase):
                xml = etree.fromstring(new.to_xml())
                if old is None:
                    collection_node.append(xml)
                else:
                    collection_node.replace(old, xml)
                continue

            if old is None:
                self._create_from_xpath(field.xpath, self._get_tree(), new)
            else:
                old.text = new

    def _update_field(self, field):
        """
        Update _dom with value from field

        :param field: BaseField
        :return:
        """
        if '@' in field.xpath:
            self._update_attribute(field)
        elif isinstance(field, CollectionField):
            self._update_collection(field)
        elif isinstance(field, OneToOneField):
            self._update_subtree(field)
        else:
            node = self._get_tree().xpath(field.xpath)
            value = str(getattr(self, field._name))
            if node:
                node[0].text = value
            else:
                self._create_from_xpath(field.xpath, self._get_tree(), value)

    def _get_tree(self):
        if self._dom is None:
            self._dom = xpath_finder.domify(self._get_xml())
        return self._dom

    def _get_xml(self):
        if not self._xml:
            # create a fake root node that will get stripped off later
            tree = etree.Element('RrootR')
            for field in self._cache:
                self._create_from_xpath(field.xpath, tree, extra_root_name='RrootR')
            self._xml = etree.tostring(tree[0])

        return self._xml

    def _set_value(self, field, value):
        self._cache[field] = value

    def _parse_field(self, field):
        if field not in self._cache:
            namespace = getattr(self, 'namespace', None)
            self._cache[field] = field.parse(self._get_tree(), namespace)
        return self._cache[field]
