Image-based examples
====================

:ref:`A link to the figure <logo-figure>`.

.. example:: Example with an image
   :tags: images

   .. image:: astropy_project_logo.svg
      :width: 300px

.. example:: Example with an external image
   :tags: images

   .. image:: https://www.astropy.org/images/astropy_project_logo.svg
      :width: 300px

.. example:: Example with a figure
   :tags: images

   .. figure:: astropy_project_logo.svg
      :width: 300px
      :name: logo-figure

      Figure caption.

.. example:: Example with an external figure
   :tags: images

   .. figure:: https://www.astropy.org/images/astropy_project_logo.svg
      :width: 300px
      :name: external-logo-figure

      Figure caption.

.. example:: Matplotlib plot
   :tags: images

   .. plot::

      import matplotlib
      import matplotlib.pyplot as plt
      import numpy as np

      # Data for plotting
      x = [1., 2., 3.]
      y = [2., 4., 9.]

      fig, ax = plt.subplots()
      ax.plot(x, y)

      ax.set(xlabel='x', ylabel='y',
             title='Matplotlib plot')
      ax.grid()
