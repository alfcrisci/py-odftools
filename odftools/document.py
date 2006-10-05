#!/usr/bin/env python

""" document

The document object, to be used as the intermediate step for all operations
"""

from xml import sax, dom

class Document:
	""" The ODF document object.

	Three potential approaches:
	1. sax -- store the attributes as strings, parse as needed.
	2. dom -- parse into trees on initialization
	3. pyxml -- outside library, not sure what they have going on
	"""

	def __init__(self, 
				 content='', 
				 styles='', 
				 meta='', 
				 settings='', 
				 mimetype=''):
		self.content = content
		self.styles = styles
		self.meta = meta
		self.settings = settings
		self.mimetype = mimetype


#EOF
