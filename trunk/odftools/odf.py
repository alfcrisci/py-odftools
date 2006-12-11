#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

""" odf.py


The full OASIS OpenDocument specification can be found here:
http://www.oasis-open.org/specs/index.php#opendocumentv1.0


Bob Sutor's Dr. ODF project/blog series (http://www.sutor.com)
suggests the following features as examples:
- Take an ODF document and throw away all formatting except the basic heading
    and paragraph structure, printing what’s left on the screen. [toText]
- Take an ODF word processing document and convert it to HTML. (Don’t forget
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

See:
  Proposal for an OpenDocument Developers Kit (ODDK)
  http://opendocument.xml.org/node/154
  https://www.linux-community.de/Neues/story?storyid=20964
"""

import os
import zipfile
from cStringIO import StringIO

from document import *

class WriteException: pass
class ReadException: pass


# Map the names of the Zipped files to attributes of the Document object.
g_Filenames = ("content.xml", "styles.xml", "meta.xml",
   "settings.xml", "META-INF/manifest.xml")


def _read(src):
    """ Reads the contents of each of the files in archive src into obj. """
    zf = zipfile.ZipFile(src, 'r')
    names = zf.namelist()
    #obj = Document()
    obj_dict = {}
    for filename in g_Filenames:
        # Check that the filename is actually contained in this zip file
        if filename not in names:
            continue
        component = filename.split('/')[-1].split('.')[0]
        obj_dict[component] = zf.read(filename)
#        print "Contents of component %s:" % filename ##########
#        print obj_dict[component] ##########
    zf.close()
    obj = Document(**obj_dict)
    #print obj.__dict__
    return obj


def _write(obj, dst):
    """ Writes each of obj's attributes to a Zip file named dst.

    Issue: If a file in the current working directory has the same name as
    any of the keys in g_Filenames, an exception is thrown to prevent
    overwriting the file. This is a kludge.
    Better approaches:
    - Create a temporary directory for this work (but what to name it?)
    - Create these files in memory only (how do I do that?)
    """
    zf = zipfile.ZipFile(dst, 'w')

    for filename in g_Filenames:
        if filename in os.listdir(os.getcwd()):
            raise WriteException, "Naming conflict: %s already exists." % filename
        f = open(filename, 'w')
        f.write(obj.getComponentAsString(filename.split('.')[0]))
        f.close()
        zf.write(filename)

    zf.close()
    #TODO: Clean up intermediate files



# -----------------------------------------------------------------------------
# Provides a Pickle-like interface for reading and writing.

def Load(src):
    return _read(src)

def Loads(str):
    src = StringIO(str)
    obj = _read(src)
    src.close()
    return obj

def Dump(obj, dst):
    dst.write(_write(obj))
    return

def Dumps(obj):
    dst = StringIO()
    dst.write(_write(obj))
    str = dst.getvalue()
    dst.close()
    return str


# -----------------------------------------------------------------------------
# File format conversions

def OdfToText(filename):
  obj = _read(filename)
  return obj.toText()


def OdfToHTML(filename, title=''):
  obj = _read(filename)
  return obj.toHTML(title)


# -----------------------------------------------------------------------------
# Basic test script

if __name__ == "__main__":

    for filename in os.listdir(os.getcwd()):
        if filename.rsplit('.').pop() in ['odt']:
            print "\n\nContents of %s:" % filename
            print OdfToText(filename)
            f = open("%s.html" % filename.rsplit('.',1)[0], 'w')
            html = OdfToHTML(filename)
#            print html
            f.write(html) # TODO: Fix UnicodeEncodeError
            f.close()

#EOF
