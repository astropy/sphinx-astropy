master_doc = 'index'  # for Sphinx <2.0
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'numpydoc',
    'sphinx_astropy.ext.example'
]
exclude_patterns = ['_build']
suppress_warnings = ['app.add_directive', 'app.add_node']
default_role = 'obj'
