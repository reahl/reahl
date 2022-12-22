.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Chart| replace:: :class:`~reahl.web.plotly.Chart`
.. |contents| replace:: :attr:`~reahl.web.plotly.Chart.contents`
.. |Input| replace:: :class:`~reahl.web.ui.Input`
.. |SelectInput| replace:: :class:`~reahl.web.ui.SelectInput`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |set_refresh_widgets| replace:: :meth:`~reahl.web.ui.PrimitiveInput.set_refresh_widgets`

Interacting with Plotly |Chart|
===============================

.. sidebar:: Examples in this section

   - howtos.graphplotly2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


This example shows how to change a Plotly |Chart| when a user changes an |Input| that affect it. The example assumes
you already understand :doc:`the basics of Charts <plotly>` as well as :doc:`how to refresh Widgets in response to
user interaction <refreshingwidgets>`.

The example displays a line graph with two lines. One of the lines changes its values
based on a factor, which the user can select from a |SelectInput|.

Add a |Field| on `ChartForm` to keep track of the `factor`:

.. literalinclude:: ../../reahl/doc/examples/howtos/chartplotly2/chartplotly2.py
   :start-at: fields =
   :end-at: fields.factor = 

The `factor` attribute of `ChartForm` will only be updated in response to user changes once an |Input| is created for it.

This means that you first initialise `factor`, then create the |SelectInput| to possibly update the default value of `factor`.
After the creation of the |SelectInput|, create the |Chart| (which uses `factor`).
Lastly, call |set_refresh_widgets| to make the |SelectInput| change the contents of the |Chart|:

.. note::
   Refreshing only the |contents| of the |Chart| instead of the entire |Chart| updates the screen faster.

.. literalinclude:: ../../reahl/doc/examples/howtos/chartplotly2/chartplotly2.py
   :pyobject: ChartForm.__init__

Here is the entire example:

.. literalinclude:: ../../reahl/doc/examples/howtos/chartplotly2/chartplotly2.py
   :pyobject: ChartForm



