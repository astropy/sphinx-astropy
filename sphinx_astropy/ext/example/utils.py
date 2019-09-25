# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Low-level utilities and shims.
"""

__all__ = ('is_directive_registered',)

from docutils.parsers.rst import directives


def is_directive_registered(name):
    """Test if a directive is registered.

    This function is equivalent to
    `sphinx.util.docutils.is_directive_registered` that appears in
    Sphinx >= 2.0.

    Parameters
    ----------
    name : str
        Name of the directive.

    Returns
    -------
    bool
        `True` if the directive is loaded, `False` otherwise.
    """
    return name in directives._directives
