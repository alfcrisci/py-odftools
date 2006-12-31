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

class ReCompileError(Exception):
  """Thrown if regular expression is not compilable."""
  pass

class PathNotFoundError(Exception):
  """Thrown if a file reference contains a non-existing path."""
  pass


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

  def getComponentAsString(self, component_name, pretty_printing=False,
                           encoding=None):
    """Return document component as Unicode string."""
    if component_name not in self.__class__.files:
      return ""
    filename = self.__class__.files[component_name]
    attr = getattr(self, component_name)
    if isinstance(attr, basestring):
      return attr
    if pretty_printing:
      return attr.toprettyxml(encoding)
    return attr.toxml(encoding)


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

  def toXml(self, pretty_printing=False, encoding=None):
    """Return the content of the document as a XML Unicode string."""
    if pretty_printing:
      return self.content.toprettyxml(encoding)
    return self.content.toxml(encoding)

  def toText(self, skip_blank_lines=True):
    """Return the content of the document as a plain-text Unicode string."""
    textlist = [node.data for node in doc_order_iter(self.content) if node.nodeType == node.TEXT_NODE and (not skip_blank_lines or 0 != len(node.data.strip()))]
    return u"\n".join(textlist)

  def toHtml(self, title=""): # , encoding=None
    """Return an UTF-8 encoded HTML representation of the document.

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

    import codecs
    # TODO: Support other encodings than UTF-8, and maybe Unicode
    encoding = 'utf-8'
    values["title"] = unicode(title).encode(encoding) # Title for the page, if applicable
    bodyList = [] # the lines to insert into the body of the document
    # Not implemented yet:
    metaList = []   # Meta tags for the header
    styleList = []  # Stylesheet elements

    # Extract the body of the HTML document
    htmllist = ["<p>%s</p>" % node.data.encode(encoding) for node in doc_order_iter(self.content) if node.nodeType == node.TEXT_NODE]
    values["body"] = "\n".join(htmllist)

    values["meta"] = "" # TODO
    values["styles"] = "" # TODO

    # Apply values to the HTML template
    f = codecs.open(os.path.dirname(__file__) + "/template.html", 'r', encoding, 'xmlcharrefreplace')
    htmlTemplate = f.read()
    f.close()

    htmlTemplate = htmlTemplate.encode(encoding)

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

    directory = get_win_root_directory(directory)
    if must_be_directory and not os.path.isdir(directory):
        return []

    prefix = u''
    if not directory:
        directory = '.'
    else:
        prefix += directory
        if prefix[-1] not in "/\\":
            prefix += os.path.sep

    if os.path.isfile(prefix + filter):
        return [prefix + filter]

    if not os.path.isdir(directory):
        return []

    search_user = get_search_for_filter(filter)
    odf_extensions = r".*\.(?:" + "|".join(odf_formats.keys()) + ")$"
    search_odf = get_search_for_filter(odf_extensions)

    files = [prefix + file for file in os.listdir(unicode(directory))
             if search_user(file) and search_odf(file)]

    return files


def get_path_and_filter(directory, test_existence=True):
    """Return tuple containing the validated path and file filter."""

    path = ''
    filter = ''
    if test_existence and os.path.isdir(directory):
        path = directory
        if path[-1] in r"\/":
            path = path[:-1]
    else:
        import re
        search_path_separator = re.compile(r'[/\\]')
        splitted = search_path_separator.split(directory, 1)
        if directory[0] in r"\/":
            first_directory = os.path.sep
        else:
            first_directory = get_win_root_directory(splitted[0])

        # TODO: allow directory globbing "test*/*.odt"
        if len(splitted) == 2:
            if test_existence and not os.path.isdir(first_directory):
                raise PathNotFoundError('Path does not exist: ' + first_directory)
            if first_directory != os.path.sep:
                path += splitted[0]
            splitted = search_path_separator.split(splitted[1], 1)
            check_path = path + os.path.sep + splitted[0]
            while len(splitted) == 2:
                if test_existence and not os.path.isdir(check_path):
                    raise PathNotFoundError('Path does not exist: ' + check_path)
                path = check_path
                splitted = search_path_separator.split(splitted[1], 1)
                check_path = path + os.path.sep + splitted[0]
            if len(path) == 0 and first_directory == os.path.sep:
                path = os.path.sep
                filter = directory[1 :]
            else:
                filter = directory[len(path)+1 :]

        else:
            filter = directory

    return (path, filter)


def get_win_root_directory(directory):
  """Return windows root directory with path separator, otherwise unchanged."""
  if len(directory) == 2 and directory[1] == ':':
      return directory + os.path.sep
  return directory


# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560
def unique(seq):
  """Return a unique list of the sequence elements."""

  d = {}
  return [d.setdefault(e,e) for e in seq if e not in d]


def list_intersect(needles, haystack):
  """Return a list of all needles which are in haystack list.

  Result is like [e for e in output.keys() if e in ['xml','html']]."""
  return [e for e in haystack if e in needles]


def get_encoding(file):
  """Return the current encoding of the given file."""
  # TODO: support sys.stdout
  encoding = getattr(file, "encoding", None)
  if not encoding:
    import sys
    encoding = sys.getdefaultencoding()
  return encoding


def print_unicode(outfile, output, encoding=None, output_encoding=None):
  """Print output to stdout and tries different encodings if necessary."""
  import sys
  try:
    if output_encoding:
      output = output.decode(output_encoding)
  except UnicodeError, e:
    pass

  try:
    print >>outfile, output
  except UnicodeError, e:
    try:
      # output.encode('latin_1')
      import codecs
      outfile = codecs.getwriter(encoding)(outfile)
      print >>outfile, output
    except UnicodeError, e:
      raise


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
