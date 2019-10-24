# Licensed under a 3-clause BSD style license - see LICENSE.rst

from html.parser import HTMLParser
import os.path
import shutil
from xml.etree.ElementTree import tostring

import pytest
from docutils import nodes

# Sphinx pytest fixtures only available in Sphinx 1.7+
pytest.importorskip("sphinx", minversion="1.7")  # noqa E402

from sphinx.testing.util import etree_parse
from sphinx.util import logging
from sphinx.errors import SphinxError
from sphinx.cmd.build import build_main

import sphinx
from sphinx_astropy.ext.example import purge_examples, merge_examples
from sphinx_astropy.ext.example.marker import (
    format_title_to_example_id, format_title_to_source_ref_id)
from sphinx_astropy.ext.example.preprocessor import (
    detect_examples, preprocess_examples)
from sphinx_astropy.ext.example.examplepages import ExamplePage
from sphinx_astropy.ext.example.templates import Renderer
from sphinx_astropy.ext.example.utils import is_directive_registered

sphinx_version = sphinx.version_info[:2]


@pytest.mark.parametrize(
    'title, expected',
    [
        ('Title of an example', 'title-of-an-example'),
        # test unicode normalization
        ('Title of an éxample', 'title-of-an-example')
    ]
)
def test_format_title_to_example_id(title, expected):
    assert expected == format_title_to_example_id(title)


@pytest.mark.parametrize(
    'title, expected',
    [
        ('Title of an example', 'example-src-title-of-an-example')
    ]
)
def test_format_title_to_source_ref_id(title, expected):
    assert expected == format_title_to_source_ref_id(title)


@pytest.mark.sphinx('xml', testroot='example-gallery')
def test_example_directive_targets(app, status, warning):
    """Test that the example directive creates target nodes with the
    appropriate Ids.
    """
    app.verbosity = 2
    logging.setup(app, status, warning)
    app.builder.build_all()

    et = etree_parse(app.outdir / 'example-marker.xml')
    print(tostring(et.getroot(), encoding='unicode'))

    known_target_refids = [
        'example-src-example-with-two-paragraphs',
        'example-src-tagged-example',
        'example-src-example-with-multiple-tags',
        'example-src-example-with-subsections'
    ]
    targets = et.findall('*target')
    target_refids = [t.attrib['refid'] for t in targets]
    for known_target_refid in known_target_refids:
        assert known_target_refid in target_refids


@pytest.mark.sphinx('dummy', testroot='example-gallery')
def test_example_env_persistence(app, status, warning):
    """Test that the examples are added to the app env.
    """
    app.verbosity = 2
    logging.setup(app, status, warning)
    app.builder.build_all()

    assert hasattr(app.env, 'sphinx_astropy_examples')
    examples = app.env.sphinx_astropy_examples

    known_examples = [
        'example-with-two-paragraphs',
        'tagged-example',
        'example-with-multiple-tags',
        'example-with-subsections'
    ]
    for k in known_examples:
        assert k in examples

    # Test tags
    assert examples['example-with-two-paragraphs']['tags'] == set()
    assert examples['tagged-example']['tags'] == set(['tag-a'])
    assert examples['example-with-multiple-tags']['tags'] \
        == set(['tag-a', 'tag-b'])

    ex = examples['example-with-two-paragraphs']

    # Test title
    assert ex['title'] == 'Example with two paragraphs'

    # Test docname
    assert ex['docname'] == 'example-marker'

    # Test ref_id
    assert ex['ref_id'] == 'example-src-example-with-two-paragraphs'

    # Test content
    assert str(ex['content'][0]) == 'This is the first paragraph.'
    assert str(ex['content'][1]) == ''
    assert str(ex['content'][2]) == 'And the second paragraph.'

    # Test content_node
    assert isinstance(ex['content_node'], nodes.container)


@pytest.mark.sphinx('dummy', testroot='example-gallery-duplicates')
def test_example_directive_duplicates(app, status, warning):
    """The example-gallery-duplicates test case has examples with the same
    title, which is disallowed.
    """
    expected_message = r'^There is already an example titled "Tagged example"'
    with pytest.raises(SphinxError, match=expected_message):
        app.builder.build(['examples', 'duplicate-examples'])


