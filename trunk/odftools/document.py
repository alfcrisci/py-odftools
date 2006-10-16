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

	def __init__(self, 
				 mimetype='',	# Mimetype string
				 manifest='',	# Lists the contents of the ODF file
				 content='',	# Content data (the text)
				 styles='',		# Formatting data 
				 settings='',	# Use is specific to the application 
				 meta='',		# Metadata
				 **kwords		# Other files in META-INF
				 ): 
		self.mimetype = mimetype
		self.manifest = dom.parseString(manifest)
		self.content = dom.parseString(content)
		self.styles = dom.parseString(styles)
		self.settings = dom.parseString(settings)
		self.meta = dom.parseString(meta)
		#ENH: Handle **kwords
		# --- alternate route --- 
		# self.Components = {}

	def __del__(self):
		""" Unlink each DOM component """
		self.manifest.unlink()
		self.content.unlink()
		self.styles.unlink()
		self.settings.unlink()
		self.meta.unlink()


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
		textlist = []
		for node in self.content:
			if node.nodeType == node.TEXT_NODE:
				textlist.append(node.data)
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
		values["Title"] = title		# Title for the page, if applicable
		bodyList = []	# the lines to insert into the body of the document
		# Not implemented yet:
		metaList = [] 	# Meta tags for the header
		styleList = []	# Stylesheet elements

		# Extract the body of the HTML document
		for node in self.content:
			if node.nodeType == node.TEXT_NODE:
				htmllist.append("<p>%s</p>" % node.data)
		values["Body"] = "\n".join(htmllist)

		# Apply values to the HTML template
		f = open("template.html", 'r')
		htmlTemplate = f.read()
		f.close
		return htmlTemplate % values


#EOF
