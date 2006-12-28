import os, tempfile

from tests import TestCaseOdfText, TestCaseOdfImages
import odf, document, diff


class TestCaseText(TestCaseOdfText):
    """A test case for odf text documents."""

    sentence = 'This sentence serves for test purposes.'

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
        text = doc.toText()
        self.assertTrue(self.__class__.sentence in text)

    def test_html(self):
        doc = odf.load(self.file)
        html = doc.toHTML()
        self.assertTrue('<p>' + self.__class__.sentence + '</p>' in html)

    def test_replace(self):
        doc = odf.load(self.file)
        s = self._random_string()
        doc.replace(self.__class__.sentence, s)
        text = doc.toText()
        self.assertFalse(self.__class__.sentence in text)
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

        self.assertEqual(len(doc.getEmbeddedObjects()), 2)
        self.assertEqual(len(doc.getEmbeddedObjects('1')), 2)
        self.assertEqual(len(doc.getEmbeddedObjects('10*F.gif')), 1)
        self.assertEqual(len(doc.getEmbeddedObjects('*?.gif')), 1)
        self.assertRaises(document.ReCompileError, doc.getEmbeddedObjects, '*\\.png')
        self.assertEqual(len(doc.getEmbeddedObjects('10.*D.*\\.png')), 1)




# before printing or writing to a file, unicode characters should be encoded properly
# f.write(doc.toText().encode('latin_1', 'xmlcharrefreplace'))
