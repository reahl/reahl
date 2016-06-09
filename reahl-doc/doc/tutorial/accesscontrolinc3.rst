.. Copyright 2013, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Adding the access control
=========================

.. sidebar:: Examples in this section

   - tutorial.access
   - tutorial.accessbootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

There are quite a number of bits and pieces of access control that
need to be built into this application. One can classify all the bits
and pieces into three categories:

The first category has to do with access control on Inputs.

The Edit :class:`~reahl.web.ui.Button` next to each Address in the AddressBookView should
always be displayed, but be greyed out unless the current user is
allowed to edit that particular Address. On the EditAddressView
itself, the :class:`~reahl.web.ui.TextInput` for "Name" should be greyed out if the current
user is not allowed to change it. (Remember, the requirements stated
that you can only change the name if you're allowed to add Addresses
to the selected AddressBook.)

The next category concerns the :class:`~reahl.web.ui.MenuItem`\ s displayed as part of the :class:`~reahl.web.ui.Menu` of
AddressBookView.

The :class:`~reahl.web.ui.Menu` in question contains two :class:`~reahl.web.ui.MenuItem`\ s: one to add an Address,
and one to add a Collaborator. "Add Address" should always be shown,
but should be greyed out except if the current user is allowed to add
Addresses to the AddressBook being viewed. "Add Collaborator" should
not even be shown, except on the user's own AddressBook.

The last category is more sinister. A malicious user could pay attention
to what the URLs look like as he navigates the application. For
example, you'd notice that the URL of your own AddressBook is
`/address_book/3`. From such an URL it is pretty obvious that it
denotes the AddressBook with ID 3. Knowing (or guessing), you could
change the 3 to some other number and in this way end up seeing an
AddressBook that belongs to someone else even though no user interface
element lead you to it.

The same sort of vulnerability is possible for the other URLs:
`/add_address`, `/edit_address` and `/add_collaborator`.


Tests
-----

Before we start though, lets add the necessary tests. The categories
above are useful for explaining the implementation, but not so useful
to explain the requirements of the application itself. Tests should
elucidate the latter. Hence, the following tests were added:

.. literalinclude:: ../../reahl/doc/examples/tutorial/access/access_dev/accesstests.py
   :start-after: # ------- Tests added for access control


The code
--------

Inputs
~~~~~~

The access control for an :class:`~reahl.web.ui.Input` is determined from the :class:`~reahl.component.modelinterface.Field` to which
it is attached. When creating a :class:`~reahl.component.modelinterface.Field`, one can pass in two extra keyword
arguments: `readable` and `writable`. These arguments are :class:`~reahl.component.modelinterface.Action`\ s: The
methods they wrap are expected to return True or False to indicate
whether the :class:`~reahl.component.modelinterface.Field` is readable or writable for current user.

 - If a :class:`~reahl.component.modelinterface.Field` is readable, but not writable for someone, an :class:`~reahl.web.ui.Input`
   using it will be present, but greyed out.

 - If the :class:`~reahl.component.modelinterface.Field` is both readable and writable, the :class:`~reahl.web.ui.Input` will be
   displayed and active.

 - If the :class:`~reahl.component.modelinterface.Field` is not readable and also not writable, the
   corresponding :class:`~reahl.web.ui.Input` will not be displayed on the page at all.

 - It is also possible for some :class:`~reahl.component.modelinterface.Field`\ s to be writable, but yet not
   readable. This is counter-intuitive, but makes sense if you think
   about it: The quintessential example is that of a
   password. Generally, users are allowed to write their passwords,
   but these passwords are never allowed to be read.
 
   In this case, an :class:`~reahl.web.ui.Input` would be displayed and be active, but it
   will always be rendered without any contents. Contrast this with
   the normal case, where an :class:`~reahl.web.ui.Input` would be rendered with the current
   Value of the :class:`~reahl.component.modelinterface.Field` pre-populated.

This is what it looks like in the code of Address:

.. literalinclude:: ../../reahl/doc/examples/tutorial/access/access.py
   :pyobject: Address.fields

