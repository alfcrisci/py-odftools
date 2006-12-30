#!/usr/bin/env python

"""document

The document object, for containing the document in memory and to be used as
the intermediate step for all operations.

This implementation relies on minidom for handling the object. It may later
make sense to use the bulkier xml.dom or pyxml, but for now, this
should do.
"""

import os
import xml.dom.minidom as dom

# Prefix values with "application/vnd.oasis.opendocument." to get MIME types
odf_formats = {'odt':'text', 'ods':'spreadsheet', 'odp':'presentation',
               'odg':'graphics', 'odc':'chart', 'odf':'formula', 'odi':'image',
               'odm':'text-master', 'ott':'text-template',
               'ots':'spreadsheet-template', 'otp':'presentation-template',
               'otg':'graphics-template'}

class ReCompileError(Exception): pass


class Document:
  """The ODF document object."""

  # map attribute names to file names
  files={'mimetype': 'mimetype', 'content': 'content.xml', 'manifest':
         'META-INF/manifest.xml', 'styles': 'styles.xml', 'settings':
         'settings.xml', 'meta': 'meta.xml'}

  def __init__(self,
         file='',       # Document file name
         mimetype='',   # Mimetype string
         content='',    # Content data (the text)
         manifest='',   # Lists the contents of the ODF file
         styles='',     # Formatting data
         settings='',   # Use is specific to the application
         meta='',       # Metadata
         additional={}, # additional files (i.e. images)
         **kwords       # Other files in META-INF
         ):

    # Get all method parameters
    args = locals()

    # Process all Document files
    for key, filename in self.__class__.files.items():
      if key not in args or 0 == len(args[key]):
        setattr(self, key, '')
      elif not filename or '.xml' != filename[-4:]:
        setattr(self, key, args[key])
      else:
        try:
          setattr(self, key, dom.parseString(args[key]))
        except Exception, e:
          print args[key]
          print e

    # Store additional files
    self.additional = {}
    for filename, content in args["additional"].items():
        self.additional[filename] = content

    if not hasattr(self, 'file'):
      self.file = None

    #ENH: Handle **kwords
    # --- alternate route ---
    # self.Components = {}

  def __del__(self):
    """Unlink each DOM component."""
    for key in self.__class__.files:
      attr = getattr(self, key)
      if not isinstance(attr, basestring):
        attr.unlink()


  # Extract objects from the document --------------------------------------

  def getComponentAsString(self, component_name, pretty_printing=False):
    if component_name not in self.__class__.files:
      return ""
    filename = self.__class__.files[component_name]
    attr = getattr(self, component_name)
    if isinstance(attr, basestring):
      return attr
    if pretty_printing:
      return attr.toprettyxml('utf-8')
    return attr.toxml('utf-8')


  def getEmbeddedObjects(self, filter=None):
    """Return a dictionary of the objects embedded in the document.

    A more general form of getImages. By default, this should return
    all embedded objects; the list/dictionary can also be filtered
    for a certain type, e.g. image files.

    The filter currently supports UNIX glob patterns like "*abc?.png"
    and correct regular expressions like ".*abc.\.png".
    """

    # TODO: support other embedded objects
    search = get_search_for_filter(filter)
    return dict([(filename[9:], content) for filename, content in self.additional.items() if 'Pictures/' == filename[:9] and search(filename[9:])])


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


  # Convert the document to other formats ---------------------------------

  def toXml(self, pretty_printing=False):
    """Return the content of the document as a XML string."""
    if pretty_printing:
      return self.content.toprettyxml('utf-8')
    return self.content.toxml('utf-8')

  def toText(self, skip_blank_lines=True):
    """Return the content of the document as a plain-text string."""
    textlist = [node.data for node in doc_order_iter(self.content) if node.nodeType == node.TEXT_NODE and (not skip_blank_lines or 0 != len(node.data.strip()))]
    return "\n".join(textlist)

  def toHtml(self, title=""):
    """Return an HTML representation of the document.

    The current version of this function is essentially the same as toText.

    The next version should:
    - Create a stylesheet in the header
    - Apply corresponding style classes to each node

    After that, this function should also handle:
    - hyperlinks
    - images
    - tables
    """
    values = {}
    values["title"] = title   # Title for the page, if applicable
    bodyList = [] # the lines to insert into the body of the document
    # Not implemented yet:
    metaList = []   # Meta tags for the header
    styleList = []  # Stylesheet elements

    # Extract the body of the HTML document
    htmllist = ["<p>%s</p>" % node.data for node in doc_order_iter(self.content) if node.nodeType == node.TEXT_NODE]
    values["body"] = "\n".join(htmllist)

    values["meta"] = "" # TODO
    values["styles"] = "" # TODO

    # Apply values to the HTML template
    f = open(os.path.dirname(__file__) + "/template.html", 'r')
    htmlTemplate = f.read()
    f.close()
    return htmlTemplate % values

  def replace(self, search, replace):
    """Replace all occurences of search in content by replace.
    Regular expressions are fully supported for search and replace."""

    if not search:
        return 0
    import re, sre_constants
    try:
        _replace = re.compile(search).sub
        search = lambda x, y: find(x, y)

    except (sre_constants.error, TypeError), v:
        print 'Warning: could not compile regular expression:', v
        return 0
    count = 0
    for node in doc_order_iter(self.content):
        if node.nodeType == node.TEXT_NODE and node.data:
            try:
                replaced = _replace(replace, node.data)
                if replaced != node.data:
                  node.data = replaced
                  count += 1
            except (sre_constants.error, TypeError), v:
                print 'Warning: could not compile regular expression:', v
                return 0
    return count


