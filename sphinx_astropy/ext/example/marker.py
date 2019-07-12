# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""The ``example`` directive that marks examples in the main documentation
text.
"""

__all__ = ('ExampleMarkerDirective', 'purge_examples')

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.errors import SphinxError
from sphinx.util.logging import getLogger
from sphinx.util.nodes import nested_parse_with_titles


class ExampleMarkerDirective(Directive):
    """Directive for marking an example snippet in the body of documentation.

    This directive passes content through into the original
    documentation, but also indexes and copies the content to appear in an
    example gallery.

    Usage example:

    .. code-block:: rst

       .. example:: Title of Example
          :tags: tag-1, tag-2

          Example content.

          The example content can contain multiple paragraphs, lists, images,
          code blocks, equations, and so on.

    Tags are optional and comma-separated.
    """

    _logger = getLogger(__name__)

    has_content = True

    required_arguments = 1  # The title is required
    final_argument_whitespace = True

    option_spec = {
        'tags': directives.unchanged
    }

    def run(self):
        self.assert_has_content()

        env = self.state.document.settings.env

        # Examples are stored under the Sphinx_astropy_example attribute of
        # the environment.
        if not hasattr(env, 'sphinx_astropy_examples'):
            env.sphinx_astropy_examples = {}

        self.title = self.arguments[0].strip()

        self.example_id = '-'.join(('example-src', nodes.make_id(self.title)))

        _check_for_existing_example(env, self.example_id, env.docname,
                                    self.lineno, self.title)

        # Parse tags, which are comma-separated.
        if 'tags' in self.options:
            self.tags = set([t.strip()
                             for t in self.options['tags'].split(',')])
        else:
            self.tags = set()

        self._logger.debug(
            '[sphinx_astropy] example title: %s, tags: %s',
            self.title, self.tags, location=(env.docname, self.lineno))

        # The container_node is just for nested parsing on the directive's
        # content. Only its children get added back into the node tree of
        # the original documentation page.
        container_node = nodes.container(rawsource='\n'.join(self.content))
        # For docname/lineno metadata
        container_node.document = self.state.document
        nested_parse_with_titles(self.state, self.content, container_node)

        # The target node is for backlinks from an example page to the
        # source of the example in the "main" docs.
        target_node = nodes.target('', '', ids=[self.example_id])
        self.state.document.note_explicit_target(target_node)

        # Persist the example for post-processing into the gallery
        env.sphinx_astropy_examples[self.example_id] = {
            'docname': env.docname,
            'lineno': self.lineno,
            'title': self.title,
            'tags': self.tags,
            'content': self.content
        }

        output_nodes = [target_node]
        output_nodes.extend(container_node.children)

        return output_nodes


def purge_examples(app, env, docname):
    """Remove examples from ``env.sphinx_astropy_examples`` during the
    ``env-purge-doc`` event because an associated document was removed from
    the doctree.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The app instance.
    env : sphinx.environment.BuildEnvironment
        The build environment (modified in place).
    docname : str
        Name of the document behing purged during a ``env-purge-doc`` event.
    """
    if not hasattr(env, 'sphinx_astropy_examples'):
        return
    # Filter out examples matching the purged docname
    env.sphinx_astropy_examples = {
        id_: example for id_, example in env.sphinx_astropy_examples.items()
        if example['docname'] != docname}


def _check_for_existing_example(env, example_id, docname, lineno, title):
    """Check if an example already exists in the build environment.

    Parameters
    ----------
    env : sphinx.environment.BuildEnvironment
        The build environment.
    example_id : str
        The example identifier (key for the ``env.sphinx_astropy_examples``
        `dict`).
    docname : str
        The docname associated with the example.
    lineno : int
        The line number of the example in the document.
    title : str
        The title of the example.

    Raises
    ------
    SphinxError
       Raised if an existing example with the same ID exists in the
       environment, comes from a different ``docname`` and ``lineno``.

    Notes
    -----
    Only checking for an existing example with the same ``example_id``
    raises false alarms during testing with multiple builds while
    the numpydoc Sphinx extension is enabled. It seems that numpydoc is
    causing the build environment to carry over between test functions
    of the same root (even with different builders). Checking that the
    existing example came from the same document and location (checking
    ``docname`` and ``lineno`` is sufficient for identifying that the
    existing example only came from a previous build or document read.
    """
    if example_id in env.sphinx_astropy_examples:
        existing_example = env.sphinx_astropy_examples[example_id]
        if existing_example['docname'] == docname \
                and existing_example['lineno'] == lineno:
            logger = getLogger(__name__)
            logger.debug(
                '[sphinx_astropy] Found an existing instance of example '
                '"%s" from an earlier document read', title,
                location=(docname, lineno))
        else:
            raise SphinxError(
                'There is already an example titled "{title}" '
                '({docname}:{lineno})'.format(title=title,
                                              docname=docname,
                                              lineno=lineno))
