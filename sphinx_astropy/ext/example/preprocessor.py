# Licensed under a 3-clause BSD style license - see LICENSE.rst

__all__ = ('detect_examples',)

import re

from sphinx.util.logging import getLogger

from .marker import format_title_to_example_id


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

    # Make the docname absolute
    src_docname = '/' + env.path2doc(filepath)

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
        The docname (project relative path of the source file, without
        an extension) of the source file where the example came from.
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
