#!/usr/bin/env python

""" document

The document object, for containing the document in memory and to be used as
the intermediate step for all operations.

This implementation relies on minidom for handling the object. It may later
make sense to use the bulkier xml.dom or pyxml, but for now, this
should do.
"""

import xml.dom.minidom as dom


class Document:
  """ The ODF document object."""

  # map attribute names to file names
  files={'mimetype': 'mimetype', 'content': 'content.xml', 'manifest':
         'META-INF/manifest.xml', 'styles': 'styles.xml', 'settings':
         'settings.xml', 'meta': 'meta.xml'}

  def __init__(self,
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

    #ENH: Handle **kwords
    # --- alternate route ---
    # self.Components = {}

  def __del__(self):
    """ Unlink each DOM component """
    for key in self.__class__.files:
      attr = getattr(self, key)
      if str != type(attr):
        attr.unlink()


  # Extract objects from the document --------------------------------------

  def getComponentAsString(self, component_name, pretty_printing=False):
    if component_name not in self.__class__.files:
      return ""
    filename = self.__class__.files[component_name]
    attr = getattr(self, component_name)
    if str == type(attr):
      return attr
    if pretty_printing:
      return attr.toprettyxml('utf-8')
    return attr.toxml('utf-8')


  def getEmbeddedObjects(self, filter=None):
    """ Return a dictionary of the objects embedded in the document.

    A more general form of getImages. By default, this should return
    all embedded objects; the list/dictionary can also be filtered
    for a certain type, e.g. image files.

    The filter currently supports UNIX glob patterns like "*abc?.png"
    and correct regular expressions like ".*abc.\.png".
    """

    # TODO: support other embedded objects
    if filter:
      import re, sre_constants
      try:
        match = re.search(r'^(.*[^\\])\.(\w+)', filter)
        if match:
          match = match.groups()
          s = match[0].replace('*', '.*').replace('?', '.') + '\\.' + match[1]
          print s
          find = re.compile(s).search
        else:
          find = re.compile(filter).search
        search = lambda x: find(x)
      except (sre_constants.error, TypeError), v:
        print 'Warning: could not compile regular expression:', v
        search = lambda x: False
    else:
      search = lambda x: True
    return dict([(filename[9:], content) for filename, content in self.additional.items() if 'Pictures/' == filename[:9] and search(filename[9:])])


  def getElementsByType(self, elementtype):
    """ Extract all elements of a given type from the document.

    For example, formulas or code.
    """
    pass


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

  def toHTML(self, title=""):
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
    f = open("template.html", 'r')
    htmlTemplate = f.read()
    f.close()
    return htmlTemplate % values

  def replace(self, search, replace):
    """Replace all occurences of search in content by replace.
    Regular expressions are supported."""

    if not search:
      return
    import re, sre_constants
    try:
      _replace = re.compile(search).sub
      search = lambda x, y: find(x, y)

    except (sre_constants.error, TypeError), v:
      print 'Warning: could not compile regular expression:', v
      return
    for node in doc_order_iter(self.content):
      if node.nodeType == node.TEXT_NODE and node.data:
        try:
          node.data = _replace(replace, node.data)
        except (sre_constants.error, TypeError), v:
          print 'Warning: could not compile regular expression:', v
          return



# http://www-128.ibm.com/developerworks/library/x-tipgenr.html
def doc_order_iter(node):
    """
    Iterates over each node in document order,
    returning each in turn
    """
    #Document order returns the current node,
    #then each of its children in turn
    yield node
    for child in node.childNodes:
        #Create a generator for each child,
        #Over which to iterate
        for cn in doc_order_iter(child):
            yield cn
    return


#EOF
