#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

"""odf.py provides a powerful command-line interface for batch scripting.

For more information on using odf.py from the command line, see readme.txt.

"""

import os, sys
import codecs
import re
import zipfile
from cStringIO import StringIO

from document import *


# Exceptions

class WriteError(Exception):
    """Thrown if unable to write output."""
    pass

class ReadError(Exception):
    """Thrown if unable to read input."""
    pass


# Provide a Pickle-like interface for reading and writing.

# Map attribute names to file names
file_map = {'mimetype': 'mimetype', 
            'manifest': 'META-INF/manifest.xml', 
            'content': 'content.xml', 
            'styles': 'styles.xml', 
            'meta': 'meta.xml',
            'settings': 'settings.xml'}


def load(src):
    """Return a Document representing the contents of the ODF file src."""
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
    inverted = dict([(v,k) for k,v in file_map.items()])
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
    try:
      zf = zipfile.ZipFile(dst, 'w')
    except IOError, e:
      raise WriteError(e)

    # Zip document attributes
    for key, filename in file_map.items():
        if filename:
            zipinfo = zipfile.ZipInfo(filename, doc.file_dates[filename])
            data = doc.tostring(key, encoding='utf-8')
            if len(data) != 0:
                zipinfo.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zipinfo, data)

    # Zip additional files
    for filename, data in doc.additional.items():
        zipinfo = zipfile.ZipInfo(filename, doc.file_dates[filename])
        if len(data) != 0:
            zipinfo.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(zipinfo, data)

    zf.close()


def loads(str):
    """Return a Document representing the ODF file contents in binary str."""
    src = StringIO(str)
    obj = load(src)
    src.close()
    return obj


def dumps(doc):
    """Return a binary string containing the ODF content of doc (Zip file)."""
    dst = StringIO()
    dump(doc, dst)
    str = dst.getvalue()
    dst.close()
    return str


# File format conversions

def OdfToText(filename, skip_blank_lines=True):
    obj = load(filename)
    return obj.totext(skip_blank_lines)


def OdfToHtml(filename, title=''):
    obj = load(filename)
    return obj.tohtml(title)



# Path navigation
# (These are useful on Windows where the command shell is weak.)

def list_directory(directory, filter=None, ignore_case=False, recursive=False,
                   must_be_directory=False, include=None, exclude=None):
    """Scan a directory for ODF files.

    filter may be a relative or absolute directory or filename, a glob and/or
    a regular expression. After a file was found by the filter, it must match
    a ODF file extension.

    If recursive is an int, 0 is equivalent to False (no recursion).
    Any positive int limits the maximum recursion level.

    include and exclude may be a relative or absolute directory or filename, a
    glob and/or a regular expression.
    Every file that was found by the filter, must match include and must not
    match exclude (in this order).

    """
    directory = get_win_root_directory(directory)
    if must_be_directory and not os.path.isdir(directory):
        return []

    _pathsep = os.sep # faster path processing
    prefix = u''
    if not directory:
        directory = '.'
    else:
        prefix += directory
        if prefix[-1] not in "/\\":
            prefix += _pathsep

    if os.path.isfile(prefix + filter):
        return [prefix + filter]

    if not os.path.isdir(directory):
        return []

    search_user = get_search_for_filter(filter, ignore_case)
    odf_extensions = r".*\.(?:" + "|".join(odf_formats.keys()) + ")$"
    search_odf = get_search_for_filter(odf_extensions, ignore_case)

    search_include = get_search_for_filter(include, ignore_case, False)
    search_exclude = get_search_for_filter(exclude, ignore_case, False, False)

    found_files = []
    root = os.path.abspath(unicode(directory))
    root_level = root.count(_pathsep)
    if _pathsep == root[-1]:
        root_level -= 1
    for root, dirs, files in os.walk(unicode(directory)):
        files = [directory == '.' and os.path.join(root, f)[2:] or
                 os.path.join(root, f) for f in files if search_user(f) and
                 search_odf(f)]
        if files:
            files = [f for f in files if search_include(f) and
                     not search_exclude(f)]
            found_files.extend(files)

        level = root.count(_pathsep) - root_level
        if _pathsep == root[-1]:
            level -= 1

        if not recursive or \
           not isinstance(recursive, bool) and level >= recursive:
            del dirs[:]

    return found_files


