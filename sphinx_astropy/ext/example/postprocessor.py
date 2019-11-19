# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Utilities for post-processing HTML built by Sphinx to insert example content
into standalone example pages.
"""

__all__ = ('postprocess_examples',)

import copy
import os.path
import re

from bs4 import BeautifulSoup
from sphinx.util.logging import getLogger

from .marker import format_example_id_to_source_ref_id


EXTERNAL_URI = re.compile(r'^([a-z]+://)|(mailto:)')
"""Regular expression for identifying URIs that aren't relative.
"""


def postprocess_examples(app, exception):
    """Post-process examples by inserting their HTML content into the
    standalone example pages.

    This function is intended to run in the Sphinx ``build-finished`` event.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The Sphinx application.
    exception : Exception or None
        The exception raised earlier if the build failed, or `None` if the
        build succeeded. This function is a no-op if ``exception`` is not None.

    Notes
    -----
    This function is a no-op under any of these circumstances:

    - The Sphinx build, prior to this point, failed (``exception`` is not
      `None`).
    - The format of the builder is not ``html``.
    """
    logger = getLogger(__name__)

    if exception is not None:
        # skip postprocessing if the build has raised an exception
        return

    if app.builder.format != 'html':
        # Make sure this is an HTML build
        return

    if app.config.astropy_examples_enabled is False:
        return

    logger.debug('[sphinx_astropy] postprocessing example gallery pages')

    for example_id, example_info in app.env.sphinx_astropy_examples.items():
        source_html_path = app.builder.get_outfilename(
            example_info['source_docname'])
        html_path = app.builder.get_outfilename(
            example_info['docname'])
        logger.debug('[sphinx_astropy] processing example %s at %s -> %s',
                     example_id, source_html_path,
                     html_path)
        try:
            example_div = extract_example(example_id, source_html_path)
        except Exception as e:
            logger.error('Could not extract example %s from %s:\n%s',
                         example_id, source_html_path, e)
            example_div = make_fallback_example_div(example_id)

        insert_in_example_page(example_id, example_div, html_path, app.outdir,
                               source_html_path)


def extract_example(example_id, source_path):
    """Extract the ``div`` for an example from its source HTML page.

    Parameters
    ----------
    example_id : str
        The internal ID of an example.
    source_path : str
        The path of the HTML file containing the source of an example.

    Returns
    -------
    tree : bs4.Tree
        The div containing the example, as a BeautifulSoup object.

    Notes
    -----
    This function extracts an example from the source page by identifying a
    ``div`` tag with these criteria:

    - The class is ``astropy-example-content``.
    - The ``id`` of the tag is the source ref ID, following the ``example_id``
      (see
      `sphinx_astropy.ext.example.marker.format_example_id_to_source_ref_id`).

    Such a ``div`` is created by the ``example`` directive.
    """
    with open(source_path, 'r') as f:
        source_html = f.read()
    soup = BeautifulSoup(source_html, 'html.parser')

    tag_id = format_example_id_to_source_ref_id(example_id)
    example_div = soup.find('div', id=tag_id, class_='astropy-example-source')

    if example_div is None:
        raise RuntimeError(
            'Did not find source for example {}'.format(example_id))

    return example_div


def make_fallback_example_div(example_id):
    """Create a fallback ``div`` that simulates an example.

    This function is useful as a fallback if ``extract_example`` fails.

    Parameters
    ----------
    example_id : str
        The internal ID of an example.

    Returns
    -------
    tree : bs4.Tree
        The div containing the example fallback, as a BeautifulSoup object.
    """
    html = (
        '<div class="astropy-example-content" id={tag_id}>'
        '<p><strong>Warning:</strong> example {example_id} was not found.'
        '</p></div>'
    ).format(
        example_id=example_id,
        tag_id=format_example_id_to_source_ref_id(example_id))
    return BeautifulSoup(html, 'html.parser')


def insert_in_example_page(example_id, example_div, html_path, root_path,
                           source_html_path):
    """Insert example content into the standalone example's HTML page, updating
    that file.

    Parameters
    ----------
    example_id : str
        The internal ID of the example.
    example_div : bs4.Tree
        The div containing the example (as a BeautifulSoup object) as extracted
        from the source HTML page.
    html_path : str
        The file path of the HTML file for the standalone example page in the
        Sphinx build.
    root_path : str
        The file path of the the built Sphinx HTML site. The ``html_path`` and
        ``source_html_path`` parameters must be contained within this
        ``root_path``.
    """
    logger = getLogger(__name__)

    # A copy of the example_div that's adapted to work specifically
    # on the standalone example pages.
    example_div = copy.copy(example_div)
    adapt_relative_urls(example_div, root_path, source_html_path, html_path)

    try:
        with open(html_path, 'r') as f:
            html = f.read()
    except Exception:
        logger.error('Could not find standalone example page at %s',
                     html_path)
        return

    soup = BeautifulSoup(html, 'html.parser')
    target_div = soup.find('div', id=example_id,
                           class_='astropy-example-content')

    if target_div is None:
        logger.error('Example page %s is incorrectly formatted. '
                     'It does not have a div.astropy-example-content tag',
                     example_id)
        return

    target_div.replace_with(example_div)

    # Remove the wrapper div; these needs to be done on the div
    # in situ in the page's tree.
    tag_id = format_example_id_to_source_ref_id(example_id)
    new_div = soup.find('div', id=tag_id,
                        class_='astropy-example-source')
    if new_div is not None:
        new_div.unwrap()

    with open(html_path, 'wb') as f:
        f.write(soup.encode(formatter='minimal'))


def adapt_relative_urls(tree, root_path, source_page_path,
                        new_page_path):
    """Adapt the relative URLs in HTML content to work from a new page.

    Parameters
    ----------
    tree : bs4.Tree
        The HTML content, as a parsed BeautifulSoup object. This tree is
        modified in place.
    root_path : str
        The file path of the the built Sphinx HTML site. The
        ``source_page_path`` and ``new_page_path`` parameters must be contained
        within this ``root_path``.
    source_page_path : str
        The file path of the HTML page were the content was extracted from.
    new_page_path : str
        The file path of the HTML page where the content is adapted for
        insertion into.
    """
    # Adapt internal links, which Sphinx makes relative so that they work
    # well when browsing without a webserver. We need to make them relative
    # to the destination page.
    for tag in tree.find_all('a'):
        if EXTERNAL_URI.match(tag['href']) or tag['href'].startswith('#'):
            # Skip processing any link that isn't a relative link.
            continue
        if tag['href'].startswith('.//'):
            # Adapt external links made by the Matplotlib plot extension. They
            # start with ".//" and are meant to be relative to the site root.
            abs_path = os.path.join(root_path, tag['href'][3:])  # strip .//
            dest_rel_path = os.path.relpath(
                abs_path,
                start=os.path.dirname(new_page_path))
            tag['href'] = dest_rel_path
        else:
            abs_path = os.path.join(os.path.dirname(source_page_path),
                                    tag['href'])
            dest_rel_path = os.path.relpath(
                abs_path,
                start=os.path.dirname(new_page_path))
            tag['href'] = dest_rel_path

    # Adapt img tags with relative sources
    for tag in tree.find_all('img'):
        if not EXTERNAL_URI.match(tag['src']):
            abs_path = os.path.join(os.path.dirname(source_page_path),
                                    tag['src'])
            dest_rel_path = os.path.relpath(
                abs_path,
                start=os.path.dirname(new_page_path))
            tag['src'] = dest_rel_path
