Changes in sphinx-astropy
=========================

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
