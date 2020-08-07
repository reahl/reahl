.. Copyright 2020 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Input| replace:: :class:`~reahl.web.ui.Input`
.. |ButtonInput| replace:: :class:`~reahl.web.ui.ButtonInput`
.. |PrimitiveInput| replace:: :class:`~reahl.web.ui.PrimitiveInput`
.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |Form| replace:: :class:`~reahl.web.ui.Form`
.. |add_alert_for_domain_exception| replace:: :meth:`~reahl.web.bootstrap.forms.FormLayout.add_alert_for_domain_exception`
.. |get_concurrency_hash_strings| replace:: :meth:`~reahl.web.fw.Widget.get_concurrency_hash_strings`



Dealing with concurrent users
=============================

.. sidebar:: Examples in this section

   - howtos.optimisticconcurrency

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Why worry about concurrent users?
---------------------------------

If you're not careful, one user can easily overwrite the data persisted by another user working 
on the same page at the same time.

Consider this sequence of events:
 - user A opens page X
 - user B opens page X
 - user A changes input on a form on page X, and clicks on a |ButtonInput| that submits it
 - the database is changed as a result of user A's changes in such a way that page X would not render the same anymore
 - user B still has the old page X open, and now makes similar changes on that page and clicks on a |ButtonInput| that submits the info

Without intervention in the above scenario user B's changes might
overwrite those of user A or the application could break - depending
on how the code was written.


Reahl prevents changes to outdated forms
----------------------------------------

When a user clicks on a |ButtonInput|\, Reahl checks whether the |Input| values have 
been changed since it was rendered for this user. If a change is detected, an error
is shown (with an option to refresh the |Form|).

.. figure:: ../_build/screenshots/optimisticconcurrency.png
   :align: center
   :alt: The error shown when submitting an out of date |Form|\.

Customising the up-to-date-check
--------------------------------

You don't have do any coding to enable this check. You may want to customise what
should be included in this up-to-date check, and what not.

You should also ensure (as with all |Form|\s) that your form displays any errors 
that may occur as is done with |add_alert_for_domain_exception| in:

.. literalinclude:: ../../reahl/doc/examples/howtos/optimisticconcurrency/optimisticconcurrency.py
   :pyobject: SimpleForm.__init__

When a |Form| is submitted, the new user input is not immediately applied. First, the values of 
all of its |PrimitiveInput|\s are computed as they would render at this point and compared with 
what they were when the |Form| was rendered initially. 

If any differences are detected here it means that someone must have changed relevant data in 
the database since the |Form| was rendered.

To prevent a specific |PrimitiveInput| from participating in this check, pass `ignore_concurrent_change=True`
when constructing the |PrimitiveInput|. 

If you have a |Widget| that is not a |PrimitiveInput|, but that represents some data in the database
which you want to partipate in this check, override |get_concurrency_hash_strings| on your |Widget|:

.. literalinclude:: ../../reahl/doc/examples/howtos/optimisticconcurrency/optimisticconcurrency.py
   :pyobject: MyConcurrencyWidget

|get_concurrency_hash_strings| yields one or more strings that represent the database state that
should influence the up-to-date check.


