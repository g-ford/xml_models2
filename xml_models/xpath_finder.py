from lxml import etree

import sys

if sys.version < '3':
    def unicode(string):
        """
        Fake unicode function
        """
        import codecs
        if not string:
            return
        return codecs.unicode_escape_decode(string)[0]
else:
    def unicode(string):
        """
        Fake unicode function
        """
        return string


class MultipleNodesReturnedException(Exception):
    """
    An exception for when more than one node is returned when only one was expected.
    """
    pass


def find_unique(xml_doc, expression, namespace=None):
    """
    Find a single value or node in ``xml_doc`` matching ``expression``

    :param xml_doc:
    :param expression: xpath expression
    :param namespace: not used yet
    :return: the matching node or string
    :raises MultipleNodesReturnedException: if the xpath expression matches more than one result
    """
    matches = xml_doc.xpath(expression)
    if len(matches) == 1:
        matched = matches[0]

        if not matched:
            return unicode(matched.text)

        if hasattr(matched, 'text'):
            return unicode(matched.text).strip()

        return unicode(matched).strip()

    if len(matches) > 1:
        raise MultipleNodesReturnedException


def find_all(xml, expression, namespace):
    """
    Find all matching values or nodes in ``xml`` that match ``expression``

    :param xml:
    :param expression: xpath expression
    :param namespace: not used yet
    :return: a list of matching values or nodes
    """
    matches = xml.xpath(expression)
    return [etree.tostring(match) for match in matches]


def domify(xml):
    """
    Create a tree representation of XML

    :param xml:
    :return: etree
    """
    return etree.fromstring(xml)

