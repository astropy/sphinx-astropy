master_doc = 'index'  # for Sphinx <2.0
extensions = [
    'sphinx.ext.autodoc',
    'numpydoc',
    'sphinx_astropy.ext.example'
]
exclude_patterns = ['_build']
suppress_warnings = ['app.add_directive', 'app.add_node']