def get_search_for_filter(filter):
    """Return a search function for the given filter.
    Any filter not containing an escaped dot ("\.") and containing at least one "*", "?" or "." will be interpreted as glob.
    But in addition all globs still may contain all other regular expression sequences like [\d_-] or (home|job).
    Please note that you have to use " as a string separator on Windows command line.
    In addition some regular expressions containing characters like the pipe symbol "|" must be enclosed by string separators."""

    if filter:
        import re, sre_constants
        try:
            if not r'\.' in filter and [c for c in '*?.' if c in filter]:
                s = filter.replace('.', r'\.').replace('*', '.*').replace('?', '.')
                if filter[0] != '*':
                    s = '^' + s
                if filter[-1] != '*':
                    s += '$'

                find = re.compile(s).search
            else:
                find = re.compile(filter).search
            search = lambda x: find(x)
        except (sre_constants.error, TypeError), v:
            # print 'Warning: could not compile regular expression:', v
            # search = lambda x: False
            raise ReCompileError(v)
    else:
        search = lambda x: True

    return search


def list_directory(directory, filter=None, must_be_directory=False, recurse=False):
    """Scan a directory for ODF files."""

    if must_be_directory and not os.path.isdir(directory):
        return []

    if not directory:
        directory = '.'
        prefix = ''
    else:
        prefix = directory + os.path.sep

    if os.path.isfile(prefix + filter):
        return [prefix + filter]

    if not os.path.isdir(directory):
        return []

    search_user = get_search_for_filter(filter)
    odf_extensions = r".*\.(?:" + "|".join(odf_formats.keys()) + ")$"
    search_odf = get_search_for_filter(odf_extensions)

    files = [prefix + file for file in os.listdir(directory)
             if search_user(file) and search_odf(file)]

    return files


def get_path_and_filter(directory):
    """Return tuple containing the validated path and file filter."""

    path = ''
    filter = ''
    if os.path.isdir(directory):
        path = directory
        if path[-1] in r"\/":
            path = path[:-1]
    else:
        import re
        search_path_separator = re.compile(r'[/\\]')
        splitted = search_path_separator.split(directory, 1)
        # TODO: allow directory globbing "test*/*.odt"
        if len(splitted) == 2 and os.path.isdir(splitted[0]):
            path += splitted[0]
            splitted = search_path_separator.split(splitted[1], 1)
            check_path = path + os.path.sep + splitted[0]
            while os.path.isdir(check_path):
                path = check_path
                splitted = search_path_separator.split(splitted[1], 1)
                check_path = path + os.path.sep + splitted[0]
            filter = directory[len(path)+1 :]

        else:
            filter = directory

    return (path, filter)


# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560
def unique(seq):
  """Return a unique list of the sequence elements."""

  d = {}
  return [d.setdefault(e,e) for e in seq if e not in d]


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


#EOF
