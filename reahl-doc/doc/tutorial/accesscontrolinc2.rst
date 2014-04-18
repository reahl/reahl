.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
The user interface -- without access control
============================================

.. sidebar:: Examples in this section

   - tutorial.access2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

There is quite a bit of user interface in this application besides its
access control requirements. Implementing the application without
access control is not trivial, so it is a good idea to get it out of
the way.

Tests
-----

Let us add three user stories to the tests that would excercise the
functionality of the user interface, but sidestep the finer grained
access control. That will force us to build the entire application,
but allow us to ignore any access control related code for the
moment. The following three scenarios would do that:

- How a user arrives at the site and has to log in before seeing any
  address books.
- How a user adds and edits addresses in her own address book (this is
  will always be allowed, hence no access control yet).
- How the owner of an address book adds collaborators to his address
  book (ditto).

Because it is valuable to play with a running application too, a
DemoFixture is also added to the tests that sets up a few
SystemAccounts and adds some Addresses to their AddressBooks:

.. literalinclude:: ../../reahl/doc/examples/tutorial/access2/access2_dev/accesstests2.py

Code
----

The implementation that makes those tests pass is given in the code
below. There are several things you'd have to understand in this
solution:

The application uses an AddressAppPage for a page. This is just
to make the application a little easier to drive: it displays who is
logged in currently at the top of the page, and includes a :class:`~reahl.web.ui.Menu` which
just gives the user a way to always return to the home page.

When not logged in, the home page gives the user a way to log in using
an email address and password. When logged in, a list of AddressBooks
is shown. The changing home page is achieved by constructing the
HomePageWidget with different children depending on whether the user
is logged in or not.

Most importantly, the user interface includes a number of  :class:`~reahl.web.fw.View`\ s , many
of them parameterised, and with transitions amongst these
parameterised  :class:`~reahl.web.fw.View`\ s . It is easy to get lost in such code, or to build
it in a messy way. Hence, it warrants your undivided attention before
we complicate the application further.

The Reahl way to deal with this situation is to first sketch it out on
a diagram and then translate the  :class:`~reahl.web.fw.View`\ s  and :class:`~reahl.web.fw.Transition`\ s into an
`.assemble()` method. In this method (right at the bottom of the code
below), one can see which  :class:`~reahl.web.fw.View`\ s  are parameterised, and thus which
:class:`~reahl.web.fw.Transition`\ s are to parameterised  :class:`~reahl.web.fw.View`\ s . Use this information to check
that the correct arguments are specified to `.with_arguments()` where
:class:`~reahl.web.ui.Button`\ s are placed for each :class:`~reahl.component.modelinterface.Event` that may lead to a parameterised
:class:`~reahl.web.fw.View`.

We have decided to use `.define_event_handler()` in `LoginForm` and
`LogoutForm` for allowing `login_event` and `logout_event` to be
linked to :class:`~reahl.web.ui.Button`\ s in these :class:`~reahl.web.fw.Widget`\ s. All other :class:`~reahl.component.modelinterface.Event`\ s are dealt with
using :class:`~reahl.web.fw.Transition`\ s defined in `AddressBookUI.assemble()`. When it
comes to being able to clearly visualise all the pathways through the
application, some :class:`~reahl.component.modelinterface.Event`\ s are just more important to actually show on a
visual diagram than others. This code mirrors our schematic diagram.

Please take your time to study the code below:

.. literalinclude:: ../../reahl/doc/examples/tutorial/access2/access2.py
