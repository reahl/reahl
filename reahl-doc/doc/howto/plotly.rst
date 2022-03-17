.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Chart| replace:: :class:`~reahl.web.plotly.Chart`


Display a Plotly.py Figure
==========================

.. sidebar:: Examples in this section

   - howtos.graphplotly

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Writing a library to compose and render Charts is a complicated job in its own right. For this reason Reahl
does not attempt to do this job itself.

Using the `Plotly Python library <https://github.com/plotly/plotly.py/>`_ (which has its own extensive documentation)
you can construct Charts, called Figures in `Plotly`.

Here is an example of a line chart:

.. literalinclude:: ../../reahl/doc/examples/howtos/chartplotly/chartplotly.py
   :pyobject: GraphPage.create_line_chart_figure

Here is an example of a bar chart:

.. literalinclude:: ../../reahl/doc/examples/howtos/chartplotly/chartplotly.py
   :pyobject: GraphPage.create_bar_chart_figure

Such a Figure is then simply wrapped by a |Chart| to include it on a page:

.. literalinclude:: ../../reahl/doc/examples/howtos/chartplotly/chartplotly.py

