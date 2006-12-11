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
  """ The ODF document object. """
  keys=['mimetype', 'content', 'manifest', 'styles', 'settings', 'meta']

  def __init__(self,
         mimetype='', # Mimetype string
         content='',  # Content data (the text)
         manifest='', # Lists the contents of the ODF file
         styles='',   # Formatting data
         settings='', # Use is specific to the application
         meta='',   # Metadata
         **kwords   # Other files in META-INF
         ):
    args = locals()
    for key in self.__class__.keys:
      if key not in args or 0 == len(args[key]):
        setattr(self, key, '')
      elif 'mimetype' == key:
        setattr(self, key, args[key])
      else:
        setattr(self, key, dom.parseString(args[key]))
    #ENH: Handle **kwords
    # --- alternate route ---
    # self.Components = {}

  def __del__(self):
    """ Unlink each DOM component """
    for key in self.__class__.keys:
      attr = getattr(self, key)
      if str != type(attr):
        attr.unlink()


  # Extract objects from the document --------------------------------------

  def getComponentAsString(self, component_name):
    nodelist = self.__getattr__(component_name)
    return nodelist.toprettyxml()


  def getEmbeddedObjects(self, filter=None):
    """ Return a dictionary of the objects embedded in the document.

    A more general form of getImages. By default, this should return
    all embedded objects; the list/dictionary can also be filtered
    for a certain type, e.g. image files.
    """
    pass

  def getElementsByType(self, elementtype):
    """ Extract all elements of a given type from the document.

    For example, formulas or code.
    """
    pass

  # Convert the document to other formats ---------------------------------

  def toText(self):
    """ Returns the content of the document as a plain-text string. """
    textlist = [node.data for node in doc_order_iter(self.content) if node.nodeType == node.TEXT_NODE]
    return "\n".join(textlist)


  def toHTML(self, title=""):
    """ Returns an HTML representation of the document.

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