Note how the `name` :class:`~reahl.component.modelinterface.Field` is required, but only when writable. Of
course, to be able specify access rights, these no-arg methods needed
to added to Address as well:

.. literalinclude:: ../../reahl/doc/examples/tutorial/access/access.py
   :pyobject: Address.can_be_added

.. literalinclude:: ../../reahl/doc/examples/tutorial/access/access.py
   :pyobject: Address.can_be_edited

Any :class:`~reahl.web.ui.Input` anywhere in our application which uses these :class:`~reahl.component.modelinterface.Field`\ s will now
have the correct access control applied to it. 

The same principle applies to the `edit` :class:`~reahl.component.modelinterface.Event` of an
Address, and the :class:`~reahl.web.ui.Button`\ s created for it:

.. literalinclude:: ../../reahl/doc/examples/tutorial/access/access.py
   :pyobject: Address.fields

Easy, isn't it?

.. note:: 

   Although not shown in this example, any :class:`~reahl.web.fw.Widget` can be also supplied
   with methods to determine its readability or writability by the
   currrent user. :class:`~reahl.web.fw.Widget`\ s accept the `read_check` and `write_check`
   keyword arguments upon construction for this purpose. These
   `*_check` methods are just no-argument methods that will be
   called -- not :class:`~reahl.component.modelinterface.Action`\ s as are the `readable` and `writable` keyword
   arguments of :class:`~reahl.component.modelinterface.Field`\ s.



Menu items and Views
~~~~~~~~~~~~~~~~~~~~

The last two categories of our access control requirements are
actually implemented using the same mechanism. Think about it: A
:class:`~reahl.web.ui.MenuItem` is really a way to navigate to a particular :class:`~reahl.web.fw.View`. Manually
typing an URL into the location bar of the browser is pretty much the
same thing.

To accommodate the two sides of this coin,  :class:`~reahl.web.fw.View`\ s  can also have access
rights specified on them. Once again, a :class:`~reahl.web.fw.View` can be allowed to be
read or written by the current user. If you're allowed to read a :class:`~reahl.web.fw.View`,
you're allowed to see it, and consequently you are allowed to navigate
to it. A :class:`~reahl.web.ui.MenuItem` leading to such a :class:`~reahl.web.fw.View` would be displayed and
active.

A :class:`~reahl.web.ui.MenuItem` leading to a :class:`~reahl.web.fw.View` you arenot allowed to read, will not be
rendered at all.

Being allowed to write a :class:`~reahl.web.fw.View` means that the user is allowed to press
:class:`~reahl.web.ui.Button`\ s on it. The writability of a :class:`~reahl.web.fw.View` makes more sense if you think
of it in terms of user interface though: If a :class:`~reahl.web.fw.View` is readable, but
not writable to someone, :class:`~reahl.web.ui.MenuItem`\ s leading to it would be present, but
inactive -- analogous to how :class:`~reahl.component.modelinterface.Field`\ s and Inputs work.

If a malicious user tries to manually type an URL leading to a :class:`~reahl.web.fw.View` he
should not read, the framework returns an error to the browser.

On to coding all of this: Simple  :class:`~reahl.web.fw.View`\ s  work like :class:`~reahl.web.fw.Widget`\ s in that you
can pass no-argument methods to the `read_check` and `write_check`
keyword arguments of `.define_view()`. This example, however, only
shows how to deal with parameterised  :class:`~reahl.web.fw.View`\ s  (the most common case
needing access control). For parameterised  :class:`~reahl.web.fw.View`\ s , the `read_check` and
`write_check` are merely set inside the `.assemble()` method of the
:class:`~reahl.web.fw.View` -- like with other things related to parameterised  :class:`~reahl.web.fw.View`\ s , the
necessary information is available at this point to check access. See
what it looks like for EditAddressView:

.. literalinclude:: ../../reahl/doc/examples/tutorial/access/access.py
   :pyobject: EditAddressView


The complete example
~~~~~~~~~~~~~~~~~~~~

Below is the complete code for this example. A few methods needed to
be added here and there in order to be able to specify the necessary
rights:

.. literalinclude:: ../../reahl/doc/examples/tutorial/access/access.py
