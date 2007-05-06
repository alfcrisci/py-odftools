# -*- coding: iso-8859-15 -*-

""" The document class -- object model and associated methods.

Contains the document in memory and is used as the intermediate step for 
conversions and transformations.

This implementation uses the ElementTree module to create and navigate the
object. This is built into Python 2.5 and available separately as a standalone
module.

"""

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


# The Document tree and associated methods

class Document:
    """The ODF document object."""
    # Map attribute names to file names
    file_map = {'mimetype': 'mimetype', 
                'manifest': 'META-INF/manifest.xml', 
                'content': 'content.xml', 
                'styles': 'styles.xml', 
                'meta': 'meta.xml',
                'settings': 'settings.xml'}

    def __init__(self,
            file='',       # Document file name
            mimetype='',   # Mimetype string
            manifest='',   # Lists the contents of the ODF file
            content='',    # Content data (the text)
            styles='',     # Formatting data
            meta='',       # Metadata
            settings='',   # Application-specific data
            additional={}, # Additional bundled files (e.g. images)
            file_dates={}  # File dates for all files and directories
            ):

        # Get all method parameters
        args = locals()

        # Process all Document files
        for key, filename in self.__class__.file_map.items():
            if key not in args or 0 == len(args[key]):
                setattr(self, key, '')
            elif not filename or '.xml' != filename[-4:]:
                setattr(self, key, args[key])
            else:
                try:
                    # Parse the XML string and set it as an ElementTree object
                    setattr(self, key, ET.XML(args[key])) 
                except Exception, e:
                    print >>sys.stderr, sysargs[key]
                    print >>sys.stderr, e

        self.additional = additional
        self.file_dates = file_dates

        if not hasattr(self, 'file'):
            self.file = None

    def __del__(self): # XXX is this still necessary?
        """Clean up.
        
        This was originally here to unlink each DOM component.
        
        """
        for key in self.__class__.file_map:
            attr = getattr(self, key)
            if not isinstance(attr, basestring):
                del attr

    # ---------------------------
    # Extract objects from the document

    def getComponentAsString(self, component_name, #pretty_printing=False,
                            encoding=None):
        """Return document component as Unicode string."""
        if component_name not in self.__class__.file_map:
            return ""
        filename = self.__class__.file_map[component_name]
        attr = getattr(self, component_name)
        if isinstance(attr, basestring):
            return attr
        #if pretty_printing:
        #    return attr.toprettyxml(encoding)
        return ET.tostring(attr, encoding=encoding)

    def getEmbeddedObjects(self, filter=None, ignore_case=False):
        """Return a dictionary of the objects embedded in the document.

        A more general form of getImages. By default, this should return
        all embedded objects; the list/dictionary can also be filtered
        for a certain type, e.g. image files.

        The filter currently supports UNIX glob patterns like "*a[bc]?.png"
        and/or correct regular expressions like ".*a[bc].\.png$".

        """
        # TODO: support other embedded objects
        search = get_search_for_filter(filter, ignore_case)
        return dict([(filename[9:], content)
                    for filename, content in self.additional.items()
                    if 'Pictures/' == filename[:9]
                    and search(filename[9:])])

    def getElementsByType(self, elementtype):
        """Extract all elements of a given type from the document.

        For example, formulas or code.

        """
        pass

    def getAuthor(self):
        """Return the author of this document if available."""
        author = ''
        if self.meta:
            for node in self.meta.getElementsByTagName("dc:creator"):
                if (node.firstChild.nodeType == node.TEXT_NODE) and node.firstChild.data:
                    author = node.firstChild.data
                    break

        return author

    def getExtension(self):
        """Return ODF extension for given mimetype."""
        return get_extension(self.mimetype)

    # ---------------------------
    # Convert the document to other formats

    def toXml(self, pretty_printing=False, encoding=None):
        """Return the content of the document as a XML Unicode string."""
        if pretty_printing:
            return self.content.toprettyxml(encoding)
        return self.content.toxml(encoding)

    def toText(self, skip_blank_lines=True):
        """Return the content of the document as a plain-text Unicode string."""
        textlist = (node.text for node in self.content.getiterator()
                    if not skip_blank_lines or node.text)
        return unicode(os.linesep).join(textlist)

    def toHtml(self, title="", encoding="utf-8"):
        """Return an UTF-8 encoded HTML representation of the document."""
        # TODO: 
        # First, convert to ET operations
        # Then,
        # - Scrape up meta tags and add to headnode
        #     '<meta http-equiv="content-type" content="text/html; charset=UTF-8">'
        #     '<meta type="Generator" content="python-odftools" />'
        # - Title for the page, if applicable
        # - Convert self.styles to CSS and add to headnode as a <style type="text/css"> element
        #     - see cssutils at the Python cheeseshop
        # - Fix the unit test
        #
        # ENH: 
        # - Support encodings other than UTF-8, and maybe Unicode
        # - Allow named elements
        # - A more natural way of doing the doctype declaration, if possible

        attrs_odf2html = {"style-name": "class"}
        tags_odf2html = { 
                "a": "a",
                "body": "body",
                "p": "p",
                "span": "span",
                "table": "table",
                "h": "h1",
                "table-row": "tr",
                "table-cell": "td",
                "image": "img",
                "list": "ol",
                "list-item": "li" }

        htmldoc = ET.Element("html")
        headnode = ET.SubElement(htmldoc, "head")
        titlenode = ET.SubElement(headnode, "title")
        titlenode.text = title
        # ENH: add meta etc. nodes to the head as needed

        docbody = self.content.find("office:body")
        if docbody:
            bodynode = translate_nodes(docbody, tags_odf2html, attrs_odf2html)
        else:
            bodynode = ET.SubElement(htmldoc, "body")

        doctypestr = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
        htmlstr = ET.tostring(htmldoc, encoding=encoding) # .split("\n", 1)[1] # XXX kill 1st line?
        return "\n".join((doctypestr, htmlstr))

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


