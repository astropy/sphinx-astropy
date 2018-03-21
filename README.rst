
About
=====

This package serves two purposes: it provides a default Sphinx configuration and set of extensions specific to the Astropy project, and it acts as a meta-package by installing all required Sphinx extensions for the core Astropy package and other packages.

Sphinx configuration
--------------------

The default Sphinx configuration can be imported by putting:

.. code-block:: python

    from sphinx_astropy.conf import *

at the top of your ``conf.py`` file. You can then override specific settings from this default configuration, such as adding extensions or intersphinx packages. To give a clearer error messages for users, you can instead write:

.. code-block:: python

    try:
        from sphinx_astropy.conf import *
    except ImportError:
        print('ERROR: the documentation requires the sphinx-astropy package to be installed')
        sys.exit(1)

Dependencies/extensions
-----------------------

Installing **sphinx-astropy** will automatically install (if not already present):

* `Sphinx <http://www.sphinx-doc.org>`_

* `astropy-sphinx-theme <https://github.com/astropy/astropy-sphinx-theme>`_ - the default 'bootstrap' theme use by Astropy and a number of affilited packages.

* `sphinx-automodapi <http://sphinx-automodapi.readthedocs.io>`_ - an extension that makes it easy to automatically generate API documentation.

* `sphinx-gallery <https://sphinx-gallery.readthedocs.io/en/latest/>`_ - an extension to generate example galleries

* `numpydoc <https://numpydoc.readthedocs.io>`_ - an extension to parse docstrings in NumpyDoc format

* `pillow <https://pillow.readthedocs.io/en/latest/>`_ - a package to deal with
  images, used by some examples in the astropy core documentation.

|CircleCI Status|

.. |CircleCI Status| image:: https://circleci.com/gh/astropy/sphinx-astropy.svg?style=svg
   :target: https://circleci.com/gh/astropy/sphinx-astropy
