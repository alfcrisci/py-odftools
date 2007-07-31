# -*- coding: iso-8859-15 -*-

import os, sys

try:
    import xml.etree.cElementTree as ET
except ImportError:
    from elementtree.cElementTree import ElementTree as ET

from component import Component


# Exceptions for this module

class ReCompileError(Exception):
    """Thrown if regular expression cannot be compiled."""
    pass

class PathNotFoundError(Exception):
    """Thrown if a file reference contains a nonexistant path."""
    pass


# Main class

class Manifest(Component):
    """Manifest of all components comprising the document.""" 

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

