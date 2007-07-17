# -*- coding: iso-8859-15 -*-

"""Style definitions component of the document."""

import os, sys

try:
    import xml.etree.cElementTree as ET
except ImportError:
    from elementtree.cElementTree import ElementTree as ET



class Styles(object):

    def __init__(self, text):
        self.root = ET.fromstring(text)

    # Convert the document to other formats

    def to_xml(self, pretty_printing=False, encoding=None):
        """Return the content of the document as a XML Unicode string."""
        if pretty_printing:
            return self.root.toprettyxml(encoding)
        return self.content.toxml(encoding)


class _Style(object):

    def __init__(style, parent, xml):
        self.parent = parent
        node = ET.fromstring(xml) # TODO: take care of namespaces
        self.node = parent.append(node)
        # TODO: define the default style, if not already in xml


