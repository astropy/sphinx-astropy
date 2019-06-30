Changes in sphinx-astropy
=========================

1.2 (unreleased)
----------------

- Updated minimum required version of Sphinx to 1.6 as Numpydoc dropped
  suport for older ones. [#19]

- Added an ``example`` directive to mark example snippets in documentation
  text. These examples are republished in an example gallery. [#22]

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
