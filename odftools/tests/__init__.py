#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

"""Declares the filenames and basic operations for the tests in test_odf.py.

Filenames, test classes and other constants are defined here.

"""

import unittest, os, sys, shutil, tempfile

# wd = os.getcwd()
# if os.path.dirname(__file__) != wd:
#   os.chdir()
# sys.path.append('..')
td = unicode(os.path.dirname(os.path.abspath(__file__)))
if td[-5:] != 'tests':
    td += os.path.sep + 'tests'
    td_prefix = 'tests.'
elif os.getcwd()[-5:] != 'tests':
    td_prefix = 'tests.'
else:
    td_prefix = ''
sys.path.append(os.path.dirname(td))

import odf, document, diff


class TestCaseOdftools(unittest.TestCase):
    """A test case for odftools."""

    def setUp(self):
        super(TestCaseOdftools, self).setUp()

    def log_message_func(self, items, pool):
        return self.next_message

    def _load(self, file, mode='rb'):
        f = open(file, mode)
        s = f.read()
        f.close()
        return s

    def _random_string(self, length=20):
        import random
        return "".join(random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ', length))


class TestCaseOdfTempdir(TestCaseOdftools):
    """A test case for odftools including a temporary directory."""

    def setUp(self):
        super(TestCaseOdftools, self).setUp()
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)


class TestCaseOdfText(TestCaseOdftools):
    """A test case for odftools including a text document."""

    def setUp(self):
        super(TestCaseOdftools, self).setUp()
        # os.path.abspath(td + '/../testdata')
        self.file = os.path.abspath(td + '/simple_text.odt')


class TestCaseOdfImages(TestCaseOdftools):
    """A test case for odftools including a document with image files."""

    def setUp(self):
        super(TestCaseOdftools, self).setUp()
        self.file = os.path.abspath(td + '/simple_graphics.odt')


class TestCaseOdfFormats(TestCaseOdftools):
    """A test case for odftools including a table, lists, and formatted text."""

    def setUp(self):
        super(TestCaseOdftools, self).setUp()
        self.file = os.path.abspath(td + '/formatted_text.odt')


def test_suite():
    import re
    test = re.compile("^test.*\.py$", re.IGNORECASE)
    modules = [__import__(td_prefix + file[:-3], globals(), locals(), ' ') for file in os.listdir(td) if test.search(file)]
    return unittest.TestSuite(map(unittest.defaultTestLoader.loadTestsFromModule, modules))

def run_tests():
    unittest.main(defaultTest="test_suite")


if __name__ == "__main__":
    run_tests()

# vim: et sts=4 sw=4