@pytest.mark.sphinx('xml', testroot='example-gallery')
def test_example_directive_docstring(app, status, warning):
    """Test an example directive in the docsting of a function that's
    processed by autofunction and numpydoc.
    """
    app.verbosity = 2
    logging.setup(app, status, warning)
    app.builder.build_all()

    # Check the example made it to the app environment
    examples = app.env.sphinx_astropy_examples
    assert 'using-example-func' in examples

    # Check that the reference target got added to the API reference
    et = etree_parse(app.outdir / 'example_func.xml')
    print(tostring(et.getroot(), encoding='unicode'))
    targets = et.getroot().findall('.//target')
    refids = [t.attrib['refid'] for t in targets]
    assert 'example-src-using-example-func' in refids


@pytest.mark.sphinx('dummy', testroot='example-gallery')
def test_purge_examples(app, status, warning):
    """Test purging examples as part of a ``env-purge-doc`` event.

    To mock up this event we run a build then manually purge an example
    """
    app.verbosity = 2
    logging.setup(app, status, warning)
    app.builder.build_all()

    initial_docnames = set(
        [ex['docname'] for ex in app.env.sphinx_astropy_examples.values()])
    assert 'example-marker' in initial_docnames

    purge_examples(app, app.env, 'example-marker')

    after_docnames = set(
        [ex['docname'] for ex in app.env.sphinx_astropy_examples.values()])
    assert 'example-marker' not in after_docnames


@pytest.mark.sphinx('dummy', testroot='example-gallery')
def test_app_setup(app, status, warning):
    """Test that event callbacks, directives, and nodes got added to the
    Sphinx app.
    """
    # Check event callbacks
    listeners = app.events.listeners
    assert purge_examples in listeners['env-purge-doc'].values()
    assert merge_examples in listeners['env-merge-info'].values()
    assert preprocess_examples in listeners['builder-inited'].values()

    # Check registered configs
    assert 'astropy_examples_dir' in app.config
    assert 'astropy_examples_enabled' in app.config

    # Check registered directives
    assert is_directive_registered('example')
    assert is_directive_registered('example-content')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="Example contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_parallel_reads(tmpdir, rootdir):
    """Test that the examples extension works in a parallelized build.
    """
    case_dir = str(rootdir / 'test-example-gallery')
    src_dir = os.path.join(tmpdir.strpath, 'docs')
    shutil.copytree(case_dir, src_dir)

    argv = ['-j 4', '-W', '-b', 'html', src_dir, '_build/html']

    start_dir = os.path.abspath('.')
    try:
        os.chdir(src_dir)
        status = build_main(argv=argv)
    finally:
        os.chdir(start_dir)
    assert status == 0


def test_parallel_reads_duplicates(tmpdir, rootdir):
    """Test that the examples extension works in a parallelized build
    where a failure from a duplicate example is expected.
    """
    case_dir = str(rootdir / 'test-example-gallery-duplicates')
    src_dir = os.path.join(tmpdir.strpath, 'docs')
    shutil.copytree(case_dir, src_dir)

    argv = ['-j 4', '-W', '-b', 'html', src_dir, '_build/html']

    start_dir = os.path.abspath('.')
    try:
        os.chdir(src_dir)
        status = build_main(argv=argv)
    finally:
        os.chdir(start_dir)
    assert status != 0


def test_build_disabled_gallery(tmpdir, rootdir):
    """Test that the examples extension works when galley generation is
    disabled through the ``astropy_examples_enabled`` configuration.
    """
    case_dir = str(rootdir / 'test-example-gallery-disabled')
    src_dir = os.path.join(tmpdir.strpath, 'docs')
    shutil.copytree(case_dir, src_dir)

    argv = ['-j 4', '-W', '-b', 'html', src_dir, '_build/html']

    start_dir = os.path.abspath('.')
    try:
        os.chdir(src_dir)
        status = build_main(argv=argv)
    finally:
        os.chdir(start_dir)
    assert status == 0


