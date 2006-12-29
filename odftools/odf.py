#!/usr/bin/env python

""" odf.py

These utilities will attempt to cover the lightweight portions of Rob Weir's
proposal for an OpenDocument Developer's Kit:
http://opendocument.xml.org/node/154

The full OASIS OpenDocument specification can be found here:
http://www.oasis-open.org/specs/index.php#opendocumentv1.0


Bob Sutor's Dr. ODF project/blog series (http://www.sutor.com)
suggests the following features as examples:
- Take an ODF document and throw away all formatting except the basic heading
    and paragraph structure, printing what's left on the screen. [toText]
- Take an ODF word processing document and convert it to HTML. (Don't forget
    the images and tables!) [toHTML]
- Extract all the elements of a given type (e.g. formulas, code) from an ODF
    document. [getElementsByType]
- Take an ODF document and extract any images/objects embedded in it.
    [getEmbeddedObjects]
- Iterate over a directory of ODF files and print how many of them were
    authored by a given person. (list file ownership in a friendly format)

More ideas:
- Determine document type (in case of wrong filename extension)
- Clean up styles: If two or more styles have the same attributes, pick one
  name for all of them and delete the other styles.
- Diff -- mad useful. In the distant future, it may be possible to re-implement
  "track changes" as a diff patch to be included in the ODF file.
- Templating system -- e.g. set up an interface for generating new documents
  with a predetermined look-and-feel, including headers, footers etc.
  Also have an interface for generating reports using this system
"""

import os
import zipfile
from cStringIO import StringIO

from document import *

class WriteError(Exception): pass
class ReadError(Exception): pass


# -----------------------------------------------------------------------------
# Provide a Pickle-like interface for reading and writing.
def load(src):
    """Return a Document object representing the contents of the OpenDocument file src."""
    zf = zipfile.ZipFile(src, 'r')
    names = zf.namelist()
    obj_dict = {}
    obj_dict["additional"] = {}
    if str == type(src) and len(src) < 1000 and os.path.isfile(src):
      obj_dict["file"] = src
    inverted=dict([(v,k) for k,v in Document.files.items()])
    for filename in names:
        # If the Zip entry is a special ODF file, store it with it's own attribute name
        if filename in inverted:
            obj_dict[inverted[filename]] = zf.read(filename)
        else:
            obj_dict["additional"][filename] = zf.read(filename)
    zf.close()
    obj = Document(**obj_dict)
    return obj


def dump(doc, dst):
    """Write the ODF attributes of the document a Zip file named dst."""

    zf = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)

    # Zip document attributes
    for key, filename in Document.files.items():
        if filename:
            zf.writestr(filename, doc.getComponentAsString(key))

    # Zip additional files
    for filename, content in doc.additional.items():
        zf.writestr(filename, content)

    zf.close()


def loads(str):
    src = StringIO(str)
    obj = load(src)
    src.close()
    return obj

def dumps(doc):
    dst = StringIO()
    dump(doc, dst)
    str = dst.getvalue()
    dst.close()
    return str


# -----------------------------------------------------------------------------
# File format conversions

def OdfToText(filename, skip_blank_lines=True):
  obj = load(filename)
  return obj.toText(skip_blank_lines)

def OdfToHTML(filename, title=''):
  obj = load(filename)
  return obj.toHTML(title)

def OdfToSqlite(filename):
  """Return SQLite binary string of the zipped OpenDocument file."""
  try:
      from sqlite3 import dbapi2 as sqlite    # Python25
  except ImportError:
      from pysqlite2 import dbapi2 as sqlite  # Python24 and pysqlite
  file = open(filename,'rb')
  doc = file.read()
  file.close()
  return sqlite.Binary(doc)

def SqlToOdf(blob, filename=None):
  """Save the binary string blob containing a zipped OpenDocument into filename.
  Return a corresponding Document if filename is None."""

  if filename is None:
    return loads(blob)

  file = open(filename,'wb')
  file.write(blob)
  file.close()



# -----------------------------------------------------------------------------
# Commmand line processing

if __name__ == "__main__":
    from optparse import OptionParser
    usage = "usage: %prog [options] [files to process]"
    parser = OptionParser(usage)

    parser.add_option("-f", "--file", dest="filename",
                      help="write to output FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="quiet", default=False,
                      help="don't print status messages to stdout")
    parser.add_option("-t", "--selftest",
                      action="store_true", dest="selftest", default=False,
                      help="run test suite")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="verbose status messages")

    (options, args) = parser.parse_args()

    if options.selftest:
        import unittest, tests
        if options.verbose: verbosity = 2
        elif options.quiet: verbosity = 0
        else: verbosity = 1
        testrunner = unittest.TextTestRunner(verbosity=verbosity)
        testrunner.run(tests.test_suite())

    elif 0 is len(args):
        parser.print_help()


#EOF