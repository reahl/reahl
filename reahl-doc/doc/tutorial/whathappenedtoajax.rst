.. Copyright 2013, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |HTMLElement| replace:: :class:`~reahl.web.ui.HTMLElement`
.. |TextInput| replace:: :class:`~reahl.web.bootstrap.forms.TextInput`
.. |Event| replace:: :class:`~reahl.component.modelinterface.Event`
.. |Action| replace:: :class:`~reahl.component.modelinterface.Action`
.. |DomainException| replace:: :class:`~reahl.component.exceptions.DomainException`
.. |enable_refresh| replace:: :meth:`~reahl.web.ui.HTMLElement.enable_refresh`


Changing content without refreshing (Ajax)
==========================================

.. sidebar:: Examples in this section

   - tutorial.dynamiccontent

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

.. seealso:: 

   - :doc:`../howto/dynamiccontenterrors`
   - :doc:`../howto/refreshingwidgets`
   - :doc:`../howto/paginglonglists`
   - :doc:`../howto/responsivedisclosure`


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

.. literalinclude:: ../../reahl/doc/examples/tutorial/dynamiccontent/dynamiccontent.py
   :pyobject: AllocationDetailForm.__init__

A |TextInput| will trigger a refresh of the |HTMLElement| passed as its `refresh_widget`.

.. literalinclude:: ../../reahl/doc/examples/tutorial/dynamiccontent/dynamiccontent.py
   :pyobject: AllocationDetailForm.add_allocation_controls

Recalculate
-----------

.. note:: The values you recalculate must be attributes of persisted model objects.

Specify an `on_refresh` |Event| in your |enable_refresh| call to trigger a recalculate |Action|:

.. literalinclude:: ../../reahl/doc/examples/tutorial/dynamiccontent/dynamiccontent.py
   :pyobject: AllocationDetailForm.__init__
   :start-after: self.investment_order = 
   :end-before: self.add_allocation_controls()

.. literalinclude:: ../../reahl/doc/examples/tutorial/dynamiccontent/dynamiccontent.py
   :start-at: events =
   :end-at: events.allocation_changed =
   
.. literalinclude:: ../../reahl/doc/examples/tutorial/dynamiccontent/dynamiccontent.py
   :pyobject: InvestmentOrder.recalculate


Validating results
------------------

When the user finally submits the InvestmentOrder, recalculate the order before validating 
the newly recalculated results. 

.. literalinclude:: ../../reahl/doc/examples/tutorial/dynamiccontent/dynamiccontent.py
   :pyobject: InvestmentOrder.submit

If the submitted data is not correct, raise a |DomainException| to indicate the problem:

.. literalinclude:: ../../reahl/doc/examples/tutorial/dynamiccontent/dynamiccontent.py
   :pyobject: InvestmentOrder.validate_allocations

Communicate the error condition to the user by displaying the |DomainException| as part of 
AllocationDetailForm:

.. literalinclude:: ../../reahl/doc/examples/tutorial/dynamiccontent/dynamiccontent.py
   :pyobject: AllocationDetailForm.add_allocation_controls