@pytest.mark.sphinx('dummy', testroot='example-gallery')
def test_detect_examples(app, status, warning):
    """Test that the detect_examples function can match "examples"
    directives.
    """
    env = app.env
    test_filepath = str(app.srcdir / 'example-marker.rst')
    examples = list(detect_examples(test_filepath, env))

    assert examples[0].title == 'Example with two paragraphs'
    assert len(examples[0].tags) == 0

    assert examples[1].title == 'Tagged example'
    assert examples[1].tags == set(['tag-a'])
    assert repr(examples[1]) == ("ExampleSource('Tagged example', "
                                 "'/example-marker', tags={'tag-a'})")

    assert examples[2].title == 'Example with multiple tags'
    assert examples[2].tags == set(['tag-a', 'tag-b'])

    assert examples[3].title == 'Example with subsections'
    assert examples[3].tags == set(['tag-b'])

    # Test comparisons (by title)
    assert examples[0] < examples[1]
    assert examples[0] <= examples[1]
    assert examples[1] > examples[0]
    assert examples[1] >= examples[0]
    assert examples[1] != examples[0]
    assert examples[0] == examples[0]


@pytest.mark.sphinx('dummy', testroot='example-gallery')
def test_example_page(app, status, warning):
    env = app.env
    renderer = Renderer(h1_underline='#')

    # Test using example-with-two-paragraphs
    test_filepath = str(app.srcdir / 'example-marker.rst')
    examples = list(detect_examples(test_filepath, env))
    example = examples[0]

    examples_dir = os.path.join(app.srcdir, app.config.astropy_examples_dir)
    example_page = ExamplePage(example, examples_dir, app)

    assert example_page.source == example
    assert example_page.rel_docname == 'example-with-two-paragraphs'
    assert example_page.abs_docname == '/examples/example-with-two-paragraphs'
    assert example_page.filepath.endswith(example_page.abs_docname + '.rst')

    rendered_page = example_page.render(renderer)
    expected = (
        '\n'
        '.. doctest-skip-all\n'
        '\n'
        'Example with two paragraphs\n'
        '###########################\n'
        '\n'
        'From :doc:`/example-marker`.\n'
        '\n'
        '.. example-content:: example-with-two-paragraphs'
    )
    assert rendered_page == expected


@pytest.mark.sphinx('html', testroot='example-gallery')
def test_example_page_rendering(app, status, warning):
    """Test that examples pages are being rendered in the source tree by
    the preprocess_examples hook for builder-inited.
    """
    examples_source_dir = os.path.join(
        app.srcdir, app.config.astropy_examples_dir)
    example_page_paths = [
        'example-with-two-paragraphs.rst',
        'tagged-example.rst',
        'example-with-multiple-tags.rst',
        'example-with-subsections.rst'
    ]
    example_page_paths = list(
        map(lambda x: os.path.join(examples_source_dir, x),
            example_page_paths)
    )
    for path in example_page_paths:
        assert os.path.exists(path)

    # Test rendering of tagged-example
    example_page_path = example_page_paths[1]
    with open(example_page_path) as fh:
        rendered_page = fh.read()
    expected = (
        '\n'
        '.. doctest-skip-all\n'
        '\n'
        'Tagged example\n'
        '##############\n'
        '\n'
        'From :doc:`/example-marker`.\n'
        'Tagged:\n'
        ':doc:`tag-a </examples/tags/tag-a>`.\n'
        '\n'
        '.. example-content:: tagged-example'
    )
    assert rendered_page == expected

    # Test rendering of example-with-multiple-tags
    example_page_path = example_page_paths[2]
    with open(example_page_path) as fh:
        rendered_page = fh.read()
    expected = (
        '\n'
        '.. doctest-skip-all\n'
        '\n'
        'Example with multiple tags\n'
        '##########################\n'
        '\n'
        'From :doc:`/example-marker`.\n'
        'Tagged:\n'
        ':doc:`tag-a </examples/tags/tag-a>`,\n'
        ':doc:`tag-b </examples/tags/tag-b>`.\n'
        '\n'
        '.. example-content:: example-with-multiple-tags'
    )
    assert rendered_page == expected