def get_path_and_filter(directory, test_existence=True):
    """Return tuple containing the validated path and file filter."""
    path = ''
    filter = ''

    _pathsep = os.sep # faster path processing
    if _pathsep == '\\':
        directory = directory.replace('/', '\\')

    if len(directory) == 1 and directory == _pathsep:
        path = _pathsep

    elif test_existence and os.path.isdir(directory):
        path = directory
        if path[-1] in r"\/":
            path = path[:-1]
    else:
        search_path_separator = re.compile(r'[/\\]')
        splitted = search_path_separator.split(directory, 1)
        if directory[0] in r"\/":
            first_directory = _pathsep
        else:
            first_directory = get_win_root_directory(splitted[0])

        # TODO: allow directory globbing "test*/*.odt"
        if len(splitted) == 2:
            if test_existence and not os.path.isdir(first_directory):
                test_regex = directory.replace(r'\.', '.')
                splitted = search_path_separator.split(test_regex, 1)
                if len(splitted) == 1:
                    return ('', directory)
                raise PathNotFoundError('Path does not exist: ' + first_directory)
            if first_directory != _pathsep:
                path += splitted[0]
            splitted = search_path_separator.split(splitted[1], 1)
            check_path = path + _pathsep + splitted[0]
            while len(splitted) == 2:
                if test_existence and not os.path.isdir(check_path):
                    raise PathNotFoundError('Path does not exist: ' + check_path)
                path = check_path
                splitted = search_path_separator.split(splitted[1], 1)
                check_path = path + _pathsep + splitted[0]
            if len(path) == 0 and first_directory == _pathsep:
                path = _pathsep
                filter = directory[1 :]
            else:
                filter = directory[len(path)+1 :]

        else:
            filter = directory

    return (path, filter)


def get_win_root_directory(directory):
    """Return windows root directory with path separator, otherwise unchanged."""
    if len(directory) == 2 and directory[1] == ':':
        return directory + os.sep
    return directory


# Text file encoding

def get_encoding(istream):
    """Return the current encoding of the given file."""
    # TODO: support sys.stdout
    encoding = getattr(istream, "encoding", None)
    if not encoding:
        encoding = sys.getdefaultencoding()
    return encoding


def print_unicode(ostream, output, encoding=None, output_encoding=None):
    """Print output to stdout and tries different encodings if necessary."""
    if output_encoding:
        try:
            output = output.decode(output_encoding)
        except UnicodeError, e:
            pass

    try:
        print >>ostream, output
    except UnicodeError, e:
        # output.encode('latin_1')
        ostream = codecs.getwriter(encoding)(ostream)
        print >>ostream, output


def echo(msg, stream=sys.stderr, encoding=sys.stderr.encoding):
    """Print warnings and error messages the way we like it."""
    try:
        print >>stream, msg.encode(encoding)
    except UnicodeError, e:
        stream = codecs.getwriter(encoding)(stream)
        print >>stream, msg


# -----------------------------------------------------------------------------
# Commmand line processing

