.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Parameterised  Views
====================

.. sidebar:: Examples in this section

   - tutorial.parameterised1
   - tutorial.parameterised2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

Not all  :class:`~reahl.web.fw.View`\ s  can be statically defined in the `.assemble()` method of
a :class:`~reahl.web.fw.UserInterface`. In our AddressBook example you might want to add an
EditAddress :class:`~reahl.web.fw.View` for each Address in the database as shown in the
following diagram:


.. figure:: parameterised.png
   :align: center

   Views for editing addresses.


This may result in a very large number of  :class:`~reahl.web.fw.View`\ s ---an
"Edit" :class:`~reahl.web.fw.View` would have to be added to the :class:`~reahl.web.fw.UserInterface` for each Address in
the database. That is clearly not an acceptable solution.

In order to solve the problem a :class:`~reahl.web.fw.View` can have arguments -- so that a
single "Edit" :class:`~reahl.web.fw.View` can be defined *for an as yet unknown Address*.  Computing
the actual contents of the :class:`~reahl.web.fw.View` is delayed until the Address argument
becomes available.

How it works
------------

Usually, a :class:`~reahl.web.fw.View` would have a simple, hardcoded URL such as
'/add'. When a :class:`~reahl.web.fw.View` has arguments, its URL is expanded to contain the
values of its arguments. In this example, the :class:`~reahl.web.fw.View` added on '/edit'
results in a whole set of  :class:`~reahl.web.fw.View`\ s  with URLs such as '/edit/1' or
'/edit/2'.  The '/1' and '/2' are the ids for different Addresses in
this example.

Just like :class:`~reahl.web.fw.UserInterface`\ s, a :class:`~reahl.web.fw.View` can also have an `.assemble()` method in
which the definition of its contents can be finalised, based on the
arguments of the :class:`~reahl.web.fw.View`. When the framework has to render a :class:`~reahl.web.fw.View`, it
parses the requested URL to determine which :class:`~reahl.web.fw.View` the URL is referring
to. The values for the arguments to the :class:`~reahl.web.fw.View` are then extracted from
the given URL. The :class:`~reahl.web.fw.View` is constructed, and the `.assemble()` method
of the newly constructed :class:`~reahl.web.fw.View` is called, passing all the arguments of
the :class:`~reahl.web.fw.View` as keyword arguments to it.

The definition of a :class:`~reahl.web.fw.View` with an `.assemble()` method is thus partly
deferred to the time when the :class:`~reahl.web.fw.View` is actually accessed, instead of up
front when the :class:`~reahl.web.fw.UserInterface` is assembled as was previously shown. 


Parameterising a View
---------------------

In order to specify the arguments to a :class:`~reahl.web.fw.View`, a programmer supplies a
:class:`~reahl.component.modelinterface.Field` for governing each argument when defining the :class:`~reahl.web.fw.View`.

The programmer also needs to supply a custom :class:`~reahl.web.fw.View` class which
subclasses from :class:`~reahl.web.fw.UrlBoundView` and in which the `.assemble()` method is
overridden with custom logic that deals with these arguments.

In the AddressBookUI class shown below, a :class:`~reahl.web.fw.View` is added for editing,
parameterised by the id of an Address:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1/parameterised1.py
   :pyobject: EditView

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1/parameterised1.py
   :pyobject: AddressBookUI		  

Notice how the arguments of the :class:`~reahl.web.fw.View` are specified. They are passed as
:class:`~reahl.component.modelinterface.Field`\ s in extra keyword arguments to the `.define_view()` method.
Since an EditView is needed, it is also specified by the `view_class`
keyword argument of `.define_view()`.

The signature of `EditView.assemble()` needs to include a matching
keyword argument for each argument thus defined.

Inside `EditView.assemble()`, an Address is first obtained from the
given `address_id`, then that Address is used to customise the title
of the :class:`~reahl.web.fw.View`. This Address is also used when setting the 'main' slot to
contain an EditForm *for the given address*.

