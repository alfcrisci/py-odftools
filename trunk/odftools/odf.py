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

class WriteException: pass
class ReadException: pass


# -----------------------------------------------------------------------------
# Provide a Pickle-like interface for reading and writing.
def load(src):
    """Return a Document object representing the contents of the OpenDocument file src."""
    zf = zipfile.ZipFile(src, 'r')
    names = zf.namelist()
    obj_dict = {}
    obj_dict["additional"] = {}
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


def dump(document, dst):
    """Write the ODF attributes of the document a Zip file named dst."""

    zf = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)

    # Zip document attributes
    for key, filename in Document.files.items():
        if filename:
            zf.writestr(filename, document.getComponentAsString(key))

    # Zip additional files
    for filename, content in document.additional.items():
        zf.writestr(filename, content)

    zf.close()


def loads(str):
    src = StringIO(str)
    obj = load(src)
    src.close()
    return obj

def dumps(document):
    dst = StringIO()
    dst.write(dump(document))
    str = dst.getvalue()
    dst.close()
    return str


# -----------------------------------------------------------------------------
# File format conversions

def OdfToText(filename):
  obj = load(filename)
  return obj.toText()

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
  document = file.read()
  file.close()
  return sqlite.Binary(document)

def SqlToOdf(blob, filename):
  """Save the binary string blob containing a zipped OpenDocument into filename."""
  file = open(filename,'wb')
  file.write(blob)
  file.close()



# -----------------------------------------------------------------------------
# Basic test script

if __name__ == "__main__":
    sqlite = None
    try:
        from sqlite3 import dbapi2 as sqlite    # Python25
    except ImportError:
        from pysqlite2 import dbapi2 as sqlite  # Python24 and pysqlite
    except ImportError:
        pass

    if None != sqlite:
      con = sqlite.connect('odf.sqlite') # ':memory:'
      cur = con.cursor()
      cur.execute("CREATE TABLE IF NOT EXISTS odf(id INTEGER PRIMARY KEY, name TEXT UNIQUE, document BLOB)")

    for filename in os.listdir(os.getcwd()):
        if filename.rsplit('.', 1).pop() in ['odt','ods']:
            if None != sqlite:
              blobdata = OdfToSqlite(filename)

              cur.execute("REPLACE INTO odf(name, document) VALUES (?, ?)",(filename, blobdata))
              con.commit()

              cur.execute("SELECT * FROM odf ORDER BY id DESC LIMIT 1")
              document = cur.fetchone()
              print 'Last database entry:', document

              file = open('fetched_%i_%s' % (document[0], document[1]) , 'wb')
              file.write(document[2])
              file.close()

              SqlToOdf(blobdata, 'fetched_%i_b_%s' % (document[0], document[1]))

            print "\n\nContents of %s:" % filename
            text = OdfToText(filename)
            # before printing or writing to a file, unicode characters should be encoded properly
            text = text.encode('latin_1', 'xmlcharrefreplace')
            print text

            f = open("%s.html" % filename.rsplit('.',1)[0], 'w')
            html = OdfToHTML(filename)
            html = html.encode('latin_1', 'xmlcharrefreplace')
            print html
            f.write(html)
            f.close()

            document = load(filename)
            filename_splitted = filename.rsplit('.', 1);
            dump(document, filename_splitted[0] + '_dumped.' + filename_splitted[1])

    if None != sqlite:
      cur.execute("SELECT id, name FROM odf ORDER BY id")
      documents = cur.fetchall()
      cur.close()
      con.close()
      print len(documents), 'documents stored in database:', documents

#EOF