def main():
    """Handle command-line arguments and options."""

    # as long as optional option values and negation are not implemented
    from optparse_optional import OptionalOptionParser

    usage = "%prog [ file1 dir1 dir2/glob*.od? dir3\.*\.od[ts] ] [options]\n"
    usage += __doc__

    parser = OptionalOptionParser(usage)

    parser.add_option("--case-insensitive", dest="ignorecase",
                        action="store_true",
                        help="Ignore case for every file name matching.")
    parser.add_option("-d", "--directory", dest="directory",
                        help="Write all output files to DIRECTORY.")
    parser.add_option("--exclude", dest="exclude", metavar="FILE", nargs=1,
                        help="Found files must not match the exclude FILE pattern.")
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
                        oargs=1, metavar="[FILE]",
                        help="Read one file from stdin before other input files\
                        [optional argument: output FILE].")
    parser.add_option("--include", dest="include", metavar="FILE", nargs=1,
                        help="Found files must match the include FILE pattern.")
    parser.add_option("--list-authors", dest="list_author", action="store_true",
                        oargs=1, help="Print a list of authors for all input files\
                        [optional argument: output FILE].", metavar="[FILE]")
    parser.add_option("-o", "--stdout", dest="stdout", action="store_true",
                        help="Write to stdout in addition to output FILE.")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                        help="Don't print status messages to stdout.")
    parser.add_option("-r", "--replace", dest="replace", nargs=2,
                        metavar="SEARCH REPLACE",
                        help="Replace search string by replacement string.")
    parser.add_option("--recursive", dest="recursive", action="store_true",
                        oargs=1, metavar="[LEVEL]",
                        help="Search directories recursively\
                        [optional argument: maximum recursion LEVEL].")
    parser.add_option("--selftest", dest="selftest", action="store_true",
                        help="Run the test suite.")
    parser.add_option("--tohtml", dest="tohtml", action="store_true", oargs=1,
                        metavar="[FILE]", help="Convert the document to HTML\
                        [optional argument: output FILE].")
    parser.add_option("--toodf", dest="toodf", action="store_true", oargs=1,
                        metavar="[FILE]", help="Convert the document to ODF\
                        [optional argument: output FILE].")
    parser.add_option("--totext", dest="totxt", action="store_true", oargs=1,
                        metavar="[FILE]", help="Convert the document to plain text\
                        [optional argument: output FILE].")
    parser.add_option("--toxml", dest="toxml", action="store_true", oargs=1,
                        metavar="[FILE]", help="Convert the document to XML\
                        [optional argument: output FILE].")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                        help="Print verbose status messages.")

    # Encoding der Standardausgabe und des Dateisystems herausfinden
    # http://wiki.python.de/Von_Umlauten%2C_Unicode_und_Encodings
    # sys.getdefaultencoding()
    # stdout_encoding = sys.stdout.encoding or sys.getfilesystemencoding()
    fs_encoding = sys.stdout.encoding or sys.getfilesystemencoding()
    # file_encoding = 'iso8859_15'


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
                echo('Warning: Skipping already existing output file "%s"'\
                     % options.filename)
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
    if parser.is_true(options.stdin):
        if not os.fstat(0)[6]:
            print >>sys.stderr, 'Warning: No input file data on stdin (i.e. use',
            print >>sys.stderr, '"cat a.ods | python odf.py --stdin").'
        else:
            try: # Windows needs stdio set for binary mode.
                import msvcrt
                msvcrt.setmode (0, os.O_BINARY) # stdin = 0
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
                    echo('Warning: Skipping input file "%s": %s' % (arg, e))
            else:
                files.extend(list_directory(path, filter, options.ignorecase,
                                            options.recursive, False, 
                                            options.include, options.exclude))

    files = list(set(files))

    if len(files) == 0 and not stdin:
        echo('Warning: No input files given or found.')
        return

    if options.directory and not os.path.isdir(options.directory):
        echo('Warning: output directory does not exist: %s' % options.directory)
        return


    try:
        authors = {}
        files = sorted(files)
        if stdin:
            files.insert(0, 'stdin')

        for infile in files:
            if verbosity == 2:
                echo('Processing %s' % infile)

            try:
                if stdin and 'stdin' == infile:
                    doc = loads(stdin)
                else:
                    doc = load(infile)
            except zipfile.BadZipfile, e:
                echo('Warning: Skipping input file "%s": %s' % (infile, e))
                stdin = ''
                continue

            content = {}
            changed = False

            if options.replace:
                changed = doc.replace(options.replace[0], options.replace[1])

            if parser.is_true(options.totxt):
                content['txt'] = doc.totext()
            if parser.is_true(options.tohtml):
                content['html'] = doc.tohtml(os.path.basename(infile))
            if parser.is_true(options.toxml):
                content['xml'] = doc.content.tostring(encoding='utf-8')
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
                    elif stdin and isinstance(options.stdin, tuple):
                        filename = options.stdin[1]
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
                                echo('Warning: Cannot overwrite input file with '\
                                     'text content (pass --file, --extension-'\
                                     'append or --extension-replace)')
                        elif changed:
                            echo('Warning: Not allowed to overwrite input '\
                                 'file (pass --force to allow)')

                    elif filename != infile and not options.force \
                            and os.path.isfile(filename):
                        echo('Warning: Skipping already existing output file "%s"'\
                             % filename)

                    else:
                        if options.force and verbosity == 2 and os.path.isfile(filename):
                            echo('Warning: Overwriting existing output file "%s"'\
                                 % filename)

                        if extension in ['xml','html']:
                            try:
                                outfile = file(filename, 'w')
                            except IOError, e:
                                raise WriteError(e)
                            output_encoding = 'utf-8'
                        elif extension == 'odf':
                            try:
                                outfile = file(filename, 'wb')
                            except IOError, e:
                                raise WriteError(e)
                        else:
                            try:
                                outfile = codecs.open(filename, 'w', fs_encoding, 'replace')
                            except IOError, e:
                                raise WriteError(e)

                        if verbosity == 2:
                            echo('Writing %s to %s' % (extension, filename))

                        try:
                            print >>outfile, output, # important: do not print linebreak!
                        finally:
                            outfile.close()

                    if options.stdout and extension != 'odf':
                        print_unicode(sys.stdout, output, fs_encoding, output_encoding)

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
                    echo('Warning: Skipping already existing output file "%s"'\
                         % filename)
                else:
                    if verbosity == 2:
                        if options.force and os.path.isfile(filename):
                            echo('Warning: Overwriting existing output file "%s"'\
                                 % filename)
                        echo('Writing author list to %s' % filename)
                    try:
                        outfile = codecs.open(filename, 'w', encoding, errors='replace')
                    except IOError, e:
                        raise WriteError(e)
                    outfile.write(output)
                    outfile.close()

            elif not options.stdout:
                if verbosity >= 1:
                    echo('No way to output list of authors (pass --file or --stdout)')

            else:
                print_unicode(sys.stdout, output, encoding)

    except UnicodeError, e:
        if isinstance(e.object, unicode):
            # Report the problematic character by name
            import unicodedata
            echo('%s -> character name: "%s"' % (e, unicodedata.name(e.object[e.start])))
        else:
            echo('%s -> character: "%s"' % (e, e.object[e.start]))
        raise
    except ReadError, e:
        echo('Could not read input file: %s' % e)
    except WriteError, e:
        echo('Could not write output file: %s' % e)


if __name__ == "__main__":
    main()


# vim: et sts=4 sw=4
#EOF
