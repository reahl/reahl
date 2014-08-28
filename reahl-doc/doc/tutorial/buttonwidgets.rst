.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Buttons allow users to act
==========================

.. sidebar:: Examples in this section

   - tutorial.addressbook2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

All that's left to complete our application is to provide a means for
the user to instruct the application to perform some task. In this
case, to save the new address to the database.


Augmenting a model with Events
------------------------------

Just like a :class:`~reahl.component.modelinterface.Field` is used to
expose an item of data inside your model as part of a user interface,
an :class:`~reahl.component.modelinterface.Event` is something that can be
triggered by a user in order to execute a method on the model object.

To do this, use the `@exposed` decorator as before, this time to
define the `events` on your object. An
:class:`~reahl.component.modelinterface.Event` can optionally be
passed an :class:`~reahl.component.modelinterface.Action`. This is
just a wrapper around any callable -- the callable that will get called if
a user triggers this :class:`~reahl.component.modelinterface.Event`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook2/addressbook2.py
   :pyobject: Address


Adding the Save Button
----------------------

.. sidebar:: What happens when the Button is clicked?

   When the user clicks on the "Save" :class:`~reahl.web.ui.Button`, the
   browser submits its associated :class:`~reahl.web.ui.Form` (and all
   the :class:`~reahl.web.ui.Input`\ s present on that
   :class:`~reahl.web.ui.Form` to the web server. The server then
   processes the input received for each :class:`~reahl.web.ui.Input` --
   validating, marshaling and finally setting attributes on the
   underlying domain object.

   Once done with that, Reahl checks which
   :class:`~reahl.component.modelinterface.Event` triggered this
   submission, and executes the
   :class:`~reahl.component.modelinterface.Action` you specified.

The last missing piece of the address book application is the "Save"
:class:`~reahl.web.ui.Button`. It is child's play to add it -- you
merely add a :class:`~reahl.web.ui.Button`
:class:`~reahl.web.fw.Widget` as well, passing it the
:class:`~reahl.component.modelinterface.Event` defined on your model
object. 

But there's a catch: your application won't know how to handle this
:class:`~reahl.component.modelinterface.Event` if you do not first
define an :class:`~reahl.web.fw.EventHandler` for that
:class:`~reahl.component.modelinterface.Event`. Luckily in this simple
scenario that is easy:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook2/addressbook2.py
   :pyobject: AddAddressForm



Try it out
----------

We're done with :doc:`our first simple application <exampleapp>`. Do
try it out and discover how it behaves: its validation, for example,
and how it behaves when JavaScript is not active. Just remember :ref:`all
the housekeeping tasks you need to do before running the application <trying-out>`!

Here is the complete Python source of our example application:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook2/addressbook2.py



