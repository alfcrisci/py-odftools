#!/usr/bin/env python

""" odf.py


The full OASIS OpenDocument specification can be found here:
http://www.oasis-open.org/specs/index.php#opendocumentv1.0

Mad love to Bob Sutor (www.sutor.com). Bob's Dr. ODF project/blog series
suggests the following features as examples:

* Take an ODF document and extract any images/objects embedded in it.
* Take an ODF document and throw away all formatting except the basic heading 
	and paragraph structure, printing what’s left on the screen. (to text)
* Iterate over a directory of ODF files and print how many of them were authored
	by a given person. (list file ownership in a friendly format)
* Take an ODF word processing document and convert it to HTML. (Don’t forget 
	the images and tables!)
* Extract all the elements of a given type (e.g. formulas, code) from an ODF
	document.

More ideas:
* Clean up styles: If two or more styles have the same attributes, pick one 
	name for all of them and delete the other styles.
* Determine document type (in case of wrong filename extension)
*




"""

import zipfile
from cStringIO import StringIO


class WriteException: pass
class ReadException: pass


# Provides a Pickle-like interface for reading and writing. 

def Load(src):
	return _read(src)

def Loads(str):
	src = StringIO(str)
	return _read(src)

def Dump(obj, dst):
	dst.write(_write(obj))
	return

def Dumps(obj):
	dst = StringIO()
	dst.write(_write(obj))
	return dst.getvalue()


# The business end of this ---------------------------------------------------

# Map the names of the Zipped files to attributes of the Document object.
g_Filenames = {"content.xml":content,
			 "styles.xml":style,
			 "meta.xml":meta,
			 "settings.xml":settings } # mimetype?

def _read(src):
	""" Reads the contents of each of the files in archive src into obj. """
	zf = ZipFile(src, 'r')
	obj = None
	for filename, component in g_Filenames:
		obj.__setattr__(component, zf.read(filename))
	zf.close()
	return obj
	

def _write(obj, dst):
	""" Writes each of obj's attributes to a Zip file named dst.

	NB: Pardon the mess, this isn't going to be implemented till later.
	"""
	#out_stream = obj.toFile() # TODO: implement
	zf = ZipFile(dst, 'w')
	#zf.write(filename) # takes the name or an existing file
	out_stream.close()
	zf.close()


# --- Basic test script -------------------------------------------------------

if __name__ == "__main__":
	
	import os
	
	for filename in os.listdir(os.getcwd()):
		if filename.rsplit('.').pop() in ['odt']:
			doc = Load(open(filename, 'r'))
			print doc.getText()


#EOF
