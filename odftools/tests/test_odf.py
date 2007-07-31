#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-


"""Runs the specific unit tests for this module.

This file uses classes and filenames defined in __init__.py.

"""

# NB:
# before printing or writing to a file, unicode characters should be encoded properly
# f.write(doc.toText().encode('latin_1', 'xmlcharrefreplace'))

import os, tempfile

from tests import TestCaseOdfText, TestCaseOdfImages
import odf, document, diff


class TestCaseText(TestCaseOdfText):
    """A test case for odf text documents."""

    def test_load(self):
        self.assertTrue(isinstance(odf.load(self.file), document.Document))

    def test_loads(self):
        self.assertTrue(isinstance(odf.loads(self._load(self.file)), document.Document))

    def test_dump(self):
        doc = odf.load(self.file)
        s1 = odf.dumps(doc)
        fd, name = tempfile.mkstemp()
        odf.dump(doc, name)
        f = os.fdopen(fd, 'rb')
        s2 = f.read()
        f.close()
        os.remove(name)
        self.assertEqual(s1, s2, 'File dump is not equal to string dumps')

    def test_dumps(self):
        doc = odf.load(self.file)
        s = odf.dumps(doc)
        self.assertTrue(isinstance(odf.loads(s), document.Document))

    def test_text(self):
        doc = odf.load(self.file)
        text = doc.totext()
        self.assertTrue(simple_text in text)

    def test_html(self):
        doc = odf.load(self.file)
        html = doc.tohtml()
        self.assertTrue(simple_html in html)

    def test_replace(self):
        doc = odf.load(self.file)
        s = self._random_string()
        doc.replace(simple_text, s)
        text = doc.totext()
        self.assertFalse(simple_text in text)
        self.assertTrue(s in text)

    def test_odf_to_sqlite(self):
        sqlite = None
        try:
            from sqlite3 import dbapi2 as sqlite    # Python25
        except ImportError:
            from pysqlite2 import dbapi2 as sqlite  # Python24 and pysqlite
        except ImportError:
            print 'Warning: SQLite not available'
            return

        doc = odf.load(self.file)
        fd, name = tempfile.mkstemp()
        odf.dump(doc, name)

        f = os.fdopen(fd, 'rb')
        s = f.read()
        f.close()
        blob1 = sqlite.Binary(s)

        blob2 = odf.OdfToSqlite(name)

        os.remove(name)

        self.assertEqual(blob1, blob2, 'Previously encoded data is not equal to OdfToSqlite() data')

        con = sqlite.connect(':memory:')
        cur = con.cursor()
        cur.execute("CREATE TABLE odf(document BLOB)")

        cur.execute("INSERT INTO odf VALUES (?)",(blob1,))
        con.commit()
        cur.execute("SELECT document FROM odf")
        blob3 = cur.fetchone()[0]

        self.assertEqual(blob1, blob3, 'Stored SQLite data is not equal to previously encoded data')

    def test_sql_to_odf(self):
        doc = odf.load(self.file)
        s1 = odf.dumps(doc)
        s2 = odf.dumps(odf.SqlToOdf(s1))
        self.assertEqual(s1, s2, 'SqlToOdf data is not equal to previously dumped data')

        fd, name = tempfile.mkstemp()
        odf.SqlToOdf(s1, name)
        f = os.fdopen(fd, 'rb')
        s3 = f.read()
        f.close()
        self.assertEqual(s1, s3, 'SqlToOdf file dump is not equal to previously dumped data')


class TestCaseImages(TestCaseOdfImages):
    """A test case for odf documents with image files."""

    def test_images(self):
        doc = odf.load(self.file)

        self.assertEqual(len(doc.get_embedded()), 2)
        self.assertEqual(len(doc.get_embedded('1')), 2)
        self.assertEqual(len(doc.get_embedded('10*F.gif')), 1)
        self.assertEqual(len(doc.get_embedded('*?.gif')), 1)
        self.assertRaises(document.ReCompileError, doc.get_embedded, r'*\.png')
        self.assertEqual(len(doc.get_embedded(r'10.*D.*\.png')), 1)


