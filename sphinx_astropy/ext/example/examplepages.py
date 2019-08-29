# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""APIs for generating standalone example pages.
"""

__all__ = ('ExamplePage',)

import os


class ExamplePage:
    """A class that renders and represents a standalone example page.

    Parameters
    ----------
    example_source : sphinx_astropy.ext.example.preprocessor.ExampleSource
        Object describing the source of the example.
    examples_dir : str
        The directory path where example pages are written.
    srcdir : str
        The root directory path of the Sphinx project's source.
    """

    def __init__(self, example_source, examples_dir, srcdir):
        self._example_source = example_source
        self._examples_dir = examples_dir
        self._srcdir = srcdir
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
            'title': self.source.title
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
