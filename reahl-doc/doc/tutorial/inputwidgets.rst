.. Copyright 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |Input| replace:: :class:`~reahl.web.ui.Input`
.. |Form| replace:: :class:`~reahl.web.bootstrap.forms.Form`
.. |FormLayout| replace:: :class:`~reahl.web.bootstrap.forms.FormLayout`
.. |FieldSet| replace:: :class:`~reahl.web.bootstrap.ui.FieldSet`
.. |TextInput| replace:: :class:`~reahl.web.bootstrap.forms.TextInput`
.. |Button| replace:: :class:`~reahl.web.bootstrap.forms.Button`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |EmailField| replace:: :class:`~reahl.component.modelinterface.EmailField`
.. |Event| replace:: :class:`~reahl.component.modelinterface.Event`
.. |Action| replace:: :class:`~reahl.component.modelinterface.Action`
.. |UrlBoundView| replace:: :class:`~reahl.web.fw.UrlBoundView`

 
User interaction
================

.. sidebar:: Examples in this section

   - tutorial.addressbook2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Forms and Inputs
----------------

|Form|\s get input from users. Build up the |Form| by adding |Input|
|Widget|\s to it, via an appropriate |FormLayout|.

Below, we use a |FieldSet| for visual effect, and apply a |FormLayout|
to the |FieldSet| in order to add a |TextInput| for both the name and
email of a newly created Address.

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook2/addressbook2.py
   :pyobject: AddressForm
   :end-before: define_event_handler


Fields provide metadata
-----------------------

Notice how each |Input| is wired to an associated |Field|. A |Field|
holds more information about the similarly named attribute of the
Address. |EmailField| constrains the input to be a valid email
address. Invalid input is blocked by the |EmailField| and the
|FormLayout| displays an error message underneath its |TextInput|.

.. figure:: inputs.png
   :align: center
   :width: 80%
   :alt: A diagram showing a TextInput linking to an EmailField, in turn linking the email_address attribute of an Address object

   A rough design sketch

|Field|\s are defined on Address using a method decorated with
:class:`~reahl.component.modelinterface.exposed`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook2/addressbook2.py
   :pyobject: Address

.. note:: Don't confuse |Field|\s with SQLAlchemy's Columns.

   The email_address |Field| sets the email_address attribute of an
   Address after validating input, etc. A Column on that same
   email_address takes another step---to persist the attribute to the
   database. They are independent and do not *have* to be used
   together.


   
Buttons and Events
------------------
	      
To save an Address to the database, create a `save()` method on it. Expose
an |Event| for `save()` so that it can be tied to a |Button|.

When the |Button| is clicked, the `save` |Event| occurs and its
|Action| is executed. Call
:meth:`~reahl.web.fw.Widget.define_event_handler` to specify which
|UrlBoundView| to display next. (The default is to stay on the same
|UrlBoundView|.)

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook2/addressbook2.py
   :pyobject: AddressForm