@pytest.mark.sphinx('html', testroot='example-gallery')
def test_index_pages(app, status, warning):
    """Test the rendering of the landing page and the tag pages.
    """
    examples_landing_page_path = os.path.join(
        app.srcdir, app.config.astropy_examples_dir, 'index.rst')
    with open(examples_landing_page_path) as fh:
        contents = fh.read()
    expected = (
        'Example gallery\n'
        '###############\n'
        '\n'
        '.. hidden toctree for Sphinx navigation\n'
        '\n'
        '.. toctree::\n'
        '   :hidden:\n'
        '\n'
        '   api-link\n'
        '   absolute-file-download-example\n'
        '   doc-link\n'
        '   example-using-the-include-directive\n'
        '   example-with-a-figure\n'
        '   example-with-an-external-figure\n'
        '   example-with-an-external-image\n'
        '   example-with-an-image\n'
        '   example-with-multiple-tags\n'
        '   example-with-subsections\n'
        '   example-with-two-paragraphs\n'
        '   external-file-download-example\n'
        '   file-download-example\n'
        '   header-reference-target-example\n'
        '   intersphinx-api-link\n'
        '   intersphinx-ref-link\n'
        '   literalinclude-example\n'
        '   matplotlib-plot\n'
        '   named-equation\n'
        '   ref-link\n'
        '   tagged-example\n'
        '\n'
        '.. Listing for styling (eventually will become a tiled grid)\n'
        '\n'
        '- :doc:`API link <api-link>`\n'
        '  (:doc:`links </examples/tags/links>`)\n'
        '- :doc:`Absolute file download example <absolute-file-download-example>`\n'
        '  (:doc:`includes </examples/tags/includes>`)\n'
        '- :doc:`Doc link <doc-link>`\n'
        '  (:doc:`links </examples/tags/links>`)\n'
        '- :doc:`Example using the include directive <example-using-the-include-directive>`\n'
        '  (:doc:`includes </examples/tags/includes>`)\n'
        '- :doc:`Example with a figure <example-with-a-figure>`\n'
        '  (:doc:`images </examples/tags/images>`)\n'
        '- :doc:`Example with an external figure <example-with-an-external-figure>`\n'
        '  (:doc:`images </examples/tags/images>`)\n'
        '- :doc:`Example with an external image <example-with-an-external-image>`\n'
        '  (:doc:`images </examples/tags/images>`)\n'
        '- :doc:`Example with an image <example-with-an-image>`\n'
        '  (:doc:`images </examples/tags/images>`)\n'
        '- :doc:`Example with multiple tags <example-with-multiple-tags>`\n'
        '  (:doc:`tag-a </examples/tags/tag-a>`,\n'
        '  :doc:`tag-b </examples/tags/tag-b>`)\n'
        '- :doc:`Example with subsections <example-with-subsections>`\n'
        '  (:doc:`tag-b </examples/tags/tag-b>`)\n'
        '- :doc:`Example with two paragraphs <example-with-two-paragraphs>`\n'
        '- :doc:`External file download example <external-file-download-example>`\n'
        '  (:doc:`includes </examples/tags/includes>`)\n'
        '- :doc:`File download example <file-download-example>`\n'
        '  (:doc:`includes </examples/tags/includes>`)\n'
        '- :doc:`Header reference target example <header-reference-target-example>`\n'
        '  (:doc:`reference target </examples/tags/reference-target>`)\n'
        '- :doc:`Intersphinx API link <intersphinx-api-link>`\n'
        '  (:doc:`links </examples/tags/links>`)\n'
        '- :doc:`Intersphinx ref link <intersphinx-ref-link>`\n'
        '  (:doc:`links </examples/tags/links>`)\n'
        '- :doc:`Literalinclude example <literalinclude-example>`\n'
        '  (:doc:`includes </examples/tags/includes>`)\n'
        '- :doc:`Matplotlib plot <matplotlib-plot>`\n'
        '  (:doc:`images </examples/tags/images>`)\n'
        '- :doc:`Named equation <named-equation>`\n'
        '  (:doc:`reference target </examples/tags/reference-target>`)\n'
        '- :doc:`Ref link <ref-link>`\n'
        '  (:doc:`links </examples/tags/links>`)\n'
        '- :doc:`Tagged example <tagged-example>`\n'
        '  (:doc:`tag-a </examples/tags/tag-a>`)'
    )
    assert contents == expected

    tag_a_page_path = os.path.join(
        app.srcdir, app.config.astropy_examples_dir, 'tags', 'tag-a.rst')
    with open(tag_a_page_path) as fh:
        contents = fh.read()
    expected = (
        ':orphan:\n'
        '\n'
        'Examples tagged tag-a\n'
        '#####################\n'
        '\n'
        '- :doc:`Example with multiple tags </examples/example-with-multiple-tags>`\n'
        '  (:doc:`tag-a </examples/tags/tag-a>`)\n'
        '- :doc:`Tagged example </examples/tagged-example>`\n'
        '  (:doc:`tag-a </examples/tags/tag-a>`)'
    )
    assert contents == expected


