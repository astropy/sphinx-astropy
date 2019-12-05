# Licensed under a 3-clause BSD style license - see LICENSE.rst

__all__ = ('preprocess_examples', 'detect_examples',)

import re
import os
import shutil

from sphinx.util.logging import getLogger
from sphinx.errors import SphinxError

from .marker import format_title_to_example_id
from .examplepages import ExamplePage
from .indexpages import LandingPage, TagPage
from .templates import Renderer


EXAMPLE_PATTERN = re.compile(
    # Match the example directive and title argument
    r'^\.\. example:: (?P<title>.+)\n'
    # Optionally match the tags option that follows
    # Note: this only works because there aren't other options.
    r'( +:tags: +(?P<tags>.+))?$',
    flags=re.MULTILINE)
"""This regular expression pattern matches ``example`` directives in the
reStructuredText content.

Named groups:

title
    The title of the example

tags
    The comma-separated tag list.

See also
--------
detect_examples
"""


def preprocess_examples(app):
    """Generate the example gallery landing pages and stubs for individual
    standalone example pages by detecting example directives in the
    reStructuredText source.

    This fun is run as part of the ``builder-inited`` event.

    Parameters
    ----------
    app : `sphinx.application.Sphinx`
        The application instance.
    """
    logger = getLogger(__name__)

    if app.config.astropy_examples_enabled is False:
        logger.debug('[sphinx_astropy] Skipping example gallery')
        return

    logger.debug('[sphinx_astropy] preprocessing example gallery pages')

    # Create directory for example pages inside the documentation source dir
    # Incrememental rebuilds of the example gallery aren't supported yet;
    # so for now the examples directory is cleared out before each rebuild.
    examples_dir = os.path.join(app.srcdir, app.config.astropy_examples_dir)
    if os.path.isdir(examples_dir):
        shutil.rmtree(examples_dir)
    os.makedirs(examples_dir)

    renderer = Renderer(
        builder=app.builder,
        h1_underline=app.config.astropy_examples_h1)

    example_pages = []
    example_docname_prefix = app.config.astropy_examples_dir + '/'
    for docname in app.env.found_docs:
        if docname.startswith(example_docname_prefix):
            # Don't scan for examples in examples directory because those
            # docs were deleted at the start of this function.
            continue
        filepath = app.env.doc2path(docname)
        for detected_example in detect_examples(filepath, app.env):
            example_page = ExamplePage(detected_example, examples_dir, app)
            example_pages.append(example_page)
    example_pages.sort()

    for tag_page in TagPage.generate_tag_pages(
            example_pages, examples_dir, app):
        tag_page.render_and_save(renderer)

    for example_page in example_pages:
        example_page.render_and_save(renderer)

    landing_page = LandingPage(example_pages, examples_dir, app)
    landing_page.render_and_save(renderer)

    cache_examples(app.env, example_pages)


def detect_examples(filepath, env):
    """Detect ``example`` directives from a source file by regular expression
    matching.

    Parameters
    ----------
    filepath : str
        A path to a source file.
    env : sphinx.environment.BuildEnvironment
        The build environment.

    Yields
    ------
    detected_example : DetectedExample
        An object containing metadata about an example.
    """
    logger = getLogger(__name__)

    with open(filepath, encoding='utf-8') as fh:
        text = fh.read()

    src_docname = env.path2doc(filepath)

    for m in EXAMPLE_PATTERN.finditer(text):
        title = m.group('title')
        if title is None:
            logger.warning(
                '[sphinx_astropy] Could not parse example title from %s',
                m.group(0))

        tag_option = m.group('tags')
        if tag_option:
            tags = set([t.strip() for t in tag_option.split(', ')])
        else:
            tags = set()

        yield ExampleSource(title, src_docname, tags=tags)


class ExampleSource:
    """Metadata about an example detected from a source file.

    Parameters
    ----------
    title : str
        The title of an example.
    docname : str
        The docname where the example originates from.
    tags : set of str
        The tags associated with the example.

    Notes
    -----
    ``ExampleSource`` objects can sort by title.
    """

    def __init__(self, title, docname, tags=None):
        self.title = title
        """The title of the example.
        """

        if tags is None:
            self.tags = set()
            """The tags (`set` of `str`) associated with the example.
            """
        else:
            self.tags = set(tags)

        self.docname = docname
        """Docname of the page where the example comes from.
        """

        self.abs_docname = '/' + docname
        """Absolute docname of the origin page, suitable for using with a
        ``doc`` referencing role.
        """

        self.example_id = format_title_to_example_id(self.title)
        """The unique ID of the example, based on the title.
        """

    def __repr__(self):
        return ('ExampleSource({self.title!r}, {self.docname!r},'
                ' tags={self.tags!r})').format(self=self)

    def __eq__(self, other):
        return self.title == other.title

    def __ne__(self, other):
        return self.title != other.title

    def __lt__(self, other):
        return self.title < other.title

    def __le__(self, other):
        return self.title <= other.title

    def __gt__(self, other):
        return self.title > other.title

    def __ge__(self, other):
        return self.title >= other.title


def cache_examples(env, example_pages):
    """Cache metadata about examples and standalone example pages into the
    build environment.

    Parameters
    ----------
    env : sphinx.environment.BuildEnvironment
        The Sphinx build environment.
    example_pages : list
        List of `sphinx_astropy.ext.example.examplepages.ExamplePage` instances
        for each generated standalone example page.

    Raises
    ------
    sphinx.error.SphinxError
        Raised if multiple examples share the same title (or ID).

    Notes
    -----
    This function add an attribute called ``sphinx_astropy_examples`` to the
    build environment. The attribute maps example IDs to a mapping of metadata
    about each example. Metadata keys are:

    source_docname
        docname of the page where the example originated from.
    source_path
        File path of the rst file where the example originated from.
    docname
        docname of the standalone example page.
    path
        File path of the standalone example page (rst).
    title
        Title of the example.
    tags
        Set of tags (strings) associated with the example.
    """
    env.sphinx_astropy_examples = {}
    for example_page in example_pages:
        example_id = example_page.source.example_id
        if example_id in env.sphinx_astropy_examples:
            message = (
                'There is already an example titled {0!r}\n'
                '  a: {1!s}\n  b: {2!s}').format(
                example_page.source.title,
                env.sphinx_astropy_examples[example_id]['source_docname'],
                example_page.source.docname
            )
            raise SphinxError(message)
        env.sphinx_astropy_examples[example_id] = {
            'source_docname': example_page.source.docname,
            'source_path': env.doc2path(example_page.source.docname),
            'path': example_page.filepath,
            'docname': example_page.docname,
            'title': example_page.source.title,
            'tags': example_page.source.tags
        }
