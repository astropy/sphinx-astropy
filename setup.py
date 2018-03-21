#!/usr/bin/env python

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from setuptools import setup, find_packages

with open('README.rst') as infile:
    long_description = infile.read()

from sphinx_astropy import __version__

setup(name='sphinx-astropy',
      version=__version__,
      description='Sphinx extensions and configuration specific to the Astropy project',
      long_description=long_description,
      author='The Astropy Developers',
      author_email='astropy.team@gmail.com',
      license='BSD',
      url='http://astropy.org',
      zip_safe=False,
      install_requires=['sphinx>=1.4', 'astropy-sphinx-theme', 'numpydoc',
                        'sphinx-automodapi', 'sphinx-gallery', 'pillow'],
      packages=find_packages(),
      package_data={'sphinx_astropy': ['local/*']},
      classifiers=['Intended Audience :: Developers',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 3',
                   'Operating System :: OS Independent',
                   'License :: OSI Approved :: BSD License'])
