# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Tests for the sphinx_astropy.ext.example extension.

These tests are organized into three basic types:

1. Unit tests that don't depend on a Sphinx build.
2. Unit tests that use the ``sphinx`` pytest mark. These tests operate on
   the Sphinx application instance after a build and test environment
   persistence.
3. Tests that run a Sphinx build through its command-line interface and
   analyze the resulting HTML product.
"""

import os.path
import re
import shutil
from xml.etree.ElementTree import tostring

import pytest

# Sphinx pytest fixtures only available in Sphinx 1.7+
pytest.importorskip("sphinx", minversion="1.7")  # noqa E402

from bs4 import BeautifulSoup
import sphinx
from sphinx.testing.util import etree_parse
from sphinx.util import logging
from sphinx.cmd.build import build_main

from sphinx_astropy.ext.example.marker import (
    format_title_to_example_id, format_title_to_source_ref_id,
    ExampleMarkerNode)
from sphinx_astropy.ext.example.preprocessor import (
    detect_examples, preprocess_examples)
from sphinx_astropy.ext.example.examplepages import (
    ExamplePage, ExampleContentNode)
from sphinx_astropy.ext.example.templates import Renderer
from sphinx_astropy.ext.example.utils import (
    is_directive_registered, is_node_registered)

sphinx_version = sphinx.version_info[:2]


# ============================================================================
# Unit tests (independent of a Sphinx build) =================================
# ============================================================================

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


# ============================================================================
# Tests with sphinx pytest mark (operation on Sphinx application instance) ===
# ============================================================================

@pytest.mark.sphinx('html', testroot='example-gallery')
def test_app_setup(app, status, warning):
    """Test that event callbacks, directives, and nodes got added to the
    Sphinx app.
    """
    # Check event callbacks
    listeners = app.events.listeners
    assert preprocess_examples in listeners['builder-inited'].values()

    # Check registered configs
    assert 'astropy_examples_dir' in app.config
    assert 'astropy_examples_enabled' in app.config

    # Check registered directives
    assert is_directive_registered('example')
    assert is_directive_registered('example-content')

    # Check registered nodes
    assert is_node_registered(ExampleMarkerNode)
    assert is_node_registered(ExampleContentNode)


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
    """Test that the examples are added to the app env by
    `sphinx_astropy.ext.example.preprocessor.cache_examples`.
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

    # Test docnames
    assert ex['source_docname'] == 'example-marker'
    assert ex['docname'] == 'examples/example-with-two-paragraphs'

    # Test paths
    assert ex['source_path'].endswith('example-marker.rst')
    assert os.path.exists(ex['source_path'])
    assert ex['path'].endswith('example-with-two-paragraphs.rst')
    assert os.path.exists(ex['path'])


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
                                 "'example-marker', tags={'tag-a'})")

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
        '   internally-defined-substitution\n'
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
        '- :doc:`Internally defined substitution <internally-defined-substitution>`\n'
        '  (:doc:`substitutions </examples/tags/substitutions>`)\n'
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


# ============================================================================
# Test that operate on a Sphinx build through its CLI ========================
# ============================================================================

@pytest.fixture(scope="session")
def example_gallery_build(tmpdir_factory, rootdir):
    """Test fixture that builds the example-gallery test case with a
    parallelized build.
    """
    case_dir = str(rootdir / 'test-example-gallery')
    src_dir = str(tmpdir_factory.mktemp('example-gallery').join('docs'))
    shutil.copytree(case_dir, src_dir)

    argv = ['-j 4', '-W', '-b', 'html', src_dir, '_build/html']

    start_dir = os.path.abspath('.')
    try:
        os.chdir(src_dir)
        status = build_main(argv=argv)
    finally:
        os.chdir(start_dir)
    assert status == 0

    return src_dir, os.path.join(src_dir, '_build/html'), status


@pytest.fixture(scope="session")
def example_gallery_duplicates_build(tmpdir_factory, rootdir):
    """Test fixture that builds the example-gallery-duplicates test case
    where an example is duplicated.

    This build should fail
    """
    case_dir = str(rootdir / 'test-example-gallery-duplicates')
    src_dir = str(tmpdir_factory.mktemp('example-gallery-duplicates').join('docs'))
    shutil.copytree(case_dir, src_dir)

    argv = ['-j 4', '-W', '-b', 'html', src_dir, '_build/html']

    start_dir = os.path.abspath('.')
    try:
        os.chdir(src_dir)
        status = build_main(argv=argv)
    finally:
        os.chdir(start_dir)
    assert status != 0

    return src_dir, os.path.join(src_dir, '_build/html'), status


