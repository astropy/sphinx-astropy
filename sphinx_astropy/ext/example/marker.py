# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""The ``example`` directive that marks examples in the main documentation
text.
"""

__all__ = ('ExampleMarkerDirective',)

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.errors import SphinxError
from sphinx.util.logging import getLogger
from sphinx.util.nodes import nested_parse_with_titles


class ExampleMarkerDirective(Directive):
    """Directive for marking an example snippet in the body of documentation.

    This directive passes content through, unaffected, into the original
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
        if self.example_id in env.sphinx_astropy_examples:
            raise SphinxError(
                'There is already an example titled "{self.title}" '
                '({self.docname:self.lineno})'.format(self=self.title))

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

        # Persist the example for post-processing into the gallery
        env.sphinx_astropy_examples[self.example_id] = {
            'docname': env.docname,
            'lineno': self.lineno,
            'title': self.title,
            'tags': self.tags,
            'content': self.content
        }

        return container_node.children
