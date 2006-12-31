#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

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

from document import *


class WriteError(Exception):
  """Thrown if unable to write output."""
  pass

class ReadError(Exception):
  """Thrown if unable to read input."""
  pass


# -----------------------------------------------------------------------------
# Provide a Pickle-like interface for reading and writing.
def load(src):
    """Return a Document representing the contents of the ODF file src."""

    import zipfile
    zf = zipfile.ZipFile(src, 'r')
# TODO: read previously written ODF files which contained Unicode characters
# http://mail.python.org/pipermail/python-list/2006-January/363102.html
#    except zipfile.BadZipfile:
#      original = open(src, 'rb')
#      try:
#         data = original.read()
#      finally:
#        original.close()
#      position = data.rindex(zipfile.stringEndArchive, -(22 + 0), -20)
#      import cStringIO
#      coredata = cStringIO.StringIO(data[: 22 + position])
#      zf = zipfile.ZipFile(coredata)
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

    import zipfile
    zf = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)

    # Zip document attributes
    for key, filename in Document.files.items():
        if filename:
            zf.writestr(filename, doc.getComponentAsString(key, encoding='utf-8'))

    # Zip additional files
    for filename, content in doc.additional.items():
        zf.writestr(filename, content)

    zf.close()


def loads(str):
    from cStringIO import StringIO
    src = StringIO(str)
    obj = load(src)
    src.close()
    return obj

