:orphan:

{{ title | h1underline }}
{% for example in tag.example_pages %}
- :doc:`{{ example.source.title }} <{{ example.abs_docname }}>`
{%- endfor %}
