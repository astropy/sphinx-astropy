Changes in sphinx-astropy
=========================

1.9 (2023-06-06)
----------------

- To switch to ``pydata-sphinx-theme``, use ``sphinx_astropy.conf.v2``
  and install the ``[v2]`` optional dependencies. [#59]

- Update minimum required version of Sphinx to 3.0.0. [#57]

- ``check_sphinx_version`` is deprecated. [#57]

1.8 (2023-01-06)
----------------

- Update scipy intersphinx URL. [#53]

- Ensure that jQuery is always installed with Sphinx 6+. [#56]

1.7 (2022-01-10)
----------------

- Removed dependency on ``distutils``. As a result, ``packaging`` is now
  a dependency. [#51]

- Updated ``matplotlib`` URL for intersphinx. [#52]

1.6 (2021-09-22)
----------------

- Updated minimum required version of ``pytest-doctestplus`` to 0.11. [#47]

1.5 (2021-07-20)
----------------

- ``doctest`` sphinx extension has been moved to ``pytest-doctestplus`` and
  therefore ``pytest-doctestplus`` is now a required dependency. [#45]

1.4 (2021-06-22)
----------------

- Updated intersphinx links. [#32, #36]

- Removed LaTeX preamble section redefining warnings and notes. [#34]

- Added support for numpydoc intersphinx xref. [#40]

- Dropped support for Python 3.6. [#42]

1.3 (2020-04-28)
----------------

- Add extension to include generated config in the docs. [#30]

1.2 (2019-11-12)
----------------

- Updated minimum required version of Sphinx to 1.7 as Numpydoc dropped
  support for Sphinx older than 1.6 and the inherit docstring feature is
  only available in Sphinx 1.7 or greater. [#19, #24]

- Make sure all extensions are marked as parallel-safe. [#26]

1.1.1 (2019-02-21)
------------------

- Fix app.info() deprecation warning for Sphinx >= 1.6. [#17]

1.1 (2018-11-15)
----------------

- Added a new extension for controlling whether intersphinx is used on the command-line.

- Added a new extension to give a clear warning if the _static folder is missing.

1.0 (2018-02-07)
----------------

- Initial standalone version of this package (formerly packaged as part of astropy-helpers)
