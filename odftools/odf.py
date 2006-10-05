#!/usr/bin/env python

""" odf.py

"""

import zipfile


# Map the names of the Zipped files to attributes of the Document object.
filenames = {"content.xml":content,
			 "styles.xml":style,
			 "meta.xml":meta,
			 "settings.xml":settings } # mimetype?

class WriteException: pass
class ReadException: pass


class odf:
    """ Provides a Pickle-like interface for reading and writing. """
    def __init__(self):
		pass

	def dump(self, obj, dst, mode=None):
        dst.write( OdfWriter.write(obj, mode) )
        return

    def dumps(self, obj, mode=None):
        dst = StringIO()
        self.dump(obj, dst, mode)
        return dst.getvalue()

    def load(self, src):
        return OdfReader.read(src)

    def loads(self, str):
        src = StringIO(str)
        return OdfReader.read(src)


class OdfWriter:
	""" Class for writing an ODF Document object to the output stream. """

	def __init__(self):
		pass

	def write(self, obj, dst)
		""" Writes each of obj's attributes to a Zip file named dst. """
		zf = ZipFile(dst, 'w')
		for filename, attr in filenames:
			f = open(filename, 'w')
			f.write(obj.__getattr__(attr)) # Check syntax
			zf.write(filename)
			f.close()
		zf.close()


class OdfReader:
	""" Class for reading an ODF Document object from the input stream. """

	def __init__(self):
		pass

	def read(self, src):
		""" Read the contents of each of the files in archive src into obj. """
		zf = ZipFile(src, 'r')
		obj = None
		for filename, attr in filenames:
			obj.__setattr__(attr) = zf.namelist(filename).read() # Check syntax
		zf.close()



#EOF