@pytest.fixture(scope="session")
def example_gallery_disabled_build(tmpdir_factory, rootdir):
    """Test fixture that builds a site where example gallery generation is
    disabled through the ``astropy_examples_enabled`` configuration.
    """
    case_dir = str(rootdir / 'test-example-gallery-disabled')
    src_dir = str(tmpdir_factory.mktemp('example-gallery-disabled').join('docs'))
    shutil.copytree(case_dir, src_dir)

    argv = ['-j 4', '-W', '-b', 'html', src_dir, '_build/html']

    start_dir = os.path.abspath('.')
    try:
        os.chdir(src_dir)
        status = build_main(argv=argv)
    finally:
        os.chdir(start_dir)
    assert status == 0

    return src_dir, os.path.join(src_dir, '_build/html'), status


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="Example contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_example_gallery_build(example_gallery_build):
    """Test the overall build status code for the example-gallery case.
    """
    _, _, status = example_gallery_build
    assert status == 0


def test_example_gallery_duplicates_build(example_gallery_duplicates_build):
    """Test the overall build status code for the example-gallery-duplicates
    case.

    This build is expected to fail (non-zero status) because there are examples
    with the same title, which is disallowed.
    """
    _, _, status = example_gallery_duplicates_build
    assert status != 0


def test_example_gallery_disabled_build(example_gallery_disabled_build):
    """Test the overall build status code for the example-gallery-disabled
    case.
    """
    _, _, status = example_gallery_disabled_build
    assert status == 0


def parse_example_page(example_build, example_id):
    """Parse an HTML page of a standalone example from an example site build.
    """
    _, html_dir, _ = example_build
    path = os.path.join(html_dir, 'examples', '{}.html'.format(example_id))
    with open(path) as f:
        soup = BeautifulSoup(f, 'html.parser')
    return soup


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_api_link(example_gallery_build):
    """Test that the API link in the api-link example got resolved correctly
    with a relative URL.
    """
    soup = parse_example_page(example_gallery_build, 'api-link')
    assert contains_href(
        soup,
        "../example_func.html"
        "#sphinx_astropy.tests.example_module.example.example_func"
    )


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_ref_link(example_gallery_build):
    """The ref-link example has an example of a link made with the ref role.
    """
    soup = parse_example_page(example_gallery_build, 'ref-link')
    assert contains_href(soup, '../example-marker.html#example-link-target')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_doc_link(example_gallery_build):
    """The doc-link example has a doc role for making a link to another page.
    """
    soup = parse_example_page(example_gallery_build, 'doc-link')
    assert contains_href(soup, '../example-marker.html')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_intersphinx_ref_link(example_gallery_build):
    """The intersphinx-ref-link example has a ref role to the Astropy
    docs with intersphinx
    """
    soup = parse_example_page(example_gallery_build, 'intersphinx-ref-link')
    assert contains_href(
        soup,
        'https://docs.astropy.org/en/stable/wcs/index.html#astropy-wcs',
        selector='.body a.reference.external'
    )


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_intersphinx_api_link(example_gallery_build):
    """The intersphinx-api-link example has a ref role to the Astropy
    docs with intersphinx.
    """
    soup = parse_example_page(example_gallery_build, 'intersphinx-api-link')
    expected_href = (
        'https://docs.astropy.org/en/stable/api/astropy.table.Table.html'
        '#astropy.table.Table'
    )
    for atag in soup.select('.body a.reference.external'):
        if atag['href'] == expected_href:
            return
    assert False  # didn't find the expected link


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_header_reference_target(example_gallery_build):
    """The header-reference-target-example example has an example of a ref
    link to a target on a header that's also part of the example content.
    This shows that the link ends up pointing back to the original.
    """
    soup = parse_example_page(example_gallery_build,
                              'header-reference-target-example')
    # ref link inside the scope of the example
    assert contains_href(soup, '#section-target')
    # ref link outside the scope of the example
    assert contains_href(soup, '../ref-targets.html#section-2-target')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="Named equations do not work with Sphinx 1.7.")