It is possible that a :class:`~reahl.web.fw.View` may be requested for an Address id which
does not exist in the database. If this should happen, just raise a
:class:`~reahl.web.fw.CannotCreate` as shown in the beginning of `EditView`.assemble()`.

A word about bookmarks
----------------------

Since a :class:`~reahl.web.fw.UserInterface` (in this case AddressBookUI) already contains the
knowledge of which  :class:`~reahl.web.fw.View`\ s  it contains, it seems to be good design that
other elements of the user interface ask it for :class:`~reahl.web.fw.Bookmark`\ s to those
:class:`~reahl.web.fw.View`\ s  when needed.

For this reason, the `.get_edit_bookmark()` method was added to
AddressBookUI. You will notice in the code below that AddressBookUI
is sent all the way to each AddressBox just so that
`AddressBookUI.get_edit_bookmark()` can be called. Notice also that a
:class:`~reahl.web.fw.Bookmark` can never be obtained for 'the edit :class:`~reahl.web.fw.View`', a :class:`~reahl.web.fw.Bookmark` is for
something like 'the edit :class:`~reahl.web.fw.View` for address X': it includes the
arguments of the bookmarked :class:`~reahl.web.fw.View`.

Here is the complete application thus far:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1/parameterised1.py


Programmatic arguments
----------------------

Not all the arguments passed to the `.assemble()` method of a :class:`~reahl.web.fw.View`
need to be parsed from the URL of the :class:`~reahl.web.fw.View`. Sometimes it is useful to
pass an object that is available in the `.assemble()` of the
containing :class:`~reahl.web.fw.UserInterface` to the `.assemble()` of one of its  :class:`~reahl.web.fw.View`\ s .

For example, the `.assemble()` of a particular :class:`~reahl.web.fw.View` may need access to a
:class:`~reahl.web.fw.Bookmark` which is computed inside the `.assemble()` of its :class:`~reahl.web.fw.UserInterface`.

A :class:`~reahl.web.fw.View` can be parameterised by such arguments as well.  Just pass the
actual value as keyword argument to `.define_view()`. The framework
distinguishes between normal programmatic arguments and those that
have to be parsed from the URL based on the fact that :class:`~reahl.component.modelinterface.Field` instances
are sent for the arguments that need to be parsed from the URL. At the
end of the day they're all just arguments to the :class:`~reahl.web.fw.View` though.


Transitions to parameterised Views
----------------------------------

In the example above, hypertext links were added for each Address
listed on the Addresses page.  Given this example that is probably
good enough. In some cases, though, it is desirable to transition a
user to a parameterised :class:`~reahl.web.fw.View` in response to a :class:`~reahl.web.ui.Button` being clicked
(ie, in response to an :class:`~reahl.component.modelinterface.Event`).

When the framework transitions a user to a parameterised :class:`~reahl.web.fw.View` in
response to a :class:`~reahl.web.ui.Button` having been clicked, the arguments passed to the
:class:`~reahl.web.fw.View` originate from the :class:`~reahl.web.ui.Button`. 

.. sidebar:: When things get complicated

   In cases where there are multiple :class:`~reahl.web.fw.Transition`\ s possible, things get
   tricky:

   At the time of defining the :class:`~reahl.component.modelinterface.Event` or placing the :class:`~reahl.web.ui.Button` the exact
   target :class:`~reahl.web.fw.View` that will be transitioned to is not known yet. The
   target :class:`~reahl.web.fw.View` transitioned to will depend on the :class:`~reahl.web.fw.Transition`
   chosen -- something only known when the :class:`~reahl.component.modelinterface.Event` occurs. So be sure to
   specify all possible arguments to all possible target  :class:`~reahl.web.fw.View`\ s  of all
   possible :class:`~reahl.web.fw.Transition`\ s from the :class:`~reahl.web.fw.View` on which the :class:`~reahl.web.ui.Button` is placed!

Remember how this is all strung together: the :class:`~reahl.web.ui.Button` is linked to an
:class:`~reahl.component.modelinterface.Event`, which in turn fires off a :class:`~reahl.web.fw.Transition` that leads to
the :class:`~reahl.web.fw.View` itself. The parameters to be used for the :class:`~reahl.web.fw.View` thus have to
be passed on along this chain: when placing the :class:`~reahl.web.ui.Button` the programmer
has to supply the actual values to the arguments, and the :class:`~reahl.component.modelinterface.Event` must
ferry along whatever arguments are passed to it. The :class:`~reahl.web.fw.Transition` has
the final responsibility of supplying the arguments needed by its
target :class:`~reahl.web.fw.View` -- by picking them off the :class:`~reahl.component.modelinterface.Event` that occurred.

To show how this works, let us change the current example by adding
a :class:`~reahl.web.ui.Button` to each AddressBox instead of a hypertext link. To be able to
do this, each AddressBox needs to be a little :class:`~reahl.web.ui.Form`, since :class:`~reahl.web.ui.Button`\ s
need to be part of a :class:`~reahl.web.ui.Form`.

When the :class:`~reahl.web.ui.Button` is placed, it is linked to a version of the :class:`~reahl.component.modelinterface.Event`
which is *bound to* certain argument values. This *bound* :class:`~reahl.component.modelinterface.Event` is
obtained by calling `.with_arguments()` on the original :class:`~reahl.component.modelinterface.Event`, passing
it the actual values needed by the target :class:`~reahl.web.fw.View`.

The changed implementation of AddressBox below shows how AddressBox
has been changed to a :class:`~reahl.web.ui.Form`, and also how the :class:`~reahl.web.ui.Button` is created with an
:class:`~reahl.component.modelinterface.Event` which is bound to argument values:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2.py
   :pyobject: AddressBox

.. note:: 

   Methods starting with `add_` always return the added thing. This is
   similar to methods starting with `define_` which return the Factory
   for the defined thing. (A handy little trick borrowed from our
   SmallTalk friends!)

The final change to the application is the addition of a
transition. This is again done in the `.assemble()` method of the
AddressBookUI. Note how the structure of our initial schematic design
is visible in this method -- each :class:`~reahl.web.fw.View` is defined, and then all the
transitions between the  :class:`~reahl.web.fw.View`\ s :

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2.py
   :pyobject: AddressBookUI
