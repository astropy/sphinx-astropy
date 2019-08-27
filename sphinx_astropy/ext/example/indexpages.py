# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""APIs for generating index pages for examples (the main landing page and
pages for individual tags).
"""

__all__ = ('LandingPage',)

import os


class LandingPage:
    """A class that renders and represents the landing page for an example
    gallery.

    Parameters
    ----------
    example_page : sphinx_astropy.ext.example.examplePages.ExampePage
        Object describing a standalone example page.
    examples_dir : str
        The directory path where example pages are written.
    srcdir : str
        The root directory path of the Sphinx project's source.
    """

    def __init__(self, example_pages, examples_dir, srcdir):
        self._example_pages = example_pages
        self._examples_dir = examples_dir
        self._srcdir = srcdir

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
