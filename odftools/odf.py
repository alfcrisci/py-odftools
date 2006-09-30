#!/usr/bin/env python

""" odf

"""


class odf:
    """ Provides a Pickle-like interface for reading and writing. """
    def __init__(self):
		pass

	def dump(self, obj, dst, mode=0):
        dst.write( OdfWriter(obj, mode) )
        return

    def dumps(self, obj, mode=None):
        dst = StringIO()
        self.dump(obj, dst, mode)
        return dst.getvalue()

    def load(self, src):
        return OdfReader(src)

    def loads(self, str):
        src = StringIO(str)
        return OdfReader(src)
        
        
class OdfWriter:
    pass

class OdfReader:
    pass


class WriteException: pass
class ReadException: pass


#EOF
