# -*- coding: iso-8859-15 -*-

"""Contents of the document: text and data."""

import os, sys
import re
import sre_constants

try:
    import xml.etree.cElementTree as ET
except ImportError:
    from elementtree.cElementTree import ElementTree as ET


# Exceptions for this module

class ReCompileError(Exception):
    """Thrown if regular expression cannot be compiled."""
    pass

class PathNotFoundError(Exception):
    """Thrown if a file reference contains a nonexistant path."""
    pass

# Main class

class Content(object):

    def __init__(self, text):
        self.root = ET.fromstring(text)

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

        try:
            _replace = re.compile(search).sub
            search = lambda x, y: find(x, y)
        except (sre_constants.error, TypeError), v:
            print >>sys.stderr, 'Warning: could not compile regular expression:', v
            return 0

        count = 0
        for node in self.root.getiterator():
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

# Classes for content node types

class _Table(object):
    """Table, embedded in a document or standalone as a spreadsheet."""

    def __init__(self, parent):
        self.parent = parent


class _Chart(object):
    """Chart, embedded in a spreadsheet or standalone."""

    def __init__(self, parent):
        self.parent = parent


