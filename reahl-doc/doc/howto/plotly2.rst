.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Chart| replace:: :class:`~reahl.web.plotly.charts.Chart`


Interacting with Plotly |Chart|
===============================

.. sidebar:: Examples in this section

   - howtos.graphplotly2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


This example shows how to change a Plotly |Chart| when a user changes |Input|\s that affect it. The example assumes
you already understand :doc:`the basics of Charts <plotly>` as well as :doc:`how to refresh Widgets in response to
user interaction <refreshingwidgets>`.

The example displays a line graph with two lines. One of the lines changes its values
based on a factor, which the user can select from a |SelectInput|.

Add a |Field| on `ChartForm` to keep track of the `factor`:

.. literalinclude:: ../../reahl/doc/examples/howtos/plotly2/plotly2.py
   :pyobject: ChartForm.fields

Create a |SelectInput| to allow the user to change the `factor`.
Only after constructing the |SelectInput| will the `factor` attribute be set on the `ChartForm`. Create the Figure
(which depends on the `factor` attribute) after creation of the |SelectInput|.

Then only create the |Chart|, and lastly, call |set_refresh_widget| to make the |SelectInput| change the |Chart|.

.. note::
   Refreshing only the |contents| of the |Chart| updates the screen faster.

.. literalinclude:: ../../reahl/doc/examples/howtos/plotly2/plotly2.py
   :pyobject: ChartForm



