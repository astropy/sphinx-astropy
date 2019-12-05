Reference targets demo
======================

This page demonstrates examples that contain reference targets.
The standalone versions of these examples need to be stripped of these reference targets.

.. example:: Header reference target example
   :tags: reference target

   This example includes section headers with reference targets.

   .. _section-target:

   Section title
   -------------

   Contents of the section.

   Link to the header: :ref:`section-target`.

   Link to a header outside the example: :ref:`section-2-target`.

A ``ref`` link: :ref:`section-target` outside the example.

.. _section-2-target:

Example of a named equation
---------------------------

.. example:: Named equation
   :tags: reference target

   .. math:: e^{i\pi} + 1 = 0
      :label: euler

   The Euler equation :math:numref:`euler`.