def test_named_equation(example_gallery_build):
    """The named-equation example has an example of a an equation with a
    label, and a reference to that label.
    This shows that the link points back to the original equation.
    """
    soup = parse_example_page(example_gallery_build, 'named-equation')
    assert contains_href(soup, '#equation-euler')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_example_with_an_image(example_gallery_build):
    """A regular image directive with a relative URI to a local image.
    """
    soup = parse_example_page(example_gallery_build,
                              'example-with-an-image')
    assert contains_linked_img(
        soup,
        '../_images/astropy_project_logo.svg')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_example_with_an_external_image(example_gallery_build):
    """A regular image directive with an external URI.
    """
    soup = parse_example_page(example_gallery_build,
                              'example-with-an-external-image')
    assert contains_linked_img(
        soup,
        'https://www.astropy.org/images/astropy_project_logo.svg')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_example_with_a_figure(example_gallery_build):
    """A figure directive with a relative URI to a local image.
    """
    soup = parse_example_page(example_gallery_build,
                              'example-with-a-figure')
    assert contains_linked_img(
        soup,
        '../_images/astropy_project_logo.svg')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_example_with_an_external_figure(example_gallery_build):
    """A figure directive with a external image URI.
    """
    soup = parse_example_page(example_gallery_build,
                              'example-with-an-external-figure')
    assert contains_linked_img(
        soup,
        'https://www.astropy.org/images/astropy_project_logo.svg')


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_matplotlib_plot(example_gallery_build):
    """A matplotlib-based plot directive.
    """
    soup = parse_example_page(example_gallery_build, 'matplotlib-plot')

    assert contains_external_href(soup, '../images-1.py')
    assert contains_external_href(soup, '../images-1.png')
    assert contains_external_href(soup, '../images-1.hires.png')
    assert contains_external_href(soup, '../images-1.pdf')

    img_tag = soup.select('.body img')[0]
    assert img_tag['src'] == '../_images/images-1.png'


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_include_directive(example_gallery_build):
    """Test an example with content brought in from an include directive.
    """
    soup = parse_example_page(example_gallery_build,
                              'example-using-the-include-directive')
    for tag in soup.select('.body p'):
        print(tag)
        if tag.text.startswith('This is sample content from a file'):
            return
    assert False  # expected content was not found


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_literalinclude_directive(example_gallery_build):
    """Test code inserted with a literalinclude directive.
    """
    soup = parse_example_page(example_gallery_build,
                              'literalinclude-example')
    tags = soup.select('.body pre')
    assert len(tags) == 1


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_file_download_example(example_gallery_build):
    """Test the link made by a download directive to a file hosted on the
    site itself.
    """
    soup = parse_example_page(example_gallery_build,
                              'file-download-example')
    for tag in soup.select('.body a.reference.download.internal'):
        match = re.match(
            r'../_downloads/[a-z0-9]+/hello\.py',
            tag['href']
        )
        if match is not None:
            return
    assert False  # link was not found


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_absolute_file_download_example(example_gallery_build):
    """Test an absolute link to a file hosted on the site, made with a download
    directive.
    """
    soup = parse_example_page(example_gallery_build,
                              'absolute-file-download-example')
    for tag in soup.select('.body a.reference.download.internal'):
        match = re.match(
            r'../_downloads/[a-z0-9]+/astropy_project_logo\.svg',
            tag['href']
        )
        if match is not None:
            return
    assert False  # link was not found


@pytest.mark.skipif(
    sphinx_version <= (1, 7),
    reason="example-gallery site contains download role with external URL "
           "that is not supported by Sphinx 1.7.")
def test_external_file_download_example(example_gallery_build):
    """Test an absolute link to a file hosted on the site, made with a download
    directive.
    """
    soup = parse_example_page(example_gallery_build,
                              'external-file-download-example')
    expected_href = (
        'https://raw.githubusercontent.com/astropy/astropy/master/README.rst')
    for tag in soup.select('.body a.reference.download.external'):
        if tag['href'] == expected_href:
            return
    assert False  # link was not found


def contains_href(soup, expected_href, selector='.body a.reference.internal'):
    """Test if a BeautifulSoup tree contains an ``<a>`` with an expected
    href (optimized for Sphinx links with a ``reference internal`` class).

    Parameters
    ----------
    soup : BeautifulSoup
        HTML content of a Sphinx page, parsed by BeautifulSoup.
    expected_href : str
        The expected href value of a tag on the page.
    selector : str
        The CSS selector for finding tags that might contain the expected href.
        The default selector is optimized to find ``<a>`` tags in the body of
        a Sphinx page with a ``reference internal``. For example, links
        made using the ``ref`` and ``doc`` roles.

    Returns
    -------
    contains : bool
        `True` if the link is found, `False` otherwise.
    """
    for atag in soup.select(selector):
        if atag['href'] == expected_href:
            return True
    return False


def contains_external_href(soup, expected_href,
                           selector='.body a.reference.external'):
    """Test if a BeautifulSoup tree contains an ``<a>`` with an expected
    href (optimized for Sphinx links with a ``reference external`` class).

    Parameters
    ----------
    soup : BeautifulSoup
        HTML content of a Sphinx page, parsed by BeautifulSoup.
    expected_href : str
        The expected href value of a tag on the page.
    selector : str
        The CSS selector for finding tags that might contain the expected href.
        The default selector is optimized to find ``<a>`` tags in the body of
        a Sphinx page with a ``reference internal``. For example, links
        made using intersphinx to other projects.

    Returns
    -------
    contains : bool
        `True` if the link is found, `False` otherwise.
    """
    return contains_href(soup, expected_href, selector=selector)


def contains_linked_img(soup, expected_src,
                        selector='.body a.image-reference'):
    """Test if a BeautifulSoup tree contains an ``img`` tag with the expected
    src attribute that's also wrapped in an ``a`` tag.

    Parameters
    ----------
    soup : BeautifulSoup
        HTML content of a Sphinx page, parsed by BeautifulSoup.
    expected_src : str
        The expected src value of an ``img`` tag on the page (and the href
        value of the wrapping ``a`` tag).
    selector : str
        The CSS selector for finding ``<a>`` tags that wrap an image.

    Returns
    -------
    contains : bool
        `True` if the linked image is found, `False` otherwise.
    """
    for atag in soup.select(selector):
        # Check the href of both the <a> tag and the src of the <img> itself
        if atag['href'] == expected_src and atag.img['src'] == expected_src:
            return True
    return False