@pytest.mark.sphinx('html', testroot='example-gallery')
def test_links(app, status, warning):
    """Test link resolution on standalone example pages.
    """
    app.verbosity = 2
    logging.setup(app, status, warning)
    app.builder.build_all()
    print(app.outdir)

    # The api-link example has an example of an internal Python API link.
    path = app.outdir / 'examples/api-link.html'
    with open(path) as fh:
        html = fh.read()
    parser = ReferenceInternalHtmlParser()
    parser.feed(html)
    # Make sure the APIs link's href got adjusted to be relative
    # to the example page.
    assert parser.has_href(
        '../example_func.html'
        '#sphinx_astropy.tests.example_module.example.example_func')

    # The ref-link example has an example of a link made with the ref role.
    path = app.outdir / 'examples/ref-link.html'
    with open(path) as fh:
        html = fh.read()
    parser = ReferenceInternalHtmlParser()
    parser.feed(html)
    assert parser.has_href('../example-marker.html#example-link-target')

    # The doc-link example has a doc role for making a link to another page.
    path = app.outdir / 'examples/doc-link.html'
    with open(path) as fh:
        html = fh.read()
    parser.feed(html)
    assert parser.has_href('../example-marker.html')

    # The intersphinx-ref-link example has a ref role to the Astropy
    # docs with intersphinx
    path = app.outdir / 'examples/intersphinx-ref-link.html'
    with open(path) as fh:
        html = fh.read()
    parser = ReferenceExternalHtmlParser()
    parser.feed(html)
    assert parser.has_href('https://docs.astropy.org/en/stable/wcs/index.html#astropy-wcs')

    # The intersphinx-api-link example has a ref role to the Astropy
    # docs with intersphinx
    path = app.outdir / 'examples/intersphinx-api-link.html'
    with open(path) as fh:
        html = fh.read()
    parser = ReferenceExternalHtmlParser()
    parser.feed(html)
    assert parser.has_href('https://docs.astropy.org/en/stable/api/astropy.table.Table.html#astropy.table.Table')

    # The header-reference-target-example example has an example of a ref
    # link to a target on a header that's also part of the example content.
    # This shows that the link ends up pointing back to the original.
    path = app.outdir / 'examples/header-reference-target-example.html'
    with open(path) as fh:
        html = fh.read()
    parser = ReferenceInternalHtmlParser()
    parser.feed(html)
    assert parser.has_href('../ref-targets.html#section-target')

    # The named-equation example has an example of a an equation with a
    # label, and a reference to that label.
    # This shows that the link points back to the original equation.
    path = app.outdir / 'examples/named-equation.html'
    with open(path) as fh:
        html = fh.read()
    parser = ReferenceInternalHtmlParser()
    parser.feed(html)
    assert parser.has_href('../ref-targets.html#equation-euler')


