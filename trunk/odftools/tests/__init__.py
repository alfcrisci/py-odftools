# Copyright (C) 2006 Jelmer Vernooij <jelmer@samba.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import unittest, os, sys, shutil, tempfile

# wd = os.getcwd()
# if os.path.dirname(__file__) != wd:
#  os.chdir(
#     sys.path.append('..')
td = os.path.dirname(os.path.abspath(__file__))
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


def test_suite():
    import os, sys, re
    path = os.path.abspath(os.path.dirname(sys.argv[0]))
    test = re.compile("^test.*\.py$", re.IGNORECASE)
    modules = [__import__(os.path.splitext(file)[0]) for file in os.listdir(path) if test.search(file)]
    return unittest.TestSuite(map(unittest.defaultTestLoader.loadTestsFromModule, modules))

def run_tests():
    unittest.main(defaultTest="test_suite")


if __name__ == "__main__":
    run_tests()