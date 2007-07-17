# -*- coding: iso-8859-15 -*-

"""Manifest of all components comprising the document.""" 

import os, sys

try:
    import xml.etree.cElementTree as ET
except ImportError:
    from elementtree.cElementTree import ElementTree as ET


# Prefix values with "application/vnd.oasis.opendocument." to get MIME types

odf_formats = {'odt':'text', 'ods':'spreadsheet', 'odp':'presentation',
               'odg':'graphics', 'odc':'chart', 'odf':'formula', 'odi':'image',
               'odm':'text-master', 'ott':'text-template',
               'ots':'spreadsheet-template', 'otp':'presentation-template',
               'otg':'graphics-template'}

odf_prefix = "application/vnd.oasis.opendocument."


# Exceptions for this module

class ReCompileError(Exception):
    """Thrown if regular expression cannot be compiled."""
    pass

class PathNotFoundError(Exception):
    """Thrown if a file reference contains a nonexistant path."""
    pass

# Main class

class Manifest(object):

    def __init__(self, text):
        self.root = ET.fromstring(text)


# The Document tree and associated methods


    # Convert the document to other formats

    def to_xml(self, pretty_printing=False, encoding=None):
        """Return the content of the document as a XML Unicode string."""
        if pretty_printing:
            return self.root.toprettyxml(encoding)
        return self.root.toxml(encoding)

    def to_text(self, skip_blank_lines=True):
        """Return the content of the document as a plain-text Unicode string."""
        textlist = (node.text for node in self.root.getiterator()
                    if not skip_blank_lines or node.text)
        return unicode(os.linesep).join(textlist)

    # Operations

    def replace(self, search, replace):
        """Replace all occurences of search in content by replace.

        Regular expressions are fully supported for search and replace.

        Returns the number of replacements made.

        """
        if not search:
            return 0

        import re, sre_constants

        try:
            _replace = re.compile(search).sub
            search = lambda x, y: find(x, y)
        except (sre_constants.error, TypeError), v:
            print >>sys.stderr, 'Warning: could not compile regular expression:', v
            return 0

        count = 0
        for node in self.content.getiterator():
            if node.text:
                try:
                    replaced = _replace(replace, node.text)
                    if replaced != node.text:
                        node.text = replaced
                        count += 1
                except (sre_constants.error, TypeError), v:
                    print >>sys.stderr, 'Warning: could not compile regular expression:', v
                    return 0
        return count

