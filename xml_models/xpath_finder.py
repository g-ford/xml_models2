from lxml import etree

import sys
if sys.version < '3':
    import codecs
    def unicode(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def unicode(x):
        return x


class MultipleNodesReturnedException(Exception):
    pass


def find_unique(xml_doc, expression, namespace=None):
    matches = xml_doc.xpath(expression)
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
    matches = xml.xpath(expression)
    return [etree.tostring(match) for match in matches]


def domify(xml):
    return etree.fromstring(xml)

