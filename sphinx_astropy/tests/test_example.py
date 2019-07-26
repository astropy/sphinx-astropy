# Licensed under a 3-clause BSD style license - see LICENSE.rst

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

from sphinx_astropy.ext.example import purge_examples, merge_examples
from sphinx_astropy.ext.example.marker import (
    format_title_to_example_id, format_title_to_source_ref_id)


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
def test_event_connections(app, status, warning):
    assert purge_examples in app.events.listeners['env-purge-doc'].values()
    assert merge_examples in app.events.listeners['env-merge-info'].values()


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
