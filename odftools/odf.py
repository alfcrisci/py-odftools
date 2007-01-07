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
By default it writes to stderr, but you can write to file or stdout instead.
--help prints this and returns.

Multiple input files can be passed as directories and/or file filters.
File filters can be file names, globs and/or regular expressions.
If a relative or absolute file name is not found, the directory will be
searched for all ODF files which match the filter.
So * would find odc, odf, odg, odi, odm, odp, ods, odt, otg, otp, ots, ott.
--recursive searches directories recursively.
The optional argument LEVEL specifies the maximum recursion level.
For every file filter the current folder is the start directory.

One or multiple actions can be done separately to each input file.
Each different output action results in an output file.

The default output file name is the absolute input file name.
--file changes the default output file name.
--extension-replace changes the output name extension to .txt, .xml, .html or
the same ODF extension as the input file has.
--extension-append appends .txt, .xml, .html or the same ODF extension as the
input file has (deactivates --extension-replace).
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

All conversion options take an optional argument for writing to a different
output file. It will be preferred over the --file option and disregards the
--extension-* options.

--stdin reads the contents of one input file from stdin prior to processing any
other input files (if data is available). Default output file name is "stdin".

--stdout prints any output except ODF data to the console in addition to
eventually writing output files.

--quiet suppresses all output to stdout.
--verbose provides more informational output.

--list-authors outputs a list of authors for all input files.
The optional argument FILE specifies the output file name.


For the time being you can provide all options and arguments in any order:
python odf.py --list-authors --toxml dir/a*.ods --totext --extension-append

