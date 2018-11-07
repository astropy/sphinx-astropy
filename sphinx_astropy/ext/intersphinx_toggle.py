# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
The purpose of this extension is to provide a configuration value that can be
used to disable intersphinx on the command-line without editing conf.py. To use,
you can build documentation with::

    sphinx-build ... -D disable_intersphinx=1

This is used e.g. by astropy-helpers when using the build_docs command.
"""

from __future__ import print_function

from distutils.version import LooseVersion

from sphinx import __version__
from sphinx.util import logging
from sphinx.util.console import bold

SPHINX_GE_18 = LooseVersion(__version__) >= LooseVersion('1.8')

logger = logging.getLogger(__name__)


def disable_intersphinx(app, config):
    if config.disable_intersphinx:
        logger.info(bold('disabling intersphinx...'))
        config.intersphinx_mapping.clear()


def setup(app):
    # Note that the config-inited setting was only added in Sphinx 1.8
    if SPHINX_GE_18:
        app.connect('config-inited', disable_intersphinx)
        app.add_config_value('disable_intersphinx', 0, True)
