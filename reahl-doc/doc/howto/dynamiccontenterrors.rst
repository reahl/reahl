.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Widget| replace::  :class:`~reahl.web.fw.Widget`
.. |DomainException| replace::  :class:`~reahl.component.exceptions.DomainException`
.. |Action| replace:: :class:`~reahl.component.modelinterface.Action`
.. |enable_refresh| replace:: :meth:`~reahl.web.ui.HTMLElement.enable_refresh`

DomainErrors when dynamically refreshing a Widget
=================================================

.. sidebar:: Examples in this section

   - howtos.dynamiccontenterrors

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>



Simple calculator
-----------------

If your `on_refresh` |Action| can result in a |DomainException|, handle such an error and make sure
the |Widget| can be created fully regardless of it having inputs causing the error.

This example shows a simple calculator, that can add and divide two numbers. As soon as the user tabs out of one of
the inputs or changes the operator, the screen is refreshed and recalculated to show the answer.

Choosing the combination of ÷ and 0 results in an operation this calculator cannot do. It handles such an error and
reports it back to the user while also showing the answer as "---" instead of its usual numeric answer.


The calculator logic
--------------------

In the Calculator's `recalculate` method, raise a |DomainException| to signal the error condition, but at the same time
ensure that result is always set. In Calculator.recalculate result is set to None for invalid input:

.. literalinclude:: ../../reahl/doc/examples/howtos/dynamiccontenterrors/dynamiccontenterrors.py
   :pyobject: Calculator.recalculate


The display logic
-----------------

CalculateForm is the |Widget| responsible for showing the Calculator. The usual call to |enable_refresh| automatically
also calls your `on_refresh` |Action|, so be sure to handle the |DomainException| it can raise:

.. literalinclude:: ../../reahl/doc/examples/howtos/dynamiccontenterrors/dynamiccontenterrors.py
   :pyobject: CalculatorForm.__init__

When adding the result for the current nonsensical input, take into account whether or not a result could be calculated:

.. literalinclude:: ../../reahl/doc/examples/howtos/dynamiccontenterrors/dynamiccontenterrors.py
   :pyobject: CalculatorForm.display_result



Full source code
----------------

.. literalinclude:: ../../reahl/doc/examples/howtos/dynamiccontenterrors/dynamiccontenterrors.py


