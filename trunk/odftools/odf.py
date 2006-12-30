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
    the images and tables!) [toHtml]
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
    if isinstance(src, basestring) and len(src) < 1000 and os.path.isfile(src):
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

def OdfToHtml(filename, title=''):
  obj = load(filename)
  return obj.toHtml(title)

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
    usage = "%prog [options] [ file1 dir1 dir2/glob*.od? dir2\.*\.od[ts] ]\n\nAttention:\nIf options"
    usage += " -f, -o and --toxxx are not given and data was changed, the input file will be "
    usage += "overwritten!\nIf -f is given, the output file will be overwritten for every input file."
    parser = OptionParser(usage)

    parser.add_option("-d", "--directory", dest="directory",
                      help="read from DIRECTORY [separate filter with / or \\]", metavar="DIRECTORY")
    parser.add_option("-f", "--file", dest="filename",
                      help="write to output FILE", metavar="FILE")
    parser.add_option("--list-authors", dest="list_author", action="store_true",
                      help="print a list of authors for all input files")
    parser.add_option("-o", "--stdout", dest="stdout", action="store_true",
                      help="write to stdout instead of output FILE")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                      help="don't print status messages to stdout")
    parser.add_option("-r", "--replace", dest="replace", nargs=2,
                      metavar="SEARCH REPLACE",
                      help="replace search string by replacement string")
    parser.add_option("-t", "--selftest", dest="selftest", action="store_true",
                      help="run test suite")
    parser.add_option("--tohtml", dest="tohtml", action="store_true",
                      help="convert document to HTML")
    parser.add_option("--totext", dest="totext", action="store_true",
                      help="convert document to text")
    parser.add_option("--toxml", dest="toxml", action="store_true",
                      help="convert document to XML")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                      help="verbose status messages")
    # TODO: options.recurse
    # TODO: options.case_insensitive_file_search

    (options, args) = parser.parse_args()

    if options.verbose: verbosity = 2
    elif options.quiet: verbosity = 0
    else: verbosity = 1

    filter = ''
    files = []
    if options.directory is not None:
        path, filter = get_path_and_filter(options.directory)
        # path *must* contain a directory, otherwise no files will be added
        files.extend(list_directory(path, filter, True))

    for arg in args:
        if os.path.isfile(arg):
            files.append(arg)
        else:
            path, filter = get_path_and_filter(arg)
            files.extend(list_directory(path, filter))

    files = unique(files)

    if options.selftest:
        import unittest, tests
        testrunner = unittest.TextTestRunner(verbosity=verbosity)
        testrunner.run(tests.test_suite())

    elif len(files) == 0:
        parser.print_help()

    else:
        import sys
        authors = {}
        files = sorted(files)
        for infile in files:
            if verbosity == 2:
                print 'Processing', infile
            doc = load(infile)
            output = ''
            output_odf = False
            changed = False

            if options.replace:
              changed = doc.replace(options.replace[0], options.replace[1])

            if options.totext:
                output = doc.toText().encode('latin_1', 'xmlcharrefreplace')
            elif options.tohtml:
                output = doc.toHtml().encode('latin_1', 'xmlcharrefreplace')
            elif options.toxml:
                output = doc.toXml().encode('latin_1', 'xmlcharrefreplace')
            elif options.list_author:
                author = doc.getAuthor()
                if author:
                    if not authors.has_key(author):
                        authors[author] = []
                    authors[author].append(infile)
            elif options.replace:
                output = dumps(doc)
                output_odf = True

            if output:
                if options.filename:
                    outfile = open(options.filename, 'w')
                elif options.stdout:
                    outfile = sys.stdout
                elif output_odf:
                    if not changed:
                        continue
                    outfile = open(infile, 'wb')
                else:
                    sys.exit("Warning: cannot overwrite input files with text content")

                outfile.write(output)
                if not outfile == sys.stdout:
                    outfile.close()

        output = ''
        for author in sorted(authors.keys()):
            output += 'Author ' + author + ":\n"
            for file in authors[author]:
                output += file + "\n"
            output += "\n"

        if output:
            if options.filename:
                outfile = open(options.filename, 'w')
            elif options.stdout:
                outfile = sys.stdout
            else:
                sys.exit("Warning: cannot overwrite input files with text content")

            outfile.write(output.encode('latin_1', 'xmlcharrefreplace'))
            if not outfile == sys.stdout:
                outfile.close()

#EOF