@pytest.mark.sphinx('html', testroot='example-gallery')
def test_images(app, status, warning):
    """Test resolution of image-like items in examples.
    """
    app.verbosity = 2
    logging.setup(app, status, warning)
    app.builder.build_all()
    print(app.outdir)

    # A regular image directive with a relative URI to a local image.
    path = app.outdir / 'examples/example-with-an-image.html'
    with open(path) as fh:
        html = fh.read()
    parser = ImgHtmlParser()
    parser.feed(html)
    # Make sure the APIs link's href got adjusted to be relative
    # to the example page.
    assert parser.has_img_src(
        '../_images/astropy_project_logo.svg')

    # A regular image directive with an external URI
    path = app.outdir / 'examples/example-with-an-external-image.html'
    with open(path) as fh:
        html = fh.read()
    parser = ImgHtmlParser()
    parser.feed(html)
    # Make sure the APIs link's href got adjusted to be relative
    # to the example page.
    assert parser.has_img_src(
        'https://www.astropy.org/images/astropy_project_logo.svg')

    # A figure directive with a relative URI to a local image.
    path = app.outdir / 'examples/example-with-a-figure.html'
    with open(path) as fh:
        html = fh.read()
    parser = ImgHtmlParser()
    parser.feed(html)
    # Make sure the APIs link's href got adjusted to be relative
    # to the example page.
    assert parser.has_img_src(
        '../_images/astropy_project_logo.svg')

    # A figure directive with an external image URI.
    path = app.outdir / 'examples/example-with-an-external-figure.html'
    with open(path) as fh:
        html = fh.read()
    parser = ImgHtmlParser()
    parser.feed(html)
    # Make sure the APIs link's href got adjusted to be relative
    # to the example page.
    assert parser.has_img_src(
        'https://www.astropy.org/images/astropy_project_logo.svg')

    # A matplotlib-based plot directive
    path = app.outdir / 'examples/matplotlib-plot.html'
    with open(path) as fh:
        html = fh.read()
    img_parser = ImgHtmlParser()
    img_parser.feed(html)
    assert img_parser.has_img_src(
        '../_images/images-1.png')
    a_parser = ReferenceExternalHtmlParser()
    a_parser.feed(html)
    assert a_parser.has_href('../images-1.py')
    assert a_parser.has_href('../images-1.png')
    assert a_parser.has_href('../images-1.hires.png')
    assert a_parser.has_href('../images-1.pdf')


@pytest.mark.sphinx('html', testroot='example-gallery')
def test_includes(app, status, warning):
    """Test resolution of includes-based items in examples.
    """
    app.verbosity = 2
    logging.setup(app, status, warning)
    app.builder.build_all()
    print(app.outdir)

    # A regular image directive with a relative URI to a local image.
    path = app.outdir / 'examples/example-using-the-include-directive.html'
    with open(path) as fh:
        html = fh.read()
    parser = ParagraphHtmlParser()
    parser.feed(html)
    assert parser.has_p_starting_with(
        'This is sample content from a file')

    # A regular image directive with a relative URI to a local image.
    path = app.outdir / 'examples/literalinclude-example.html'
    with open(path) as fh:
        html = fh.read()
    parser = PreTagHtmlParser()
    parser.feed(html)
    assert parser.pre_count == 1

    # An internal download reference
    path = app.outdir / 'examples/file-download-example.html'
    with open(path) as fh:
        html = fh.read()
    parser = ReferenceDownloadHtmlParser()
    parser.feed(html)
    assert parser.has_href_endswith('hello.py')

    # An absolute internal download reference
    path = app.outdir / 'examples/absolute-file-download-example.html'
    with open(path) as fh:
        html = fh.read()
    parser = ReferenceDownloadHtmlParser()
    parser.feed(html)
    assert parser.has_href_endswith('astropy_project_logo.svg')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="Example contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