class TestCaseFormatting(TestCaseOdfText):
    """A test case for odf documents with tables, lists and formatted text."""

    def test_text(self):
        doc = odf.load(self.file)
        text = doc.totext()
        self.assertTrue(formatted_text in text)

    def test_html(self):
        doc = odf.load(self.file)
        html = doc.tohtml()
        self.assertTrue(formatted_html in html)


# ---------------------------
# Strings for comparison with HTML and plain-text output

simple_text= 'This sentence serves for test purposes.'

simple_html = """<html>
    <head/>
    <body class="">
        <p class="">
            <p class=""/>
            <p class="">
                <p class=""/>
                <p class=""/>

                <p class=""/>
                <p class=""/>
            </p>
            <p class="">
                This sentence serves for test purposes.
            </p>
        </p>
    </body>
</html>"""


formatted_text = """Test Sentences
This document tests basic formatting.
This line tests bold, italic and underline formatting.
This paragraph uses a different style (Text body).
Visit the project homepage at: http://code.google.com/p/py-odftools/

Test List
Unordered list:
One
Two
Three
Ordered list:
First
Second
Third

Test Table

R
r
R
RR
Rr
r
Rr
rr"""

formatted_html = """<html>
    <head/>
    <body class="">
        <p class="">
            <p class="">
                <p class=""/>
                <p class=""/>
                <p class=""/>

                <p class=""/>
            </p>
            <h1 class="">
                Test Sentences
            </h1>
            <p class="">
                This document tests basic formatting.
            </p>
            <p class="">
                This line tests 
                <span class="">

                    bold
                </span>
                , 
                <span class="">
                    italic
                </span>
                and 
                <span class="">
                    underline
                </span>
                formatting.
            </p>

            <p class="">
                This paragraph uses a different style (Text body).
            </p>
            <p class="">
                Visit the project homepage at: 
                <a class="">
                    http://code.google.com/p/py-odftools/
                </a>
            </p>
            <h1 class="">

                Test List
            </h1>
            <p class="">
                Unordered list:
            </p>
            <ol class="">
                <li class="">
                    <p class="">
                        One
                    </p>

                </li>
                <li class="">
                    <p class="">
                        Two
                    </p>
                </li>
                <li class="">
                    <p class="">
                        Three
                    </p>

                </li>
            </ol>
            <p class="">
                Ordered list:
            </p>
            <ol class="">
                <li class="">
                    <p class="">
                        First
                    </p>

                </li>
                <li class="">
                    <p class="">
                        Second
                    </p>
                </li>
                <li class="">
                    <p class="">
                        Third
                    </p>

                </li>
            </ol>
            <p class=""/>
            <h1 class="">
                Test Table
            </h1>
            <table class="">
                <p class=""/>
                <tr class="">

                    <td class="">
                        <p class=""/>
                    </td>
                    <td class="">
                        <p class="">
                            R
                        </p>
                    </td>
                    <td class="">

                        <p class="">
                            r
                        </p>
                    </td>
                </tr>
                <tr class="">
                    <td class="">
                        <p class="">
                            R
                        </p>

                    </td>
                    <td class="">
                        <p class="">
                            RR
                        </p>
                    </td>
                    <td class="">
                        <p class="">
                            Rr
                        </p>

                    </td>
                </tr>
                <tr class="">
                    <td class="">
                        <p class="">
                            r
                        </p>
                    </td>
                    <td class="">

                        <p class="">
                            Rr
                        </p>
                    </td>
                    <td class="">
                        <p class="">
                            rr
                        </p>
                    </td>
                </tr>

            </table>
            <p class=""/>
        </p>
    </body>
</html>"""



# vim: et sts=4 sw=4
