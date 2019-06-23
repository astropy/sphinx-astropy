# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Example gallery Sphinx extension.

Use the ``example`` directive to mark standalone examples where they appear in
the documentation. Other directives (to be built) index and render those
examples in a centralized example gallery.
"""

__all__ = ('setup',)

from pkg_resources import get_distribution


def setup(app):
    """Set up the example gallery Sphinx extensions.

    Parameters
    ----------
    app
        The Sphinx application.

    Returns
    -------
    metadata : `dict`
        Dictionary with extension metadata. See
        http://www.sphinx-doc.org/en/master/extdev/index.html#extension-metadata
        for more information.
    """
    return {'version': get_distribution('sphinx_astropy').version,
            # env_version needs to be incremented when the persisted data
            # formats of the extension change.
            'env_version': 1,
            'parallel_read_safe': True,
            'parallel_write_safe': True}
