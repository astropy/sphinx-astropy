import matplotlib.sphinxext.plot_directive

master_doc = 'index'  # for Sphinx <2.0
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'numpydoc',
    matplotlib.sphinxext.plot_directive.__name__,
    'sphinx_astropy.ext.doctest',
    'sphinx_astropy.ext.example'
]
exclude_patterns = ['_build', '_includes']
suppress_warnings = ['app.add_directive', 'app.add_node']
default_role = 'obj'
intersphinx_mapping = {
    'astropy': ('https://docs.astropy.org/en/stable/', None),
}
astropy_examples_enabled = True
