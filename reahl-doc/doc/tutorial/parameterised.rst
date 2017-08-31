.. Copyright 2013, 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |View| replace:: :class:`~reahl.web.fw.View`
.. |UserInterface| replace:: :class:`~reahl.web.fw.UserInterface`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |Event| replace:: :class:`~reahl.component.modelinterface.Event`
.. |Button| replace:: :class:`~reahl.web.ui.Button`
.. |Form| replace:: :class:`~reahl.web.ui.Form`
.. |Transition| replace:: :class:`~reahl.web.fw.Transition`

Parameterised  Views
====================

.. sidebar:: Examples in this section

   - tutorial.parameterised1
   - tutorial.parameterised2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

The AddressBook example can be changed to allow editing of existing
Addresses.

.. figure:: parameterised.png
   :align: center

   Views for editing addresses.

A |View| can have arguments---so that a single "Edit" |View| is
defined *for an as yet unknown Address*.  Computing the actual
contents of the |View| is delayed until the Address argument becomes
available.


How to create a parameterised view
----------------------------------

To specify that a |View| has arguments, create your own class that
inherits from |UrlBoundView|. Give it an
:meth:`~reahl.web.fw.UrlBoundView.assemble` method with keyword
arguments that represent the arguments to the
|UrlBoundView|.

Customise the |View| based on the arguments given inside this
:meth:`~reahl.web.fw.UrlBoundView.assemble` method. The title of the
|UrlBoundView| is set by setting
:attr:`~reahl.web.fw.UrlBoundView.title`. Populate the |Slots| by
calling :meth:`~reahl.web.fw.UrlBoundView.set_slot`

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1/parameterised1.py
   :pyobject: EditView

If an EditView is requested for an address_id that does not exist, raise
a :class:`~reahl.web.fw.CannotCreate` to indicate that the
EditView does not exist for the given arguments.



How to define a parameterised view
----------------------------------

To define a parameterised |View|, use the `view_class` keyword
argument to :meth:`~reahl.web.fw.UserInterface.define_view`.

The framework parses arguments from the URL of the |UrlBoundView| and
passes these into the call to |assemble|.

|Field|\s describe how the framework manages arguments sent to the
|View| via its URL. Each |Field| sent as a keyword argument to
:meth:`~reahl.web.fw.UserInterface.define_view`, is used to compute
the value of a matching keyword argument in |assemble|.

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1/parameterised1.py
   :pyobject: AddressBookUI


Bookmarks to parameterised Views
--------------------------------

In any Reahl application there are two ways to get to a View:
- click on an |A| created from a |Bookmark|
- automatically because of transition.

Our 'tutorial.parameterised1' example creates an |A| next to each
listed address:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1/parameterised1.py
   :pyobject: AddressBox

A distinct |Bookmark| is computed for each Address. This is done in
`AddressbookUI.get_edit_bookmark`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1/parameterised1.py
   :pyobject: AddressBookUI.get_edit_bookmark


Transitions to parameterised Views
----------------------------------

In the 'tutorial.parameterised2' , an edit |Button| is instead placed
next to each Address.

A |Button| has to be in a |Form|, so AddressBox much change to be a
|Form|.  Call
:meth:`~reahl.component.modelinterface.Event.with_arguments` on the
|Event| to which the |Button| is tied so that the user will transition
to a matching EditView.


.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2.py
   :pyobject: AddressBox

Lastly, define a transition as usual:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2.py
   :pyobject: AddressBookUI


Programmatic arguments
----------------------

Not all the arguments passed to the `.assemble()` method of a |View|
need to be parsed from the URL of the |View|. Sometimes it is useful to
pass an object that is available in the `.assemble()` of the
containing |UserInterface| to the `.assemble()` of one of its  |View|\s .

For example, the `.assemble()` of a particular |View| may need access to a
:class:`~reahl.web.fw.Bookmark` which is computed inside the `.assemble()` of its |UserInterface|.

A |View| can be parameterised by such arguments as well.  Just pass the
actual value as keyword argument to `.define_view()`. The framework
distinguishes between normal programmatic arguments and those that
have to be parsed from the URL based on the fact that |Field| instances
are sent for the arguments that need to be parsed from the URL. At the
end of the day they're all just arguments to the |View| though.


Multiple possible destinations
------------------------------

In cases where there are multiple |Transition|\ s possible, things get
tricky:

At the time of defining the |Event| or placing the |Button| the exact
target |View| that will be transitioned to is not known yet. The
target |View| transitioned to will depend on the |Transition|
chosen -- something only known when the |Event| occurs. So be sure to
specify all possible arguments to all possible target  |View|\s  of all
possible |Transition|\ s from the |View| on which the |Button| is placed!


