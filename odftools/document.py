#!/usr/bin/env python

""" document

The document object, for containing the document in memory and to be used as 
the intermediate step for all operations.

This implementation relies on minidom for handling the object. It may later
become prudent to use the bulkier xml.dom or pyxml, but for now, this
should do.
"""

from xml.dom.minidom import *

class Document:
	""" The ODF document object. """

	def __init__(self, 
				 mimetype='',	# Mimetype string
				 manifest=""	# Lists the contents of the ODF file
				 content='',	# Content data (the text)
				 styles='',		# Formatting data 
				 settings='',	# Use is specific to the application 
				 meta='',		# Metadata
				 # Consider **kwords for META-INF
				 ): 
		self.mimetype = mimetype
		self.manifest = xml.dom.minidom.parseString(manifest)
		self.content = xml.dom.minidom.parseString(content)
		self.styles = xml.dom.minidom.parseString(styles)
		self.settings = xml.dom.minidom.parseString(settings)
		self.meta = xml.dom.minidom.parseString(meta)
		# --- alternate route --- 
		# self.Components = {}

	def __del__(self):
		# unlink each DOM component
		# for attr in []:
		#	self.__attr__(attr).unlink()
		self.manifest.unlink()
		self.content.unlink()
		self.styles.unlink()
		self.settings.unlink()
		self.meta.unlink()
		

	def getText(self, nodelist):
		rc = []
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc.append(node.data + '\n')
		return "".join(rc)

	

#EOF
