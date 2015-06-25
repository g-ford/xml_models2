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
from xml.dom import minidom
import xpath

class MultipleNodesReturnedException(Exception):
    pass
    
lxml_available = False
try:
   from lxml import etree, objectify
   lxml_available = True
except:
    pass

def find_unique(xml, expression, namespace=None):
    if lxml_available:
        return _lxml_xpath(xml, expression, namespace)
    else:
        return _pydom_xpath(xml, expression, namespace)
    
def find_all(xml, expression, namespace=None):
    if lxml_available:
        return _lxml_xpath_all(xml, expression, namespace)
    else:
        return _pydom_xpath_all(xml, expression, namespace)
    
def _lxml_xpath(xml_doc, expression, namespace):
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
    
def _lxml_xpath_all(xml, expression, namespace):
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

def _pydom_xpath_all(xml, expression, namespace):
    nodelist = xpath.find(expression, xml, default_namespace=namespace)
    return [fragment.toxml() for fragment in nodelist]

def _pydom_xpath(xml, expression, namespace):
    nodelist = xpath.find(expression, xml, default_namespace=namespace)
    if len(nodelist) > 1:
        raise MultipleNodesReturnedException
    if len(nodelist) == 0:
        return None
    if nodelist[0].nodeType == minidom.Node.DOCUMENT_NODE:
        node = nodelist[0].firstChild.firstChild
    else:
        node = nodelist[0].firstChild
    if node == None:
        return None
    if node.nodeType == minidom.Node.TEXT_NODE:
        return node.nodeValue
    else:
        return None
            
def get_xpath(xpath, namespace):
    if namespace:
        xpath_list = xpath.split('/')
        xpath_with_ns = ""
        for element in xpath_list:
            if not element.startswith('@') and not element == '' :
                xpath_with_ns += "/x:" + element
            elif element == '':
                pass
            else:
                xpath_with_ns += "/" + element
        return xpath_with_ns
    else:
        return xpath

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