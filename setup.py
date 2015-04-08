#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import os.path
import stat
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from setuptools.command.sdist import sdist as _sdist

from pyf import __version__


class Tox(TestCommand):
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None
    
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    
    def run_tests(self):
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)


class sdist(_sdist):
    def make_readable(self, filename):
        if os.path.exists(filename):
            all_read = stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH
            statinfo = os.stat(filename)
            os.chmod(filename, statinfo.st_mode | all_read)
    
    def run(self):
        # make sure all the inaccessible files are readable
        # so we can read to make a source distribution
        for dpath, dirs, files in os.walk('tests/inaccessible-files'):
            for d in dirs:
                self.make_readable(os.path.join(dpath, d))
            for f in files:
                self.make_readable(os.path.join(dpath, f))
        _sdist.run(self)


desc = 'pyf: programmers find'

here = os.path.abspath(os.path.dirname(__file__))
try:
    long_description = open(os.path.join(here, 'doc/README.rst')).read()
except:
    long_description = desc

# https://pypi.python.org/pypi?%3Aaction=list_classifiers
classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: POSIX',
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.4",
    'Topic :: Software Development :: Build Tools',
    'Topic :: System :: Systems Administration',
    'Topic :: Text Processing',
    'Topic :: Utilities'
]

keywords = ['search', 'text', 'find']
platforms = ['macosx', 'linux', 'unix']

setup(
    name='pyf-programmers-find',
    version=__version__,
    description=desc,
    long_description=long_description,
    author='Simon Blanchard',
    author_email='bnomis@gmail.com',
    license='MIT',
    url='https://github.com/bnomis/pyf',

    classifiers=classifiers,
    keywords=keywords,
    platforms=platforms,

    packages=find_packages(exclude=['tests']),

    entry_points={
        'console_scripts': [
            'pyf = pyf.pyf:run',
            #'pyfiletype = pyf.filetype:main'
        ]
    },

    tests_require=['tox'],
    cmdclass={
        'sdist': sdist,
        'test': Tox
    },
)

