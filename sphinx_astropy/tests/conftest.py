# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from sphinx.testing.path import path

# Exclude 'roots' dirs for pytest test collector
collect_ignore = ['roots']


@pytest.fixture(scope='session')
def rootdir():
    """Directory containing Sphinx projects for testing.
    """
    return path(__file__).parent.abspath() / 'roots'
