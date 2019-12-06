####################################
Using the Astropy Examples extension
####################################

Your Sphinx documentation pages might contain a lot of information: overviews, examples, how-tos, and references.
Embedded within your documentation pages might be useful standalone content.
This content makes sense in the flow of your existing documentation, but it might also get lost.
The ``sphinx_astropy.ext.example`` extension helps you to resurface content into standalone, easily discovered, pages.

With this extension, all you need to do to create a standalone example is mark it up with an ``example`` directive, give it a title, and optionally tag it.
The extension will:

- Generate an HTML page for each example with a copy of the example's content from the original documentation page.
- Generate an index of all the examples.
- Generate an index page for each unique tag.

This page describes how to set up ``sphinx_astropy.ext.example`` for your Sphinx project and mark up examples.

How to add ``sphinx_astropy.ext.example`` to a Sphinx project
=============================================================

Basic configuration
-------------------

You will need to configure this extension in your Sphinx project's :file:`conf.py` file.

First, add this extension to the ``extensions`` list:

.. code-block:: python

   python
   extensions = [
       'sphinx_astropy.ext.example`
   ]

.. note::

   If you are using Astropy's default configuration, `sphinx_astropy.conf.v1`, this is already done for you.

Configuring the gallery
-----------------------

By default, ``sphinx_astropy.ext.example`` won't generate an example gallery.
This lets you mark up examples in your existing documentation without affecting your Sphinx build.
Once you decide to publish a gallery of your examples, you can follow these steps:

1. In your :file:`conf.py` file, activate the gallery generation feature:

   .. code-block:: python

      astropy_examples_enabled = True

2. Review the directory, relative to the site root, where you want the example gallery to be located.
   The default is ``examples``, but you can update this in your :file:`conf.py` file:

   .. code-block:: python

      astropy_examples_dir = 'examples'

3. Add the :file:`index.rst` page of the example gallery to a ``toctree`` on your site.
   Given the default value of ``astropy_examples_dir``, the ``toctree`` on the :file:`index.rst` of your Sphinx project should look like:

   .. code-block:: rst

      .. toctree::

         examples/index

4. Add the ``astropy_examples_dir`` to your :file:`.gitignore` file, or equivalent, so that they aren't committed to version control.
   The extension takes care of generating these source files for you.
5. If your Sphinx project has a cleanup command, such as in a :file:`Makefile`, consider adding the ``astropy_examples_dir`` to the directories that are deleted when your Sphinx build is cleaned up.

How to mark up examples
=======================

To create an example in your reStructuredText documentation, enclose that content within an ``example`` directive:

.. code-block:: rst

   Content *before* an example.

   .. example:: Title of the Example
      :tags: tag1, tag2, tag3

      This is the content of the example.

      Any reStructuredText is allowed:

      - lists,
      - code blocks
      - images
      - equations

   Content *after* an example.

When that documentation page is rendered, it will look as if ``example`` directive never existed.
But all the content within the ``example`` directive is copied into its own page in the example gallery.

Every example must have a title. This title must be unique across the entire documentation site.

Examples can optionally have one or more tags pass as arguments to a ``:tags:`` field.
These tags are comma-delimited.

Tips for marking up examples
----------------------------

- Don't overlap example directives.
  An example can't include another example.

- You can include headings and subsections in examples.
  Stick to a heading hierarchy though.
  Don't start with a sub-subsection and also include the subsequent subsection.

- Ensure that each example has a unique title.
  If they aren't, the Sphinx build will fail.
