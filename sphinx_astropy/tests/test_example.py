# Licensed under a 3-clause BSD style license - see LICENSE.rst

from xml.etree.ElementTree import tostring

from docutils import nodes
import pytest
from sphinx.testing.util import etree_parse
from sphinx.util import logging
from sphinx.errors import SphinxError

# Sphinx pytest fixtures only available in Sphinx 1.7+
pytest.importorskip("sphinx", minversion="1.7")


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
        'example-src-example-with-two-paragraphs',
        'example-src-tagged-example',
        'example-src-example-with-multiple-tags',
        'example-src-example-with-subsections'
    ]
    for k in known_examples:
        assert k in examples

    # Test tags
    assert examples['example-src-example-with-two-paragraphs']['tags'] == set()
    assert examples['example-src-tagged-example']['tags'] == set(['tag-a'])
    assert examples['example-src-example-with-multiple-tags']['tags'] \
        == set(['tag-a', 'tag-b'])

    ex = examples['example-src-example-with-two-paragraphs']

    # Test title
    assert ex['title'] == 'Example with two paragraphs'

    # Test docname
    assert ex['docname'] == 'example-marker'

    # Test content
    assert str(ex['content'][0]) == 'This is the first paragraph.'
    assert str(ex['content'][1]) == ''
    assert str(ex['content'][2]) == 'And the second paragraph.'


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
    assert 'example-src-using-example-func' in examples

    # Check that the reference target got added to the API reference
    et = etree_parse(app.outdir / 'example_func.xml')
    print(tostring(et.getroot(), encoding='unicode'))
    targets = et.getroot().findall('.//target')
    refids = [t.attrib['refid'] for t in targets]
    assert 'example-src-using-example-func' in refids
