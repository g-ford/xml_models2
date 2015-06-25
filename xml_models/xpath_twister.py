# this fallback path is taken from http://lxml.de/1.3/tutorial.html
try:
  from lxml import etree
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
        except ImportError:
          raise


class MultipleNodesReturnedException(Exception):
    pass
    
def find_unique(xml_doc, expression, namespace=None):
        if namespace:
            find = etree.XPath(get_xpath(expression, namespace), namespaces={'x': namespace})
        else:
            find = etree.XPath(get_xpath(expression, namespace))
        matches = find(xml_doc)
        if len(matches) == 1:
            matched = matches[0]
            if type(matched) == type(''):
                return unicode(matched).strip()
            if isinstance(matched, etree._ElementStringResult):
                 return str(matched)
            if isinstance(matched, etree._ElementUnicodeResult):
                return unicode(matched)
            if matched is None or matched == False:
                return unicode(matched.text).strip()
            if isinstance(matched, etree._Element):
                if matched.text is not None:
                    return unicode(matched.text)
        if len(matches) > 1:
            raise MultipleNodesReturnedException
    
def find_all(xml, expression, namespace):
    if namespace:
        find = etree.XPath(get_xpath(expression, namespace), namespaces={'x': namespace})
    else:
        find = etree.XPath(get_xpath(expression,namespace))
    matches = find(xml)
    return [etree.tostring(match) for match in matches]

def domify(xml):
    if lxml_available:
        return objectify.fromstring(xml)
    else:
        return minidom.parseString(xml)
            
def get_xpath(xpath, namespace):
    # if namespace:
    #     xpath_list = xpath.split('/')
    #     xpath_with_ns = ""
    #     for element in xpath_list:
    #         if not element.startswith('@') and not element == '' :
    #             xpath_with_ns += "/x:" + element
    #         elif element == '':
    #             pass
    #         else:
    #             xpath_with_ns += "/" + element
    #     return xpath_with_ns
    # else:
    return xpath


import unittest
class XPathTest(unittest.TestCase):
    
    def test_xpath_returns_expected_element_value(self):
        #setup
        xml = minidom.parseString("<foo><baz>dcba</baz><bar>abcd</bar></foo>")
        #execute
        val = _pydom_xpath(xml, "/foo/bar", None)
        #assert
        self.assertEquals("abcd", val)
        
    def test_xpath_returns_expected_element_value_from_unicode_xml_fragment(self):
        #setup
        xml = minidom.parseString(u"<foo><baz>dcba</baz><bar>abcd\xe9</bar></foo>".encode('utf-8'))
        #execute
        val = _pydom_xpath(xml, "/foo/bar", None)
        #assert
        self.assertEquals(u"abcd\xe9", val)
    
    def test_xpath_returns_expected_attribute_value(self):
        #setup
        xml = minidom.parseString('<foo><baz name="Arthur">dcba</baz><bar>abcd</bar></foo>')
        #execute
        val = _pydom_xpath(xml, "/foo/baz/@name", None)
        #assert
        self.assertEquals("Arthur", val)
        
    def test_xpath_returns_expected_attribute_value_from_unicode_xml_fragment(self):
        #setup
        xml = minidom.parseString(u'<foo><baz name="Arthur\xe9">dcba</baz><bar>abcd</bar></foo>'.encode('utf-8'))
        #execute
        val = _pydom_xpath(xml, "/foo/baz/@name", None)
        #assert
        self.assertEquals(u"Arthur\xe9", val)
    
    def test_lxml_returns_expected_element_value(self):
        #setup
        xml = objectify.fromstring('<foo><baz name="Arthur">dcba</baz><bar>abcd</bar></foo>')
        #execute
        val = _lxml_xpath(xml, "/foo/bar", None)
        #assert
        self.assertEquals("abcd", val)
    
    def test_lxml_returns_expected_element_value_from_unicode_xml_fragment(self):
        #setup
        xml = objectify.fromstring(u'<foo><baz name="Arthur">dcba</baz><bar>abcd\xe9</bar></foo>'.encode('utf-8'))
        #execute
        val = _lxml_xpath(xml, "/foo/bar", None)
        #assert
        self.assertEquals(u"abcd\xe9", val)
    
    def test_lxml_returns_expected_attribute_value(self):
        #setup
        xml = objectify.fromstring('<foo><baz name="Arthur">dcba</baz><bar>abcd</bar></foo>')
        #execute
        val = _lxml_xpath(xml, "/foo/baz/@name", None)
        #assert
        self.assertEquals("Arthur", val)

    def test_lxml_returns_expected_attribute_value_from_unicode_xml_fragment(self):
        #setup
        xml = objectify.fromstring(u'<foo><baz name="Arthur\xe9">dcba</baz><bar>abcd</bar></foo>'.encode('utf-8'))
        #execute
        val = _lxml_xpath(xml, "/foo/baz/@name", None)
        #assert
        self.assertEquals(u"Arthur\xe9", val)
    
if __name__=='__main__':
    unittest.main()