def dumps(doc):
    from cStringIO import StringIO
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
    usage = "%prog [options] [ file1 dir1 dir2/glob*.od? dir2\.*\.od[ts] ]\n"\
            "\nAttention:\nIf option --force is given and data was changed "\
            "or converted, existing files will be overwritten!\nIf document "\
            "data was changed, the input file will be overwritten."
    parser = OptionParser(usage)

    parser.add_option("-d", "--directory", dest="directory",
                      metavar="DIRECTORY", help=
                      "read from DIRECTORY [separate filter with / or \\]",)
    parser.add_option("-f", "--file", dest="filename",
                      help="write to output FILE", metavar="FILE")
    parser.add_option("--filename-append", dest="filename_append",
                      action="store_true",
                      help="append an extension to each output FILE")
    parser.add_option("--force", dest="force", action="store_true",
                      help="force overwriting of output FILE")
    parser.add_option("--list-authors", dest="list_author", action="store_true",
                      help="print a list of authors for all input files")
    parser.add_option("-o", "--stdout", dest="stdout", action="store_true",
                      help="write to stdout instead of output FILE")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                      help="don't print status messages to stdout")
    parser.add_option("-r", "--replace", dest="replace", nargs=2,
                      metavar="SEARCH REPLACE",
                      help="replace search string by replacement string")
    parser.add_option("--selftest", dest="selftest", action="store_true",
                      help="run test suite")
    parser.add_option("--tohtml", dest="tohtml", action="store_true",
                      help="convert document to HTML")
    parser.add_option("--totext", dest="totext", action="store_true",
                      help="convert document to text")
    parser.add_option("--toxml", dest="toxml", action="store_true",
                      help="convert document to XML")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                      help="verbose status messages")

    # TODO: options.pipe
    # TODO: options.output_directory # Maybe just change --directory ?
    # TODO: options.recurse
    # TODO: options.case_insensitive_file_search
    # TODO: options.encoding

    import sys, codecs

    # Encoding der Standardausgabe und des Dateisystems herausfinden
    # http://wiki.python.de/Von_Umlauten%2C_Unicode_und_Encodings
    # sys.getdefaultencoding()
    stdout_encoding = sys.stdout.encoding or sys.getfilesystemencoding()
    fs_encoding = sys.getfilesystemencoding()
    encoding = 'iso8859_15'

    # Decode all parameters to Unicode before parsing
    sys.argv = [s.decode(fs_encoding) for s in sys.argv]

    options, args = parser.parse_args()

    if options.verbose: verbosity = 2
    elif options.quiet: verbosity = 0
    else: verbosity = 1

    filter = ''
    files = []
    if options.directory is not None:
      try:
        path, filter = get_path_and_filter(options.directory)
      except PathNotFoundError, e:
        if verbosity == 2:
          print_unicode(sys.stderr, u'Warning: Skipping input directory "' +
                        options.directory + '":' + str(e), encoding)
      else:
        # path *must* contain a directory, otherwise no files will be added
        files.extend(list_directory(path, filter, True))

    for arg in args:
      if os.path.isfile(arg):
        files.append(arg)
      else:
        try:
          path, filter = get_path_and_filter(arg)
        except PathNotFoundError, e:
          if verbosity == 2:
            print_unicode(sys.stderr, u'Warning: Skipping input file "' + arg +
                          '":' + str(e), encoding)
        else:
          files.extend(list_directory(path, filter))

    files = unique(files)

    if options.selftest:
      import unittest, tests
      testrunner = unittest.TextTestRunner(verbosity=verbosity)
      testrunner.run(tests.test_suite())

    elif len(files) == 0:
      parser.print_help()

    else:
      try:
        authors = {}
        files = sorted(files)
        import zipfile
        for infile in files:
          if verbosity == 2:
            print_unicode(sys.stdout, u'Processing ' + infile, encoding)

          try:
            doc = load(infile)
          except zipfile.BadZipfile, e:
            print_unicode(sys.stderr, u'Warning: Skipping input file "' +
                          infile + '": ' + str(e), encoding)
            continue

          content = {}
          changed = False

          if options.replace:
            changed = doc.replace(options.replace[0], options.replace[1])

          if options.totext:
            content['txt'] = doc.toText()
          if options.tohtml:
            content['html'] = doc.toHtml(os.path.basename(infile))
          if options.toxml:
            content['xml'] = doc.toXml(encoding='utf-8')
          if options.replace and changed:
            content['odf'] = dumps(doc)
          if options.list_author:
            author = doc.getAuthor()
            if author:
              if not authors.has_key(author):
                authors[author] = []
              authors[author].append(infile)

          if content:
              for extension, output in content.items():
                filename = infile
                output_encoding = ''

                if options.filename:
                  filename = options.filename
                if options.filename_append:
                  if 'odf' == extension:
                    filename += u'.' + infile.split('.')[-1]
                  else:
                    filename += u'.' + unicode(extension)

                if not options.force and os.path.isfile(filename):
                  print_unicode(sys.stderr, u'Warning: Skipping already '
                                + u'existing output file "' + filename + u'"',
                                encoding)
                  continue

                if extension in ['xml','html']:
                  outfile = open(filename, 'w')
                  output_encoding = 'utf-8'
                elif extension == 'odf':
                  outfile = open(filename, 'wb')
                else:
                  outfile = codecs.open(filename, 'w', encoding, 'replace')

                if verbosity == 2:
                  print_unicode(sys.stdout,
                                u'Writing ' + extension + u' to ' + filename,
                                encoding)

                try:
                  print >>outfile, output
                finally:
                  outfile.close()

                # TODO: allow ODF output to stdout with --pipe
                if options.stdout and extension != 'odf':
                  print_unicode(sys.stdout, output, encoding, output_encoding)

        content = []
        for author in sorted(authors.keys()):
          content.append(u'Author ' + author + u':')
          for file in authors[author]:
            content.append(file)
        output = u"\n".join(content)

        if output:
          if options.filename or options.filename_append:
            filename = infile
            if options.filename:
              filename = options.filename
            if options.filename_append:
              filename += u'.txt'

            if not options.force and os.path.isfile(filename):
              print_unicode(sys.stderr,
                            u'Warning: Skipping already existing output'\
                                  u' file "' + filename + u'"', encoding)
            else:
              if verbosity == 2:
                print_unicode(sys.stdout,
                              u'Writing author list to ' + filename, encoding)
              outfile = codecs.open(filename, 'w', encoding, 'replace')
              outfile.write(output)
              outfile.close()

          if options.stdout:
            print_unicode(sys.stdout, output, encoding)

      except UnicodeError, e:
        if unicode == type(e.object):
          import unicodedata
          print e, ' -> character name: "' + unicodedata.name(e.object[e.start]) + '"'
        else:
          print e, ' -> character: "' + e.object[e.start] + '"'
        raise

#EOF