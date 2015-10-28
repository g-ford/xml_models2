from __future__ import absolute_import
import xml_models
import xml_models.rest_client as rest_client
from lxml import etree
from xml_models.xpath_finder import MultipleNodesReturnedException
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO


class ModelManager(object):
    """
    Handles what can be queried for, and acts as the entry point for querying.

    The API and usage is intended to be familiar to Django users however it does not support the complete Django
    ModelManager API.

    """

    def __init__(self, model, finders):
        self.model = model
        self.finders = {}
        self.headers = {}
        for key in finders.keys():
            field_names = [field if isinstance(field, str) else field._name for field in key]
            sorted_field_names = list(field_names)
            sorted_field_names.sort()
            self.finders[tuple(sorted_field_names)] = (finders[key], field_names)

    def filter(self, **kw):
        """
        Filter models by key-value pairs.

        :Example:

        .. code-block:: python

            Model.objects.filter(attr1=value1,attr2=value2)

        How the actual HTTP request is handled is determined by :ref:`finders`.

        :param kw: key value pairs of field name and value
        :return: lazy query
        """
        return ModelQuery(self, self.model, headers=self.headers).filter(**kw)

    def filter_custom(self, url):
        """
        Set a URL to be called when querying

        :param url: full URL
        :return: lazy query
        """
        return ModelQuery(self, self.model, headers=self.headers).filter_custom(url)

    def count(self):
        """
        Get a count

        :return: int
        """
        return ModelQuery(self, self.model, headers=self.headers).count()

    def get(self, **kw):
        """
        Get a single object.

        This can be called directly with key-value pairs or after setting some ``filters``

        :param kw:
        :return:
        """
        return ModelQuery(self, self.model, headers=self.headers).get(**kw)


# this is an internal class and should not be exposed to end users so we don't need docstrings
# pylint: disable=missing-docstring
class ModelQuery(object):
    def __init__(self, manager, model, headers=None):
        self.manager = manager
        self.model = model
        self.args = {}
        self.headers = headers or {}
        self.custom_url = None


        # When calling list(query) list will call __count__ before __iter__, both of which will call _fetch &
        # _fragments. We keep a cache of fetched URLs and parsed out fragments so as to prevent fetching and parsing
        # the tree twice.
        self.__fragment_cache = []
        self.__fetch_cache = {}

    def filter(self, **kw):
        for key in kw.keys():
            self.args[key] = kw[key]
        return self

    def filter_custom(self, url):
        self.custom_url = url
        return self

    def count(self):
        response = self._fetch()
        return len(list(self._fragments(response.content)))

    def __iter__(self):
        response = self._fetch()
        for fragment in self._fragments(response.content):
            yield self.model(fragment)

    def __len__(self):
        return self.count()

    def get(self, **kw):
        for key in kw.keys():
            self.args[key] = kw[key]
        response = self._fetch()
        if not response.content or response.response_code == 404:
            raise DoesNotExist(self.model, self.args)

        if not response.content:
            raise DoesNotExist(self.model, self.args)

        content = response.content

        node_to_find = getattr(self.model, 'collection_node', None)
        if node_to_find:
            tree = etree.fromstring(content)
            node = tree.find('.//' + node_to_find).getchildren()
            if len(node) > 1:
                raise MultipleNodesReturnedException
            content = etree.tostring(node[0])

        return self.model(content)

    def _fetch(self):
        # the caching here may be better handled with requests caching?
        url = self._find_query_path()
        if not url in self.__fetch_cache:
            self.__fetch_cache[url] = rest_client.Client("", verify=xml_models.VERIFY).GET(url, headers=self.headers)
        return self.__fetch_cache[url]

    def _fragments(self, xml):
        if len(self.__fragment_cache):
            for item in self.__fragment_cache:
                yield item
            return

        if not xml:
            raise DoesNotExist(self.model, self.args)

        xpath_to_find = getattr(self.model, 'collection_xpath', None)
        if xpath_to_find:
            tree = etree.parse(StringIO(xml.encode()))
            for node in tree.xpath(xpath_to_find):
                yield etree.tostring(node)
            return

        node_to_find = getattr(self.model, 'collection_node', None)
        tree = etree.iterparse(StringIO(xml.encode()), ['start', 'end'])
        _, child = next(tree)

        while node_to_find and child.tag != node_to_find:
            _, child = next(tree)

        _, child = next(tree)

        node_stack = [child.tag]
        for event, elem in tree:
            if event == 'start':
                node_stack.append(elem.tag)
            if event == 'end':
                if len(node_stack) == 0:
                    continue  # we've gone past our collection node into the parent nodes
                node_stack.pop()
            if event == 'end' and len(node_stack) == 0:
                result = etree.tostring(elem)
                elem.clear()
                self.__fragment_cache.append(result)
                yield result

    def _find_query_path(self):
        if self.custom_url:
            return self.custom_url

        keys = self.args.keys()
        keys = sorted(keys)
        key_tuple = tuple(keys)
        try:
            (url, attrs) = self.manager.finders[key_tuple]
            return url % tuple([self.args[x] for x in attrs])
        except KeyError:
            raise NoRegisteredFinderError(str(key_tuple))


class NoRegisteredFinderError(Exception):
    pass


class ValidationError(Exception):
    pass


class DoesNotExist(Exception):
    def __init__(self, model, args):
        Exception.__init__(self, "DoesNotExist: %s matching query %s does not exist" % (model.__name__, str(args)))

