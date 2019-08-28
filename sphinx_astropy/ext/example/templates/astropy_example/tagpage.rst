:orphan:

{{ title | h1underline }}
{% for example in tag.example_pages %}
- :doc:`{{ example.source.title }} <{{ example.abs_docname }}>`
{%- for tag_page in example.tag_pages %}
  {% if loop.first %}({% endif %}:doc:`{{ tag_page.name }} <{{ tag_page.abs_docname }}>`{% if not loop.last %},{% else %}){% endif %}
{%- endfor %}
{%- endfor %}
