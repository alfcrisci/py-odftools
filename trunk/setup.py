#!/usr/bin/env python
#! -*- coding: iso-8859-15 -*-

"""Standard script for generating installers for various platforms.

To generate the default built distribution for your platform, run this command:

    python setup.py bdist

This creates a tarball on Unix systems (including cygwin) and a simple
executable installer on Windows.

See also:
http://www.python.org/doc/current/dist/built-dist.html

"""

# TODO: Create an egg if setuptools is available, else fall back to this

from distutils.core import setup
import sys 

# Patch distutils if it can't handle "classifiers" or "download_url" keywords
if sys.version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None


setup(  name='odftools',
        version='0.1.0',
        url='http://code.google.com/p/python/py-odftools/',
        author='Eric Talevich',
        author_email='eric.talevich@gmail.com',
        description='OpenDocument library for Python',
        packages=['odftools'],
        package_data={'odftools': ['README.txt']},
        #scripts=['odftools/odf.py'],
        download_url='http://code.google.com/p/python/py-odftools/',
        classifiers=[
            'Development Status :: 0 - Nada',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: New BSD License'
            'Operating System :: POSIX',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Platform-Independent',
            'Programming Language :: Python',
            'Topic :: Office/Business',
            'Topic :: Software Development',
            ])

