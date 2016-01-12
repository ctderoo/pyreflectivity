#!/usr/bin/env python

# Standard library modules.
import os

# Third party modules.
from setuptools import setup, find_packages

# Local modules.

# Globals and constants variables.
BASEDIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(BASEDIR, 'VERSION')) as version_file:
    version = version_file.read().strip()

# Get the long description from the relevant file
with open('README.rst', 'r') as f:
    long_description = f.read()

setup(name='pyreflectivity',
      version=version,
      description="Access Lawrence Berkeley National Laboratory's X-ray reflectivity database for thick mirror",
      long_description=long_description,

      author='Philippe Pinard',
      author_email='philippe.pinard@gmail.com',
      maintainer='Philippe Pinard',
      maintainer_email='philippe.pinard@gmail.com',

      url='https://github.com/ppinard/pyreflectivity',
      license='MIT',
      keywords='reflectivity mirror',

      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: Scientific/Engineering :: Visualization'
        ],

      packages=find_packages(),
      package_data={},

      install_requires=['numpy', 'requests', 'beautifulsoup4'],

      zip_safe=True,

      test_suite='nose.collector'

     )
