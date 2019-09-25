# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""APIs for generating index pages for examples (the main landing page and
pages for individual tags).
"""

__all__ = ('LandingPage', 'TagPage')

import os

from docutils import nodes


class LandingPage:
    """A class that renders and represents the landing page for an example
    gallery.

    Parameters
    ----------
    example_page : sphinx_astropy.ext.example.examplePages.ExampePage
        Object describing a standalone example page.
    examples_dir : str
        The directory path where example pages are written.
    app : sphinx.application.Sphinx
        The Sphinx application instance.
    """

    def __init__(self, example_pages, examples_dir, app):
        self._example_pages = example_pages
        self._examples_dir = examples_dir
        self._app = app
        self._srcdir = app.srcdir

    @property
    def rel_docname(self):
        """The docname of the landing page relative to the examples directory.
        """
        return 'index'

    @property
    def abs_docname(self):
        """The absolute docname of the landing page.
        """
        return '/' + os.path.splitext(
            os.path.relpath(self.filepath, start=self._srcdir))[0]

    @property
    def filepath(self):
        """The filesystem path where the reStructuredText file for the
        landing page is rendered.
        """
        return os.path.join(self._examples_dir,
                            self.rel_docname + '.rst')

    def render(self, renderer):
        """Render the source for the landing page using a
        ``astropy_example/landingpage.rst`` template.

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
            'example_pages': self._example_pages
        }
        return renderer.render('astropy_example/landingpage.rst', context)

    def render_and_save(self, renderer):
        """Render the landing page and write it to `filepath`
        using the ``astropy_example/landingpage.rst`` template.

        Parameters
        ----------
        renderer : sphinx_astropy.ext.example.templates.Renderer
            The Jinja template renderer.
        """
        content = self.render(renderer)
        with open(self.filepath, 'w') as fh:
            fh.write(content)


class TagPage:
    """A class that renders and represents the landing page for an example
    gallery.

    Parameters
    ----------
    tag_name : str
        The tag that this page corresponds to
    example_page : sphinx_astropy.ext.example.examplePages.ExampePage
        Object describing a standalone example page.
    examples_dir : str
        The directory path where example pages are written.
    app : sphinx.application.Sphinx
        The Sphinx application instance.
    """

    def __init__(self, tag_name, example_pages, examples_dir, app):
        self.name = tag_name
        self._examples_dir = examples_dir
        self._app = app
        self._srcdir = app.srcdir

        # Process example pages to get all examples with this tag;
        # also insert a reference to this tag page into that example page
        # so it can link to the tag index page.
        self._example_pages = []
        for example_page in example_pages:
            if tag_name in example_page.source.tags:
                self._example_pages.append(example_page)
                example_page.insert_tag_page(self)

    @classmethod
    def generate_tag_pages(cls, example_pages, examples_dir, srcdir):
        """Construct `TagPage` instances for all tags associated with a
        sequence of ExamplePage instances.

        Simultaneously, this constructor also associates `TagPage` instances
        with `ExamplePage` instances
        (`sphinx_astropy.ext.example.examplepages.ExamplePage.tag_pages`).

        Parameters
        ----------
        example_pages : sequence of ExamplePage
            Example pages.
        examples_dir : str
            The directory path where example pages are written.
        srcdir : str
            The root directory path of the Sphinx project's source.

        Yields
        ------
        tag_page : TagPage
            A tag index page.
        """
        tag_names = set()
        for example_page in example_pages:
            tag_names.update(example_page.source.tags)
        tag_names = list(tag_names)
        tag_names.sort()
        for tag_name in tag_names:
            yield cls(tag_name, example_pages, examples_dir, srcdir)

    def __str__(self):
        return "<TagPage {self.abs_docname!r}>".format(self=self)

    def __repr__(self):
        return ('TagPage({self.name!r}, {self._example_pages!r}, '
                '{self._examples_dir!r}, {self._srcdir!r})').format(self=self)

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def __lt__(self, other):
        return self.name < other.name

    def __le__(self, other):
        return self.name <= other.name

    def __gt__(self, other):
        return self.name > other.name

    def __ge__(self, other):
        return self.name >= other.name

    @property
    def tag_id(self):
        """The URL-safe ID of the tag.
        """
        return nodes.make_id(self.name)

    @property
    def example_pages(self):
        """Iterator over ExamplePage instances tagged with this tag.
        """
        for example in self._example_pages:
            yield example

    @property
    def rel_docname(self):
        """The docname of the tag page relative to the examples directory.
        """
        return 'tags/{self.tag_id}'.format(self=self)

    @property
    def abs_docname(self):
        """The absolute docname of the tag page.
        """
        return '/' + os.path.splitext(
            os.path.relpath(self.filepath, start=self._srcdir))[0]

    @property
    def filepath(self):
        """The filesystem path where the reStructuredText file for the
        tag page is rendered.
        """
        return os.path.join(self._examples_dir,
                            self.rel_docname + '.rst')

    def render(self, renderer):
        """Render the source for the tag page using a
        ``astropy_example/tagpage.rst`` template.

        Parameters
        ----------
        renderer : sphinx_astropy.ext.example.templates.Renderer
            The Jinja template renderer.

        Returns
        -------
        content : str
            The content of the tag page.
        """
        context = {
            'tag': self,
            'title': 'Examples tagged {self.name}'.format(self=self)
        }
        return renderer.render('astropy_example/tagpage.rst', context)

    def render_and_save(self, renderer):
        """Render the tag page and write it to `filepath`
        using the ``astropy_example/tagpage.rst`` template.

        Parameters
        ----------
        renderer : sphinx_astropy.ext.example.templates.Renderer
            The Jinja template renderer.
        """
        content = self.render(renderer)
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as fh:
            fh.write(content)
