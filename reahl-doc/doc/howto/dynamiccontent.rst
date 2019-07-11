.. Copyright 2019 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |HTMLElement| replace:: :class:`~reahl.web.ui.HTMLElement`
.. |TextInput| replace:: :class:`~reahl.web.bootstrap.forms.TextInput`
.. |Event| replace:: :class:`~reahl.component.modelinterface.Event`
.. |Action| replace:: :class:`~reahl.component.modelinterface.Action`
.. |enable_refresh| replace:: :meth:`~reahl.web.ui.HTMLElement.enable_refresh`

Dynamically changing page content
=================================

.. sidebar:: Examples in this section

   - howtos.dynamiccontent

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Dishing out money
-----------------

You can make parts of your page refresh in response to having changed the value of an input.

This example is a page on which you choose how to divide an amount you want to invest into two different funds:

.. figure:: ../_build/screenshots/dynamiccontent_1.png
   :align: center
   :alt: AllocationDetailForm.

You enter the total amount, and then the percentage allocated to each fund. Each time you tab out of a 
percentage input, the amount portion next to it and the totals at the bottom of the table are recalculated.

.. figure:: ../_build/screenshots/dynamiccontent_2.png
   :align: center
   :alt: AllocationDetailForm with totals and amounts recalculated.

You can also change the total amount or elect to rather specify portions as amounts instead of percentages.

.. figure:: ../_build/screenshots/dynamiccontent_3.png
   :align: center
   :alt: AllocationDetailForm specified in amount.


Make an |HTMLElement| refreshable
---------------------------------

You make an |HTMLElement| (AllocationDetailForm in this example) refreshable by calling |enable_refresh| on it:

.. literalinclude:: ../../reahl/doc/examples/howtos/dynamiccontent/dynamiccontent.py
   :pyobject: AllocationDetailForm.__init__

A |TextInput| will trigger a refresh of the |HTMLElement| passed as its `refresh_widget`.

.. literalinclude:: ../../reahl/doc/examples/howtos/dynamiccontent/dynamiccontent.py
   :pyobject: AllocationDetailForm.add_allocation_controls

Recalculate
-----------

.. note:: The values you recalculate must be attributes of persisted model objects.

Specify an `on_refresh` |Event| in your |enable_refresh| call to trigger a recalculate |Action|:

.. literalinclude:: ../../reahl/doc/examples/howtos/dynamiccontent/dynamiccontent.py
   :pyobject: AllocationDetailForm.__init__
   :start-after: self.investment_order = 
   :end-before: self.add_allocation_controls()

.. literalinclude:: ../../reahl/doc/examples/howtos/dynamiccontent/dynamiccontent.py
   :pyobject: InvestmentOrder.events
   
.. literalinclude:: ../../reahl/doc/examples/howtos/dynamiccontent/dynamiccontent.py
   :pyobject: InvestmentOrder.recalculate

