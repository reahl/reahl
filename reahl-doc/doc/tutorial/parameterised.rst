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
   - tutorial.parameterised1bootstrap
   - tutorial.parameterised2
   - tutorial.parameterised2bootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

Not all  |View|\s  can be statically defined in the `.assemble()` method of
a |UserInterface|. In our AddressBook example you might want to add an
EditAddress |View| for each Address in the database as shown in the
following diagram:


.. figure:: parameterised.png
   :align: center

   Views for editing addresses.


This may result in a very large number of  |View|\s -- an
"Edit" |View| would have to be added to the |UserInterface| for each Address in
the database. That is clearly not an acceptable solution.

In order to solve the problem a |View| can have arguments -- so that a
single "Edit" |View| can be defined *for an as yet unknown Address*.  Computing
the actual contents of the |View| is delayed until the Address argument
becomes available.

How it works
------------

Usually, a |View| would have a simple, hardcoded URL such as
'/add'. When a |View| has arguments, its URL is expanded to contain the
values of its arguments. In this example, the |View| added on '/edit'
results in a whole set of  |View|\s  with URLs such as '/edit/1' or
'/edit/2'.  The '/1' and '/2' are the ids for different Addresses in
this example.

Just like |UserInterface|\ s, a |View| can also have an `.assemble()` method in
which the definition of its contents can be finalised, based on the
arguments of the |View|. When the framework has to render a |View|, it
parses the requested URL to determine which |View| the URL is referring
to. The values for the arguments to the |View| are then extracted from
the given URL. The |View| is constructed, and the `.assemble()` method
of the newly constructed |View| is called, passing all the arguments of
the |View| as keyword arguments to it.

The definition of a |View| with an `.assemble()` method is thus partly
deferred to the time when the |View| is actually accessed, instead of up
front when the |UserInterface| is assembled as was previously shown. 


Parameterising a View
---------------------

To specify that a |View| has arguments, a programmer supplies a
|Field| for governing each argument when defining the |View|.

The programmer also needs to supply a custom |View| class which
subclasses from :class:`~reahl.web.fw.UrlBoundView` and in which the `.assemble()` method is
overridden with custom logic that deals with these arguments.

In the AddressBookUI class shown below, a |View| is added for editing,
parameterised by the id of an Address:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1bootstrap/parameterised1bootstrap.py
   :pyobject: EditView

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1bootstrap/parameterised1bootstrap.py
   :pyobject: AddressBookUI		  

Notice how the arguments of the |View| are specified. They are passed as
|Field|\ s in extra keyword arguments to the `.define_view()` method.
Since an EditView is needed, it is also specified by the `view_class`
keyword argument of `.define_view()`.

The signature of `EditView.assemble()` needs to include a matching
keyword argument for each argument thus defined.

Inside `EditView.assemble()`, an Address is first obtained from the
given `address_id`, then that Address is used to customise the title
of the |View|. This Address is also used when setting the 'main' slot to
contain an EditForm *for the given address*.

It is possible that a |View| may be requested for an Address id which
does not exist in the database. If this should happen, just raise a
:class:`~reahl.web.fw.CannotCreate` as shown in the beginning of `EditView`.assemble()`.

A word about bookmarks
----------------------

Since a |UserInterface| (in this case AddressBookUI) already contains the
knowledge of which  |View|\s  it contains, it seems to be good design that
other elements of the user interface ask it for :class:`~reahl.web.fw.Bookmark`\ s to those
|View|\s  when needed.

For this reason, the `.get_edit_bookmark()` method was added to
AddressBookUI. You will notice in the code below that AddressBookUI
is sent all the way to each AddressBox just so that
`AddressBookUI.get_edit_bookmark()` can be called. Notice also that a
:class:`~reahl.web.fw.Bookmark` can never be obtained for 'the edit |View|', a :class:`~reahl.web.fw.Bookmark` is for
something like 'the edit |View| for address X': it includes the
arguments of the bookmarked |View|.

Here is the complete application thus far:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1bootstrap/parameterised1bootstrap.py


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


Transitions to parameterised Views
----------------------------------

In the example above, hypertext links were added for each Address
listed on the Addresses page.  Given this example that is probably
good enough. In some cases, though, it is desirable to transition a
user to a parameterised |View| in response to a |Button| being clicked
(ie, in response to an |Event|).

When the framework transitions a user to a parameterised |View| in
response to a |Button| having been clicked, the arguments passed to the
|View| originate from the |Button|. 

.. sidebar:: When things get complicated

   In cases where there are multiple |Transition|\ s possible, things get
   tricky:

   At the time of defining the |Event| or placing the |Button| the exact
   target |View| that will be transitioned to is not known yet. The
   target |View| transitioned to will depend on the |Transition|
   chosen -- something only known when the |Event| occurs. So be sure to
   specify all possible arguments to all possible target  |View|\s  of all
   possible |Transition|\ s from the |View| on which the |Button| is placed!

Remember how this is all strung together: the |Button| is linked to an
|Event|, which in turn fires off a |Transition| that leads to
the |View| itself. The parameters to be used for the |View| thus have to
be passed on along this chain: when placing the |Button| the programmer
has to supply the actual values to the arguments, and the |Event| must
ferry along whatever arguments are passed to it. The |Transition| has
the final responsibility of supplying the arguments needed by its
target |View| -- by picking them off the |Event| that occurred.

To show how this works, let us change the current example by adding
a |Button| to each AddressBox instead of a hypertext link. To be able to
do this, each AddressBox needs to be a little |Form|, since |Button|\ s
need to be part of a |Form|.

When the |Button| is placed, it is linked to a version of the |Event|
which is *bound to* certain argument values. This *bound* |Event| is
obtained by calling `.with_arguments()` on the original |Event|, passing
it the actual values needed by the target |View|.

The changed implementation of AddressBox below shows how AddressBox
has been changed to a |Form|, and also how the |Button| is created with an
|Event| which is bound to argument values:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2bootstrap/parameterised2bootstrap.py
   :pyobject: AddressBox

.. note:: 

   Methods starting with `add_` always return the added thing. This is
   similar to methods starting with `define_` which return the Factory
   for the defined thing. (A handy little trick borrowed from our
   SmallTalk friends!)

The final change to the application is the addition of a
transition. This is again done in the `.assemble()` method of the
AddressBookUI. Note how the structure of our initial schematic design
is visible in this method -- each |View| is defined, and then all the
transitions between the  |View|\s :

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2bootstrap/parameterised2bootstrap.py
   :pyobject: AddressBookUI