# ----------------------------------------------------------------------------
# Global functions 


def get_extension(mimetype):
    """Return ODF extension for given mimetype."""
    # XXX -- why isn't this part of the Document class?
    # Would we really want to use this outside the ODF doc context?
    # If not, merge this into the Document method getExtension
    if mimetype.startswith(odf_prefix):
        _mimetype = mimetype[len(odf_prefix):]
        for extension, mimetype in odf_formats.items():
            if mimetype == _mimetype:
                return extension
    return ''


# Search / navigation

def get_search_for_filter(filter, ignore_case=False, limit_glob=True, none_value=True):
    """Return a search function for the given filter.

    Any filter not containing an escaped dot ("\.") and containing at least one
    "*", "?" or "." will be interpreted as glob.
    But in addition all globs still may contain all other regular expression
    sequences like [\d_-] or (home|job).

    Please note that you have to use " as a string separator on Windows command
    line. In addition, some regular expressions containing characters like the
    pipe symbol "|" must be enclosed by string separators.

    limit_glob adds ^ and $ modifiers to globs (default).
    none_value specifies the return value if filter is empty.

    """
    if filter:
        import re, sre_constants
        try:
            # filter = re.escape(filter)
            if os.sep == '\\':
                filter = filter.replace('/', '\\\\')

            if filter[-1] == '\\' and (len(filter) == 1 or filter[-2] != '\\'):
                filter += '\\'

            if is_glob(filter):
                s = filter.replace('.', r'\.').replace('*', '.*').replace('?', '.')
                if limit_glob and filter[0] != '*':
                    s = '^' + s
                if limit_glob and filter[-1] != '*':
                    s += '$'

                filter = s
            if ignore_case:
                find = re.compile(filter, re.IGNORECASE).search
            else:
                find = re.compile(filter).search
            search = lambda x: find(x)
        except (sre_constants.error, TypeError), v:
            # print >>sys.stderr, 'Warning: could not compile regular expression:', v
            # search = lambda x: False
            raise ReCompileError(v)
    else:
        search = lambda x: none_value

    return search


def is_glob(filter):
    """Return True if filter contains a glob expression, False otherwise."""
    return not r'\.' in filter and [c for c in '*[]?.' if c in filter]


# Data structure navigation

# http://www-128.ibm.com/developerworks/library/x-tipgenr.html
def doc_order_iter(node):
    """Iterates over each node in document order, returning each in turn."""
    # Document order returns the current node, then each of its children in turn
    yield node
    for child in node.childNodes:
        # Create a generator for each child, over which to iterate
        for cn in doc_order_iter(child):
            yield cn
    return


def translate_nodes(innode, tag_map, attr_map):
    """Converts an ElementTree with one set of tags into another.

    Starting with the root of each tree, recurses through each child
    of innode, converts tags and attributes according to the given
    mappings, and returns a tree of the resulting new nodes.

    Returns a node (tree) called outnode.

    """
 
    # Validate innode lil bit
    try:
        if innode.tag is ET.Comment:
            return innode
        elif innode.tag is ET.ProcessingInstruction:
            # Not sure how to the handle this, so skip it
            pass
    except AttributeError:
        # Assume innode was garbage. Return it as a comment and keep going.
        return ET.Comment(str(innode))

    # Rename tags according to tag_map
    try:
        tag = tag_map[innode.tag]
    except KeyError:
        tag = "p" # By default, handle unexpected nodes as text -- is this crazy?

    outnode = ET.Element(tag)

    # Rename attributes according to attr_map
    for attr in innode.attrib:
        outnode.set(attr_map[attr], innode.get(attr))

    # Translate any children the same way
    if len(innode):
        for cnode in list(innode):
            newnode = translate_nodes(cnode, tag_map, attr_map)
            outnode.append(newnode)


    return outnode


# vim: et sts=4 sw=4
#EOF
