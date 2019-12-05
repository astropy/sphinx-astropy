# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from sphinx.testing.path import path

# Exclude 'cases' dirs for pytest test collector
collect_ignore = ['cases']


@pytest.fixture(scope='session')
def rootdir():
    """Directory containing Sphinx projects for testing (`str`).

    This fixture, ``rootdir``, is needed by the ``pytest.mark.sphinx`` mark.
    Internal users can use the `casesdir` fixture instead for more canonical
    terminology.
    """
    return path(__file__).parent.abspath() / 'cases'


@pytest.fixture(scope='session')
def casesdir(rootdir):
    """Directory containing Sphinx projects for testing (`str`).
    """
    return rootdir
