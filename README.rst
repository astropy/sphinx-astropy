About
=====

.. image:: https://zenodo.org/badge/119399685.svg
   :target: https://zenodo.org/badge/latestdoi/119399685
   :alt: Zenodo DOI

.. image:: https://github.com/astropy/sphinx-astropy/actions/workflows/python-tests.yml/badge.svg
   :target: https://github.com/astropy/sphinx-astropy/actions/workflows/python-tests.yml
   :alt: CI Status

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

* `astropy-sphinx-theme <https://github.com/astropy/astropy-sphinx-theme>`_ - the default 'bootstrap' theme use by Astropy and a number of affiliated packages. This goes with `sphinx_astropy.conf.v1`.

* `sphinx-automodapi <http://sphinx-automodapi.readthedocs.io>`_ - an extension that makes it easy to automatically generate API documentation.

* `sphinx-gallery <https://sphinx-gallery.readthedocs.io/en/latest/>`_ - an extension to generate example galleries

* `numpydoc <https://numpydoc.readthedocs.io>`_ - an extension to parse docstrings in NumpyDoc format

* `pillow <https://pillow.readthedocs.io/en/latest/>`_ - a package to deal with
  images, used by some examples in the astropy core documentation.

* `pytest-doctestplus <https://github.com/astropy/pytest-doctestplus/>`_ - providing the 'doctestplus' extension to skip code snippets in narrative documentation.

pydata-sphinx-theme (v2)
^^^^^^^^^^^^^^^^^^^^^^^^

To use the new `pydata-sphinx-theme` with `sphinx_astropy.conf.v2`, you have to install
the optional `[v2]` dependencies::

    pip install sphinx-astropy[v2]

That would pull in the following as well:

* `pydata-sphinx-theme <https://github.com/pydata/pydata-sphinx-theme/>`_ - a clean, three-column,
  Bootstrap-based Sphinx theme by and for the `PyData community <https://pydata.org/>`_.

* `sphinx-copybutton <https://github.com/executablebooks/sphinx-copybutton>`_ - a small Sphinx
  extension to add a "copy" button to code blocks.
