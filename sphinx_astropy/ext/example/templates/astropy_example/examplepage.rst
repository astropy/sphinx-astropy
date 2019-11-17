{%- if has_doctestskipall %}
.. doctest-skip-all
{%- endif %}

{{ title | escape | h1underline}}

From :doc:`{{ example.abs_docname }}`.
{%- if tag_pages %}
Tagged:
{%- for tag_page in tag_pages %}
:doc:`{{ tag_page.name }} <{{ tag_page.abs_docname }}>`{% if not loop.last %},{% else %}.{% endif %}
{%- endfor %}
{%- endif %}

.. example-content:: {{ example.example_id }}
