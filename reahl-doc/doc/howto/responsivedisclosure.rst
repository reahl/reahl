.. Copyright 2019 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |enable_refresh| replace:: :meth:`~reahl.web.ui.HTMLElement.enable_refresh`
.. |RadioButtonSelectInput| replace:: :class:`~reahl.web.bootstrap.forms.RadioButtonSelectInput`
.. |HTMLElement| replace:: :class:`~reahl.web.ui.HTMLElement`

Responsive disclosure
=====================

.. sidebar:: Examples in this section

   - howtos.responsivedisclosure

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>



Revealing parts of a page
-------------------------

Instead of showing an intimidating page to a user, you can break it
up into manageable sections that are revealed only if needed.

This example gathers information from someone who wants to make an
investment. What you need to fill in is different depending on whether you are a
new investor or an existing one. Sections are revealed as you enter information.

Here is how different sections nest inside of one another::

      NewInvestmentForm
            |
            |
            +----(InvestorDetailsSection)
                      |  
                      |  
                      +---(IDDocumentSection)
                      |  
                      |  
                      +---(AllocationDetailSection)


Optionally displaying a section
-------------------------------


NewInvestmentForm is always present:

.. figure:: ../_build/screenshots/responsivedisclosure_1.png
   :align: center
   :alt: NewInvestmentForm only.

It optionally contains an InvestorDetailsSection.

Changing the `new_or_existing_radio` |RadioButtonSelectInput| refreshes the NewInvestmentForm.

.. figure:: ../_build/screenshots/responsivedisclosure_2.png
   :align: center
   :alt: InvestorDetailsSection also showing.


Since you have made a selection using the |RadioButtonSelectInput|, `investment_order.new_or_existing`
now has a value and the refreshed version of NewInvestmentForm includes the InvestorDetailSection.

.. note:: The :doc:`dynamic content <dynamiccontent>` example explains how to make an |HTMLElement| refresh.

.. literalinclude:: ../../reahl/doc/examples/howtos/responsivedisclosure/responsivedisclosure.py
   :pyobject: NewInvestmentForm


The whole picture
-----------------

The InvestorDetailSection has different contents, depending on whether you chose to be new or existing:

.. figure:: ../_build/screenshots/responsivedisclosure_3.png
   :align: center
   :alt: InvestorDetailsSection showing different contents.

The AllocationDetailSection is only displayed when you agree to the terms inside the InvestorDetailSection.

.. literalinclude:: ../../reahl/doc/examples/howtos/responsivedisclosure/responsivedisclosure.py
   :pyobject: InvestorDetailsSection




