import rest_client
from xml.etree import ElementTree as et

class ModelManager(object):
    """Handles what can be queried for, and acts as the entry point for querying.  There is an instance per model that is used
    in the django style of Model.objects.get(attr1=value, attr2=value2) for single results, or
    Model.objects.filter(attr1=value1,attr2=value2) for multiple results.  As with Django, you can chain filters together, i.e.
    Model.objects.filter(attr1=value1).filter(attr2=value2)  Filter is not evaluated until you try to iterate over the results or
    get a count of the results."""
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
        return ModelQuery(self, self.model, headers=self.headers).filter(**kw)

    def filter_custom(self, url):
        return ModelQuery(self, self.model, headers=self.headers).filter_custom(url)

    def count(self):
        raise NoRegisteredFinderError("foo")

    def get(self, **kw):
        return ModelQuery(self, self.model, headers=self.headers).get(**kw)


class ModelQuery(object):

    def __init__(self, manager, model, headers={}):
        self.manager = manager
        self.model = model
        self.args = {}
        self.headers = headers
        if 'xml_models' in str(model.__class__):
            self._fragments = self._xml_fragments
        elif 'json_models' in str(model.__class__):
            self._fragments = self._json_fragments
        else:
            raise NonSupportedModelError

    def filter(self, **kw):
        for key in kw.keys():
            self.args[key] = kw[key]
        return self

    def filter_custom(self, url):
        self.custom_url = url
        return self

    def count(self):
        response = rest_client.Client("").GET(self._find_query_path(), headers=self.headers)
        count = 0
        for x in self._fragments(response.content):
            count += 1
        return count

    def __iter__(self):
        response = rest_client.Client("").GET(self._find_query_path(), headers=self.headers)
        for fragment in self._fragments(response.content):
            yield self.model(fragment)

    def __len__(self):
        return self.count()

    def get(self, **kw):
        for key in kw.keys():
            self.args[key] = kw[key]
        response = rest_client.Client("").GET(self._find_query_path(), headers=self.headers)
        if not response.content:
            raise DoesNotExist(self.model, self.args)
        if response.response_code == 404:
            raise DoesNotExist(self.model, self.args)
        content = response.content.read()
        if not content:
            raise DoesNotExist(self.model, self.args)
        return self.model(content)

    def _xml_fragments(self, xml):
        tree = et.iterparse(xml, ['start','end'])
        tree.next()
        evt, child = tree.next()
        node_name = child.tag
        for event, elem in tree:
            if event == 'end' and elem.tag == node_name:
                result = et.tostring(elem)
                elem.clear()
                yield result

    def _json_fragments(self, json):
        for result in json.readlines():
            yield result

    def _find_query_path(self):
        if hasattr(self, 'custom_url'):
            return self.custom_url
        keys = self.args.keys()
        keys.sort()
        key_tuple = tuple(keys)
        try:
            (url, attrs) = self.manager.finders[key_tuple]
            return url % tuple([ self.args[x] for x in attrs])
        except KeyError:
            raise NoRegisteredFinderError(str(key_tuple))

class NoRegisteredFinderError(Exception):
    pass

class NonSupportedModelError(Exception):
    pass

class ValidationError(Exception):
    pass

class DoesNotExist(Exception):

    def __init__(self, model, args):
        Exception.__init__(self, "DoesNotExist: %s matching query %s does not exist" %(model.__name__, str(args)))

