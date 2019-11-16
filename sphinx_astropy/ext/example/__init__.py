# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Example gallery Sphinx extension.

Use the ``example`` directive to mark standalone examples where they appear in
the documentation. Other directives (to be built) index and render those
examples in a centralized example gallery.
"""

__all__ = ('setup',)

from pkg_resources import get_distribution

from .examplepages import ExampleContentDirective
from .marker import (
    ExampleMarkerDirective, purge_examples, merge_examples,
    ExampleMarkerNode, visit_example_marker_html, depart_example_marker_html)
from .preprocessor import preprocess_examples, reorder_example_page_reading


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
    app.add_node(
        ExampleMarkerNode,
        html=(visit_example_marker_html, depart_example_marker_html))
    app.add_directive('example', ExampleMarkerDirective)
    app.add_directive('example-content', ExampleContentDirective)
    app.connect('builder-inited', preprocess_examples)
    app.connect('env-purge-doc', purge_examples)
    app.connect('env-merge-info', merge_examples)
    app.connect('env-before-read-docs', reorder_example_page_reading)

    # Toggles the gallery generation on or off.
    app.add_config_value('astropy_examples_enabled', False, 'env')

    # Configures the directory, relative to the documentation source root,
    # where example pages are created.
    app.add_config_value('astropy_examples_dir', 'examples', 'env')

    # Configures the character to use for h1 underlines in rst
    app.add_config_value('astropy_examples_h1', '#', 'env')

    return {'version': get_distribution('sphinx_astropy').version,
            # env_version needs to be incremented when the persisted data
            # formats of the extension change.
            'env_version': 1,
            'parallel_read_safe': False,
            'parallel_write_safe': True}
