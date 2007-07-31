# -*- coding: iso-8859-15 -*-

import os, sys

try:
    import xml.etree.cElementTree as ET
except ImportError:
    from elementtree.cElementTree import ElementTree as ET

from component import Component


class Styles(Component):
    """Style definitions component of the document."""
    pass


class _Style(object):

    def __init__(style, parent, xml):
        self.parent = parent
        node = ET.fromstring(xml) # TODO: take care of namespaces
        self.node = parent.append(node)
        # TODO: define the default style, if not already in xml


