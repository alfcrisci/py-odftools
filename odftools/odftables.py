#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

"""Script for handling tables in ODF documents.

Features:
    - Extract the <table> elements from an ODF file and return:
        - a set of SQL table definitions
        - a SQLite database containing the tables and data
        - a set of tables in CSV format
        - a spreadsheet with each table as a separate page
    - Dump the entire OpenDocument file to a database as binary data
    - Generate a spreadsheet from the data in the tables of:
        - a SQLite database
        - a CSV file

"""

import sys
# import odf


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



def echo(msg):
    print >>sys.stderr, msg


if __name__ == '__main__':
    from optparse import OptionParser

    usage = "%prog [-hv] -i=[csv|ods|odt|sql] -o=[csv|ods|sql|sqldef] [file]"
    usage += "\n\n" + __doc__

    parser = OptionParser(usage)

    # odftables -vh -if odt -of sql foo.xyz
    parser.add_option("-i", "--in-format", 
            dest="in_format", metavar="FORMAT",
            help="Input file FORMAT: csv, ods, odt or sql.")
    parser.add_option("-o", "--out-format", 
            dest="out_format", metavar="FORMAT",
            help="Output file FORMAT: csv, ods, sql or sqldef.")
    parser.add_option("-q", "--quiet", 
            dest="quiet", action="store_true",
            help="Do not print status messages.")
    parser.add_option("--selftest", 
            dest="selftest", action="store_true",
            help="Run the test suite.")
    parser.add_option("-v", "--version", 
            dest="version", action="store_true",
            help="Display the version info and exit.")

    options, args = parser.parse_args()

    if options.selftest:
        # Run the unit tests and exit
        import unittest
        import tests
        # ...
        sys.exit(0)

    if (options.in_format not in ('csv', 'ods', 'odt', 'sql') 
            or options.out_format not in ('csv', 'ods', 'sql', 'sqldef')):
        # invalid arguments
        print "Invalid arguments"
        sys.exit(0)

    if options.quiet:
        echo = lambda x: None

    if args:
        encoding = sys.stdout.encoding or sys.getfilesystemencoding()
        sys.argv = [a.decode(encoding) for a in sys.argv]
    else:
        args = sys.stdin

    echo(args)