@pytest.mark.sphinx('html', testroot='example-gallery')
def test_external_downloads(app, status, warning):
    """Test a download role pointing to external content.
    """
    app.verbosity = 2
    logging.setup(app, status, warning)
    app.builder.build_all()
    print(app.outdir)

    # An external download reference
    path = app.outdir / 'examples/external-file-download-example.html'
    with open(path) as fh:
        html = fh.read()
    parser = ReferenceDownloadHtmlParser()
    parser.feed(html)
    assert parser.has_href(
        'https://raw.githubusercontent.com/astropy/astropy/master/README.rst')


class ReferenceExternalHtmlParser(HTMLParser):
    """HTML Parser that specifically parses for Sphinx's external
    reference link.

    Internal reference links have a class ``reference external``. The `links`
    attribute is a list of such links, which are represented as a dictionary
    of their attributes.
    """

    def __init__(self, *args, **kwargs):
        self.links = []
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrdict = {a[0]: a[1] for a in attrs if len(a) == 2}
            try:
                if 'reference external' in attrdict['class']:
                    # matches
                    self.links.append(attrdict)
            except KeyError:
                pass

    def has_href(self, href):
        """Test if a link with a particular href is in the parsed HTML.
        """
        for link in self.links:
            if link['href'] == href:
                return True
        return False


class ReferenceInternalHtmlParser(HTMLParser):
    """HTML Parser that specifically parses for Sphinx's internal
    reference link.

    Internal reference links have a class ``reference internal``. The `links`
    attribute is a list of such links, which are represented as a dictionary
    of their attributes.
    """

    def __init__(self, *args, **kwargs):
        self.links = []
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrdict = {a[0]: a[1] for a in attrs if len(a) == 2}
            try:
                if 'reference internal' in attrdict['class']:
                    # matches
                    self.links.append(attrdict)
            except KeyError:
                pass

    def has_href(self, href):
        """Test if a link with a particular href is in the parsed HTML.
        """
        for link in self.links:
            if link['href'] == href:
                return True
        return False


class ImgHtmlParser(HTMLParser):
    """HTML Parser that specifically parses for ``img`` tags.
    """

    def __init__(self, *args, **kwargs):
        self.imgs = []
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            attrdict = {a[0]: a[1] for a in attrs if len(a) == 2}
            self.imgs.append(attrdict)

    def has_img_src(self, uri):
        """Test if an image is present based on its URI.
        """
        for img in self.imgs:
            if img['src'] == uri:
                return True
        return False


class ParagraphHtmlParser(HTMLParser):
    """HTML Parser that specifically parses for ``p`` tags.
    """

    def __init__(self, *args, **kwargs):
        self.paragraphs = []
        self.open_tag = False
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            attrdict = {a[0]: a[1] for a in attrs if len(a) == 2}
            self.paragraphs.append({'tag': attrdict, 'content': None})
            self.open_tag = True

    def handle_data(self, data):
        if self.open_tag:
            self.paragraphs[-1]['content'] = data
            self.open_tag = False

    def has_p_starting_with(self, content):
        """Test if a paragraph exists that begins with the given content.
        """
        for p in self.paragraphs:
            if p['content'].startswith(content):
                return True
        return False


class PreTagHtmlParser(HTMLParser):
    """HTML Parser that counts ``pre`` tags.
    """

    def __init__(self, *args, **kwargs):
        self.pre_count = 0
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.pre_count += 1


class ReferenceDownloadHtmlParser(HTMLParser):
    """HTML Parser that specifically parses for Sphinx's ``reference download``
    links.

    Internal reference links have a class ``reference internal``. The `links`
    attribute is a list of such links, which are represented as a dictionary
    of their attributes.
    """

    def __init__(self, *args, **kwargs):
        self.links = []
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrdict = {a[0]: a[1] for a in attrs if len(a) == 2}
            try:
                if 'reference download' in attrdict['class']:
                    # matches
                    self.links.append(attrdict)
            except KeyError:
                pass

    def has_href(self, href):
        """Test if a link with a particular href is in the parsed HTML.
        """
        for link in self.links:
            if link['href'] == href:
                return True
        return False

    def has_href_endswith(self, path):
        for link in self.links:
            if link['href'].endswith(path):
                return True
        return False
