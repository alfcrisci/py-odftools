#!/usr/bin/env python

# XXX: What's the deal with eggs? is that a 2.5 thing?

from distutils.core import setup
import sys 

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
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
        scripts=['odftools/odf'],
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
            ],
        )

