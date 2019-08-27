{{ "Example gallery" | escape | h1underline}}

.. hidden toctree for Sphinx navigation

.. toctree::
   :hidden:
{% for example in example_pages %}
   {{ example.rel_docname }}
{%- endfor %}

.. Listing for styling (eventually will become a tiled grid)
{% for example in example_pages %}
- :doc:`{{ example.source.title }} <{{ example.rel_docname }}>`
{%- endfor %}
