#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-


# These utilities will attempt to cover the lightweight portions of Rob Weir's
# proposal for an OpenDocument Developer's Kit:
# http://opendocument.xml.org/node/154
#
# The full OASIS OpenDocument specification can be found here:
# http://www.oasis-open.org/specs/index.php#opendocumentv1.0


"""odf.py provides a powerful command line interface for batch scripting.

--selftest just executes all unittests and returns.
--help prints this and returns.

Multiple input files can be passed as directories and/or file filters.
File filters can be file names, globs and/or regular expressions.
If a relative or absolute file name is not found, the directory will be
searched for all ODF files which match the filter.
So * would find odc, odf, odg, odi, odm, odp, ods, odt, otg, otp, ots, ott.
--recursive searches directories recursively.

One or multiple actions can be done separately to each input file.
Each different output action results in an output file.

The default output file name is the absolute input file name.
--file changes the default output file name.
--filename-append appends .txt, .xml, .html or the same ODF extension as the
input file has.
--directory changes the output path (returns if directory doesn't exist).
--force allows overwriting of existing files!

--replace replaces all occurences of a search expression by a replacement
expression before any other action occurs.
Only text nodes of content.xml will be affected.

--tohtml converts the input file to a HTML representation.
--totext converts the input file content.xml to a plain-text representation.
--toxml outputs the input file content.xml.

--toodf outputs the input file even if no data was changed.
Even if --toodf is not given, ODF output will be written if no conversion
was done but data was changed.
No non-ODF data will be written to input file names, even if --force.
The corresponding warning will not be print if --stdout is given and --file
is not given.

--stdout prints any output except ODF data to the console in addition to
eventually writing output files.

--quiet suppresses all output to stdout.
--verbose provides more informational output.

--list-authors outputs a list of authors for all input files.


For the time being you can provide all options and arguments in any order:
python odf.py --list-authors --toxml dir/a*.ods --totext --filename-append

Except option parameters have to follow their options directly:
python odf.py --replace s([e])arch r\\1place /*.od[ts]
python odf.py a.odt --file dir/a.html --tohtml


Examples:
---------

# Replace text in documents, convert them to text and print the result.
python odf.py /* --replace s r --totext --stdout

# Replace text, convert to HTML and save with appended .html extension.
python odf.py * --replace s r --tohtml --filename-append

# Search recursively, replace text and overwrite only changed input files.
python odf.py . --replace s r --recursive --force

# Search recursively, replace text and overwrite all input files.
python odf.py . --replace s r --recursive --force --toodf


Attention:
----------

--toodf or changed ODF data and no conversions result in ODF output.

Examples:

# Write new ODF files even when no data was changed.
python odf.py * --replace s r --toodf --filename-append

# Overwrite input file if data was changed.
python odf.py a.odt --force --replace s r

# Do not overwrite input file EVEN if data was changed! A warning message
# will be printed that writing text to input file is not permitted.
python odf.py a.odt --force --replace s r --totext

# Print to stdout but suppress text-to-ODF warning even if data was changed.
python odf.py a.odt --force --replace s r --totext --stdout

# But: write to input file even if data was not changed.
python odf.py a.odt --force --replace s r --totext --stdout --toodf

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
    try:
        zf = zipfile.ZipFile(src, 'r')
    except IOError, e:
        raise ReadError(e)
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
    try:
      zf = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
    except IOError, e:
      raise WriteError(e)

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

    try:
        file = open(filename,'rb')
    except IOError, e:
        raise ReadError(e)
    doc = file.read()
    file.close()
    return sqlite.Binary(doc)


def SqlToOdf(blob, filename=None):
    """Save the binary string blob containing a zipped OpenDocument into filename.

    Return a corresponding Document if filename is None.
    """

    if filename is None:
        return loads(blob)

    try:
        file = open(filename,'wb')
    except IOError, e:
        raise WriteError(e)
    file.write(blob)
    file.close()



# -----------------------------------------------------------------------------
# Commmand line processing

def process_command_line():
  """Handle command-line arguments."""

  from optparse import OptionParser
  usage = "%prog [options] [ file1 dir1 dir2/glob*.od? dir2\.*\.od[ts] ]\n"
  usage += __doc__.replace("\n  ", "\n") # etal20070102: Why replace()?
  parser = OptionParser(usage)

  parser.add_option("-d", "--directory", dest="directory",
                    metavar="DIRECTORY", help=
                    "write all output files to DIRECTORY")
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
  parser.add_option("--recursive", dest="recursive", action="store_true",
                    help="search directories recursively")
  parser.add_option("--selftest", dest="selftest", action="store_true",
                    help="run test suite")
  parser.add_option("--tohtml", dest="tohtml", action="store_true",
                    help="convert document to HTML")
  parser.add_option("--toodf", dest="toodf", action="store_true",
                    help="convert document to ODF")
  parser.add_option("--totext", dest="totext", action="store_true",
                    help="convert document to text")
  parser.add_option("--toxml", dest="toxml", action="store_true",
                    help="convert document to XML")
  parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                    help="verbose status messages")

  # TODO: options.stdin
  # TODO: options.pipe
  # TODO: options.output_directory # Maybe just change --directory ?
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

  if options.selftest:
    import unittest, tests
    testrunner = unittest.TextTestRunner(verbosity=verbosity)
    testrunner.run(tests.test_suite())
    return

  filter = ''
  files = []

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
        files.extend(list_directory(path, filter, options.recursive))

  files = unique(files)

  if len(files) == 0:
    print >>sys.stderr, 'Warning: No input files given or found.'
    return

  if options.directory and not os.path.isdir(options.directory):
    print_unicode(sys.stderr, u'Warning: output directory does not exist "' +
                  options.directory, encoding)
    return


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
      if options.toodf or (changed and not content):
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
            if options.directory:
              filename = os.path.join(options.directory, os.path.basename(filename))

            if filename == infile and (extension != 'odf' or not options.force):
              if extension != 'odf':
                if not options.stdout or options.filename:
                  print_unicode(sys.stderr, 
                                u'Warning: Cannot overwrite input file ' \
                                u'with text content (pass --file or --filename-append)',
                                encoding)
              elif changed:
                print_unicode(sys.stderr, 
                              u'Warning: Not allowed to overwrite input file (pass --force to allow)',
                              encoding)

            elif filename != infile and not options.force and os.path.isfile(filename):
              print_unicode(sys.stderr, 
                            u'Warning: Skipping already ' \
                            u'existing output file "%s"' % filename,
                            encoding)

            else:
              if options.force and verbosity == 2 and os.path.isfile(filename):
                print_unicode(sys.stdout, 
                              u'Warning: Overwriting existing ' \
                              u'output file "%s"' % filename,
                              encoding)

              if extension in ['xml','html']:
                try:
                  outfile = open(filename, 'w')
                except IOError, e:
                  raise WriteError(e)
                output_encoding = 'utf-8'
              elif extension == 'odf':
                try:
                  outfile = open(filename, 'wb')
                except IOError, e:
                  raise WriteError(e)
              else:
                try:
                  outfile = codecs.open(filename, 'w', encoding, 'replace')
                except IOError, e:
                  raise WriteError(e)

              if verbosity == 2:
                print_unicode(sys.stdout,
                              u'Writing %s to %s' % (extension, filename),
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
      count = len(authors[author])
      if count == 1:
        filecount = u'1 file'
      else:
        filecount = unicode(count) + u' files'
      content.append(u'Author %s (%s):' % (author, filecount))
      for file in authors[author]:
        content.append(file)
    output = u"\n".join(content)

    if output:
      # TODO: maybe set a default output file name like list_authors.txt?
      if options.filename:
        filename = options.filename
        if options.filename_append:
          filename += u'.txt'
        if options.directory:
          filename = os.path.join(options.directory, os.path.basename(filename))

        if not options.force and os.path.isfile(filename):
          print_unicode(sys.stderr,
                        u'Warning: Skipping already existing output file "%s"' % filename,
                        encoding)
        else:
          if verbosity == 2:
            if options.force and os.path.isfile(filename):
              print_unicode(sys.stdout, 
                            u'Warning: Overwriting existing output file "%s"' % filename,
                            encoding)
            print_unicode(sys.stdout,
                          u'Writing author list to ' + filename,
                          encoding)
          try:
            outfile = codecs.open(filename, 'w', encoding, 'replace')
          except IOError, e:
            raise WriteError(e)
          outfile.write(output)
          outfile.close()

      elif not options.stdout:
        if verbosity >= 1:
          print 'No way to output list of authors (pass --file or --stdout)'

      else:
        print_unicode(sys.stdout, output, encoding)

  except UnicodeError, e:
    if unicode == type(e.object):
      import unicodedata
      print >>sys.stderr, e, ' -> character name: "' + unicodedata.name(e.object[e.start]) + '"'
    else:
      print >>sys.stderr, e, ' -> character: "' + e.object[e.start] + '"'
    raise
  except ReadError, e:
    print_unicode(sys.stderr, u'Could not read input file: ' + str(e), encoding)
  except WriteError, e:
    print_unicode(sys.stderr, u'Could not write output file: ' + str(e), encoding)


if __name__ == "__main__":
    process_command_line()


#EOF