Except option parameters have to follow their options directly:
python odf.py --replace s([e])arch r\\1place /*.od[ts]
python odf.py a.odt --file dir/a.html --tohtml


Examples:
---------

# Replace text in documents, convert them to text and print the result.
python odf.py /* --replace s r --totext --stdout

# Replace text, convert to HTML and save with appended .html extension.
python odf.py * --replace s r --tohtml --extension-append

# Search recursively, replace text and overwrite only changed input files.
python odf.py . --replace s r --recursive --force

# Search recursively, replace text and overwrite all input files.
python odf.py . --replace s r --recursive --force --toodf

# Search recursively (maximum 2 levels), print authors to stdout and file.
python odf.py /a* /b/c* --recursive 2 --list-authors authors.txt --stdout

# Convert document to HTML and text and save with different file names.
python odf.py a.odt --tohtml b.htm --totext c.log --file=for_unspecified_opts


Attention:
----------

--extension-replace could lead to an output filename of an input file.

--toodf or changed ODF data and no conversions result in ODF output.

Examples:

# Write new ODF files even when no data was changed.
python odf.py * --replace s r --toodf --extension-append

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

    names = zf.namelist()
    obj_dict = {}
    obj_dict["additional"] = {}
    obj_dict["file_dates"] = {}
    if isinstance(src, basestring) and len(src) < 1000 and os.path.isfile(src):
        obj_dict["file"] = src
    inverted = dict([(v,k) for k,v in Document.files.items()])
    file_dates = {}

    for filename in names:
        # If the Zip entry is a special ODF file, store it's own attribute name
        if filename in inverted:
            obj_dict[inverted[filename]] = zf.read(filename)
        else:
            obj_dict["additional"][filename] = zf.read(filename)
        obj_dict["file_dates"][filename] = zf.getinfo(filename).date_time
    zf.close()

    obj = Document(**obj_dict)
    return obj


def dump(doc, dst):
    """Write the ODF content of doc to a Zip file named dst.

    The output file is a full ODF file and readable by load() and OOo.
    """

    import zipfile
    try:
      zf = zipfile.ZipFile(dst, 'w')
    except IOError, e:
      raise WriteError(e)

    # Zip document attributes
    for key, filename in Document.files.items():
        if filename:
            zipinfo = zipfile.ZipInfo(filename, doc.file_dates[filename])
            content = doc.getComponentAsString(key, encoding='utf-8')
            if len(content) != 0:
                zipinfo.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zipinfo, content)

    # Zip additional files
    for filename, content in doc.additional.items():
        zipinfo = zipfile.ZipInfo(filename, doc.file_dates[filename])
        if len(content) != 0:
            zipinfo.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(zipinfo, content)

    zf.close()


def loads(str):
    """Return a Document representing the ODF file contents in binary str."""

    from cStringIO import StringIO
    src = StringIO(str)
    obj = load(src)
    src.close()
    return obj


def dumps(doc):
    """Return a binary string containing the ODF content of doc (Zip file)."""

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
        f = open(filename,'rb')
    except IOError, e:
        raise ReadError(e)
    doc = f.read()
    f.close()
    return sqlite.Binary(doc)


def SqlToOdf(blob, filename=None):
    """Save binary string blob containing a zipped OpenDocument into filename.

    Return a corresponding Document if filename is None.
    """

    if filename is None:
        return loads(blob)

    try:
        f = open(filename,'wb')
    except IOError, e:
        raise WriteError(e)
    f.write(blob)
    f.close()



# -----------------------------------------------------------------------------
# Commmand line processing

def process_command_line():
  """Handle command-line arguments."""

  # as long as optional option values and negation are not implemented
  from optparse_optional import OptionalOptionParser

  usage = "%prog [options] [ file1 dir1 dir2/glob*.od? dir3\.*\.od[ts] ]"
  usage += os.linesep + __doc__
  parser = OptionalOptionParser(usage)

  parser.add_option("-d", "--directory", dest="directory", metavar="DIRECTORY",
                    help="Write all output files to DIRECTORY.")
  parser.add_option("--extension-append", dest="extension_append",
                    action="store_true",
                    help="Append an extension to each output FILE.")
  parser.add_option("--extension-replace", dest="extension_replace",
                    action="store_true",
                    help="Replace the extension of each output FILE.")
  parser.add_option("-f", "--file", dest="filename", metavar="FILE",
                    help="Write to output FILE.")
  parser.add_option("--force", dest="force", action="store_true",
                    help="Force overwriting of output FILE.")
  parser.add_option("-i", "--stdin", dest="stdin", action="store_true",
                    help="Read from stdin in addition to input files.")
  parser.add_option("--list-authors", dest="list_author", action="store_true",
                    oargs=1, help="Print a list of authors for all input files\
                    [optional argument: output FILE].")
  parser.add_option("-o", "--stdout", dest="stdout", action="store_true",
                    help="Write to stdout in addition to output FILE.")
  parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                    help="Don't print status messages to stdout.")
  parser.add_option("-r", "--replace", dest="replace", nargs=2,
                    metavar="SEARCH REPLACE",
                    help="Replace search string by replacement string.")
  parser.add_option("--recursive", dest="recursive", action="store_true",
                    oargs=1, help="Search directories recursively\
                    [optional argument: maximum recursion LEVEL].")
  parser.add_option("--selftest", dest="selftest", action="store_true",
                    help="Run the test suite.")
  parser.add_option("--tohtml", dest="tohtml", action="store_true", oargs=1,
                    help="Convert the document to HTML\
                    [optional argument: output FILE].")
  parser.add_option("--toodf", dest="toodf", action="store_true", oargs=1,
                    help="Convert the document to ODF\
                    [optional argument: output FILE].")
  parser.add_option("--totext", dest="totxt", action="store_true", oargs=1,
                    help="Convert the document to plain text\
                    [optional argument: output FILE].")
  parser.add_option("--toxml", dest="toxml", action="store_true", oargs=1,
                    help="Convert the document to XML\
                    [optional argument: output FILE].")
  parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                    help="Print verbose status messages.")

  # TODO: options.pipe ? Read one file from stdin and write to stdout
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
    stream = sys.stderr
    if options.filename:
      if not options.force and os.path.isfile(options.filename):
        print_unicode(sys.stderr,
                      u'Warning: Skipping already existing output file "%s"' %
                      options.filename, encoding)
        return
      stream = open(options.filename, 'w')
    elif options.stdout:
      stream = sys.stdout
    testrunner = unittest.TextTestRunner(stream=stream, verbosity=verbosity)
    testrunner.run(tests.test_suite())
    if options.filename:
      stream.close()
    return

  filter = ''
  files = []

  stdin = ''
  if options.stdin:
    if not os.fstat(0)[6]:
      print >>sys.stderr, 'Warning: No input file data on stdin (i.e. use',
      print >>sys.stderr, '"cat a.ods | python odf.py --stdin").'
    else:

      try: # Windows needs stdio set for binary mode.
        import msvcrt
        msvcrt.setmode (0, os.O_BINARY) # stdin  = 0
      except ImportError:
        pass

      stdin = sys.stdin.read()

  if isinstance(options.recursive, tuple):
    if not options.recursive[0]:
      options.recursive = False
    else:
      options.recursive = int(options.recursive[1])

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

  if len(files) == 0 and not stdin:
    print >>sys.stderr, 'Warning: No input files given or found.'
    return

  if options.directory and not os.path.isdir(options.directory):
    print_unicode(sys.stderr, u'Warning: output directory does not exist "' +
                  options.directory, encoding)
    return


  try:
    authors = {}
    files = sorted(files)
    if stdin:
      files.insert(0, 'stdin')

    import zipfile
    for infile in files:
      if verbosity == 2:
        print_unicode(sys.stdout, u'Processing ' + infile, encoding)

      try:
        if stdin and 'stdin' == infile:
          doc = loads(stdin)
        else:
          doc = load(infile)
      except zipfile.BadZipfile, e:
        print_unicode(sys.stderr, u'Warning: Skipping input file "' +
                      infile + '": ' + str(e), encoding)
        stdin = ''
        continue

      content = {}
      changed = False

      if options.replace:
        changed = doc.replace(options.replace[0], options.replace[1])

      if parser.is_true(options.totxt):
        content['txt'] = doc.toText()
      if parser.is_true(options.tohtml):
        content['html'] = doc.toHtml(os.path.basename(infile))
      if parser.is_true(options.toxml):
        content['xml'] = doc.toXml(encoding='utf-8')
      if parser.is_true(options.toodf) or (changed and not content):
        content['odf'] = dumps(doc)
      if parser.is_true(options.list_author):
        author = doc.getAuthor()
        if author:
          if not author in authors:
            authors[author] = []
          authors[author].append(infile)

      if content:
        for extension, output in content.items():
          filename = infile
          output_encoding = ''

          if options.filename:
            filename = options.filename

          optional = getattr(options, 'to' + extension)
          if isinstance(optional, tuple):
            filename = optional[1]
          elif options.extension_append or options.extension_replace:
            if 'odf' == extension:
              if stdin and 'stdin' == infile:
                extension_new = unicode(doc.getExtension())
                if not extension_new:
                  extension_new = u'odf'
              else:
                extension_new = infile.split('.')[-1]
            else:
              extension_new = unicode(extension)
            if options.extension_append:
              filename += u'.' + extension_new
            else:
              splitted = filename.split('.')
              if len(splitted) == 1:
                filename += u'.' + extension_new
              else:
                filename = u'.'.join(splitted[:-1]) + u'.' + extension_new

          if options.directory:
            filename = os.path.join(options.directory,
                                    os.path.basename(filename))

          if filename == infile and (extension != 'odf' or not options.force):
            if extension != 'odf':
              if not options.stdout or options.filename:
                print_unicode(sys.stderr,
                              u'Warning: Cannot overwrite input file with '\
                              u'text content (pass --file, --extension-'\
                              u'append or --extension-replace)', encoding)
            elif changed:
              print_unicode(sys.stderr,
                            u'Warning: Not allowed to overwrite input ' \
                            u'file (pass --force to allow)', encoding)

          elif filename != infile and not options.force and os.path.isfile(filename):
            print_unicode(sys.stderr,
                          u'Warning: Skipping already existing output ' \
                          u'file "%s"' % filename, encoding)

          else:
            if options.force and verbosity == 2 and os.path.isfile(filename):
              print_unicode(sys.stderr,
                            u'Warning: Overwriting existing output file ' \
                            u'"%s"' % filename, encoding)

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
              print >>outfile, output, # important: do not print linebreak!
            finally:
              outfile.close()

          # TODO: allow ODF output to stdout with --pipe
          if options.stdout and extension != 'odf':
            print_unicode(sys.stdout, output, encoding, output_encoding)

      stdin = ''


    content = []
    for author in sorted(authors.keys()):
      count = len(authors[author])
      if count == 1:
        filecount = u'1 file'
      else:
        filecount = unicode(count) + u' files'
      content.append(u'Author %s (%s):' % (author, filecount))
      for filename in authors[author]:
        content.append(filename)
    output = unicode(os.linesep).join(content)

    if output:
      # Shouldn't stdout be the default? '>' and '|' already exist as tools.
      if isinstance(options.list_author, tuple):
        filename = options.list_author[1] # first optional argument
      elif options.filename:
        filename = options.filename
        if options.extension_append:
          filename += u'.txt'
        if options.directory:
          filename = os.path.join(options.directory, os.path.basename(filename))
      else:
        filename = ''

      if filename:
        if not options.force and os.path.isfile(filename):
          print_unicode(sys.stderr,
                        u'Warning: Skipping already existing output file ' \
                        u'"%s"' % filename, encoding)
        else:
          if verbosity == 2:
            if options.force and os.path.isfile(filename):
              print_unicode(sys.stderr,
                            u'Warning: Overwriting existing output file ' \
                            u'"%s"' % filename, encoding)
            print_unicode(sys.stdout,
                          u'Writing author list to ' + filename, encoding)
          try:
            outfile = codecs.open(filename, 'w', encoding, 'replace')
          except IOError, e:
            raise WriteError(e)
          outfile.write(output)
          outfile.close()

      elif not options.stdout:
        if verbosity >= 1:
          print >>sys.stderr, 'No way to output list of authors (pass --file',
          print >>sys.stderr, 'or --stdout)'

      else:
        print_unicode(sys.stdout, output, encoding)

  except UnicodeError, e:
    if isinstance(e.object, unicode):
      import unicodedata
      print >>sys.stderr, e, ' -> character name: "',
      print >>sys.stderr, unicodedata.name(e.object[e.start]), '"'
    else:
      print >>sys.stderr, e, ' -> character: "', e.object[e.start], '"'
    raise
  except ReadError, e:
    print_unicode(sys.stderr, u'Could not read input file: %s' % str(e),
                  encoding)
  except WriteError, e:
    print_unicode(sys.stderr, u'Could not write output file: %s' % str(e),
                  encoding)


if __name__ == "__main__":
    process_command_line()


#EOF
