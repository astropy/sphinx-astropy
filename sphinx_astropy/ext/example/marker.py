# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""The ``example`` directive that marks examples in the main documentation
text.
"""

__all__ = ('ExampleMarkerNode', 'visit_example_marker_html',
           'depart_example_marker_html', 'ExampleMarkerDirective',
           'purge_examples', 'merge_examples', 'format_title_to_example_id',
           'format_title_to_source_ref_id')

import itertools

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.errors import SphinxError
from sphinx.util.logging import getLogger
from sphinx.util.nodes import nested_parse_with_titles


class ExampleMarkerNode(nodes.container):
    """Docutils node that encapsulates an example in the source content.

    This node is inserted by the `ExampleMarkerDirective`.
    """


def visit_example_marker_html(self, node):
    """HTML visitor for the `ExampleMarkerNode`.

    In HTML, marked up examples are wrapped in a ``<div>`` tag with a class
    of ``astropy-example-source``.
    """
    # The class is used by the HTML postprocessor to capture the HTML of
    # examples. The content of the div gets re-posted onto the stand-alone
    # example pages.
    self.body.append(
        self.starttag(node, 'div', CLASS='astropy-example-source'))


def depart_example_marker_html(self, node):
    """HTML departure handler for the `ExampleMarkerNode`.
    """
    self.body.append('</div>')


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

        # ID for example within the build environment
        self.example_id = format_title_to_example_id(self.title)
        # ID for the reference node. The example-src- prefix distinguishes
        # this ID as the source of the example, rather than a reference to
        # the standalone example page.
        self.ref_id = format_title_to_source_ref_id(self.title)

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

        # The example content is parsed into the ExampleMarkerNode. This
        # node serves as both a container and a node that gets turned into a
        # <div> that the HTML-postprocessor uses to identify and copy
        # example content in the standalone example pages.
        rawsource = '\n'.join(self.content)
        example_node = ExampleMarkerNode(rawsource=rawsource)
        # For docname/lineno metadata
        example_node.document = self.state.document
        nested_parse_with_titles(self.state, self.content, example_node)

        # A copy of all substitution_definition nodes that are found within
        # the directive, and above the example directive (these are mutually
        # exclusive sets). These need to be copied over to the example
        # page so that substitution references can get resolved there.
        # (substitution_reference nodes are resolved by docutils just after
        # this directive is run).
        substitution_definitions = []
        for n in itertools.chain(
                example_node.traverse(nodes.substitution_definition),
                self.state.document.traverse(nodes.substitution_definition)):
            self._logger.debug('Copying substitution {}'.format(n))
            substitution_definitions.append(n.deepcopy())

        # The target node is for backlinks from an example page to the
        # source of the example in the "main" docs.
        # In HTML, this becomes the id attribute of the container div.
        target_node = nodes.target('', '', ids=[self.ref_id])
        self.state.document.note_explicit_target(target_node)

        # Persist the example for post-processing into the gallery
        env.sphinx_astropy_examples[self.example_id] = {
            'docname': env.docname,
            'lineno': self.lineno,
            'title': self.title,
            'tags': self.tags,
            'content': self.content,
            'content_node': example_node.deepcopy(),
            'substitution_definitions': substitution_definitions,
            'ref_id': self.ref_id,
        }

        return [target_node, example_node]


def format_title_to_example_id(title):
    """Convert an example's title into an ID for the title.

    IDs are slugified versions of the title.

    Parameters
    ----------
    title : str
        The title of the example (such as set are the argument to the
        ``example`` directive.

    Returns
    -------
    example_id : str
        The ID for the example. This ID is used internally to identify an
        example within the build environment.
    """
    return nodes.make_id(title)


def format_title_to_source_ref_id(title):
    """Convert an example's title into the ref ID for the example's source
    location.

    The target node itself is generated by the ``example`` directive.

    Parameters
    ----------
    title : str
        The title of the example (such as set are the argument to the
        ``example`` directive.

    Returns
    -------
    ref_id : str
        The ref ID for the node marking the example's *source* location.
    """
    example_id = format_title_to_example_id(title)
    return 'example-src-{}'.format(example_id)


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


def merge_examples(app, env, docnames, other):
    """Merge ``env.sphinx_astropy_examples`` from parallel document reads
    during the ``env-merge-info`` event.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The app instance.
    env : sphinx.environment.BuildEnvironment
        The build environment (modified in place).
    docname : str
        Name of the document behing purged during a ``env-purge-doc`` event.
    other : sphinx.environment.BuildEnvironment
        The build environment from the *other* parallel process.
    """
    if not hasattr(other, 'sphinx_astropy_examples'):
        return
    if not hasattr(env, 'sphinx_astropy_examples'):
        env.sphinx_astropy_examples = {}

    for example_id, example in other.sphinx_astropy_examples.items():
        _check_for_existing_example(env, example_id, example['docname'],
                                    example['lineno'], example['title'])
        env.sphinx_astropy_examples[example_id] = example


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
