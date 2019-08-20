# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Utilities for managing and rendering page templates.

These utilities are based on sphinx.ext.autosummary, copyright 2007-2019 by the
Sphinx team.
"""

__all__ = ('Renderer',)

import os

from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from sphinx.jinja2glue import BuiltinTemplateLoader
from sphinx.util import rst


class Underliner:
    """Jinja filter for underlining a line of text (to make a headline in
    reStructuredText).

    Parameters
    ----------
    character : str
        The character used for the underline. For example (``'#'``).
    """

    def __init__(self, character):
        if len(character) != 1:
            raise ValueError('The underline must be a single character, '
                             'got %r' % character)
        self._character = character

    def __call__(self, text):
        if '\n' in text:
            raise ValueError('Can only underline single lines')
        return text + '\n' + self._character * len(text)


class Renderer:
    """A class for managing and rendering page templates.

    Inspired by the AutosummaryRenderer in ``sphinx.ext.autosummary``.

    Parameters
    ----------
    builder : sphinx.builders.Builder
        The Sphinx builder. The builder may have its own templates.
    """

    def __init__(self, builder=None, template_dir=None, h1_underline='#'):
        template_dirs = [os.path.join(os.path.dirname(__file__), 'templates')]
        if builder is None:
            if template_dir:
                template_dirs.insert(0, template_dir)
            loader = FileSystemLoader(template_dirs)
        else:
            # allow the user to override the templates
            loader = BuiltinTemplateLoader()
            loader.init(builder, dirs=template_dirs)

        self.env = SandboxedEnvironment(loader=loader)
        """The Jinja2 environment for rendering templates.
        """

        self.env.filters['escape'] = rst.escape
        self.env.filters['h1underline'] = Underliner(h1_underline)

    def render(self, template_name, context):
        """Render a template.
        """
        return self.env.get_template(template_name).render(context)
