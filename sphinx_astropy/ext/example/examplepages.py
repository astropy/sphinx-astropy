# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""APIs for generating standalone example pages.
"""

__all__ = ('ExamplePage', 'ExampleContentDirective')

import os
import posixpath
import re

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.util.logging import getLogger
from sphinx.addnodes import pending_xref

from .utils import is_directive_registered


HTTP_URI = re.compile(r'^http(s?)://')
"""Regular expression for identifying http or https URIs.
"""


class ExamplePage:
    """A class that renders and represents a standalone example page.

    Parameters
    ----------
    example_source : sphinx_astropy.ext.example.preprocessor.ExampleSource
        Object describing the source of the example.
    examples_dir : str
        The directory path where example pages are written.
    app : sphinx.application.Sphinx
        The Sphinx application instance.
    """

    def __init__(self, example_source, examples_dir, app):
        self._example_source = example_source
        self._examples_dir = examples_dir
        self._app = app
        self._srcdir = app.srcdir
        self._tag_pages = []

    @property
    def source(self):
        """Metadata about the source of the example, a
        `sphinx_astropy.ext.example.preprocessor.ExampleSource` instance.`
        """
        return self._example_source

    def __str__(self):
        return '<ExamplePage {self.abs_docname!r}>'.format(self=self)

    def __repr__(self):
        return ('ExamplePage({self.example_source!r}, {self.docname!r},'
                ' tags={self.tags!r})').format(self=self)

    def __eq__(self, other):
        return self.source == other.source

    def __ne__(self, other):
        return self.source != other.source

    def __lt__(self, other):
        return self.source < other.source

    def __le__(self, other):
        return self.source <= other.source

    def __gt__(self, other):
        return self.source > other.source

    def __ge__(self, other):
        return self.source >= other.source

    @property
    def rel_docname(self):
        """The docname of the standalone example page relative to the
        examples directory.
        """
        return self.source.example_id

    @property
    def abs_docname(self):
        """The absolute docname of the standalone example page.
        """
        return '/' + os.path.splitext(
            os.path.relpath(self.filepath, start=self._srcdir))[0]

    @property
    def filepath(self):
        """The filesystem path where the reStructuredText file for the
        standalone example page is rendered.
        """
        return os.path.join(self._examples_dir,
                            self.rel_docname + '.rst')

    def insert_tag_page(self, tag_page):
        """Associate a tag page with the example page.

        Typically this API is called by
        `sphinx_astropy.ext.example.indexpages.generate_tag_pages`, which
        simultaneously creates tag pages and associates eample pages with
        those tag pages.

        Parameters
        ----------
        tag_page : sphinx_astropy.ext.examples.indexpages.TagPage
            A tag page.

        See also
        --------
        tag_pages
        """
        self._tag_pages.append(tag_page)
        self._tag_pages.sort()

    @property
    def tag_pages(self):
        """Sequence of tag pages
        (`sphinx_astropy.ext.examples.indexpages.TagPage`) associated with
        the example page.
        """
        return self._tag_pages

    def render(self, renderer):
        """Render the source for the standalone example page using a
        ``astropy_example/examplepage.rst`` template.

        Parameters
        ----------
        renderer : sphinx_astropy.ext.example.templates.Renderer
            The Jinja template renderer.

        Returns
        -------
        content : str
            The content of the standalone example page.
        """
        context = {
            'title': self.source.title,
            'tag_pages': self.tag_pages,
            'example': self.source,
            'has_doctestskipall': is_directive_registered('doctest-skip-all')
        }
        return renderer.render('astropy_example/examplepage.rst', context)

    def render_and_save(self, renderer):
        """Render the standalone example page and write it to `filepath`
        using the ``astropy_example/examplepage.rst`` template.

        Parameters
        ----------
        renderer : sphinx_astropy.ext.example.templates.Renderer
            The Jinja template renderer.
        """
        content = self.render(renderer)
        with open(self.filepath, 'w') as fh:
            fh.write(content)


class ExampleContentDirective(Directive):
    """A directive that inserts content from an example marked by the
    ``example`` directive into place.

    Example:

    .. code-block:: rst

       .. example-content:: example-id

    The argument is the ID of the example.
    """

    _logger = getLogger(__name__)
    has_content = False
    required_arguments = 1  # example ID

    def run(self):
        self.env = self.state.document.settings.env
        self.example_id = self.arguments[0].strip()
        try:
            self.example = self.env.sphinx_astropy_examples[self.example_id]
        except (KeyError, AttributeError):
            message = 'Example {} not found in the environment'.format(
                self.example_id)
            self._logger.warning(message)
            return [nodes.Text(message, message)]

        # Adapt nodes to work from the standalone example page rather than the
        # source page.
        for node in self.example['content_node'].traverse():
            if isinstance(node, pending_xref):
                self._process_pending_xref(node)
            elif isinstance(node, nodes.image):
                self._process_pending_image(node)
        return [self.example['content_node']]

    def _process_pending_xref(self, node):
        """Adapt a ``pending_xref`` node to work from a standalone example
        page.

        Parameters
        ----------
        node : sphinx.addnodes.pending_xref
            A ``pending_xref`` node type.
        """
        # The docname of the page where the example originated.
        origin_docname = node['refdoc']
        # Switch the refdoc to be the current doc. This will ensure
        # the link resolves correctly from the standalone example page.
        node['refdoc'] = self.env.docname
        if node['refdomain'] == 'std' and node['reftype'] == 'doc':
            if not node['reftarget'].startswith('/'):
                # Replace the relative reftarget with the absolute
                # reftarget so it will resolve from the standalone
                # example page
                abs_reftarget = '/' + posixpath.normpath(
                    posixpath.join(
                        origin_docname,
                        posixpath.relpath(node['reftarget'],
                                          start=origin_docname)))
                node['reftarget'] = abs_reftarget

    def _process_pending_image(self, node):
        """Adapt an ``image`` node to work from a standalone example page.

        Parameters
        ----------
        node : docutils.nodes.image
            An ``image`` node type.
        """
        if not HTTP_URI.match(node['uri']):
            if not node['uri'].startswith('/'):
                # Replace the relative image URI with the absolute
                # project-relative path so it will resolve from the
                # standalone example page.
                abs_uri = '/' + os.path.normpath(
                    os.path.join(
                        self.example['docname'],
                        os.path.relpath(node['uri'],
                                        start=self.example['docname'])))
                node['uri'] = abs_uri
