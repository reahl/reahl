.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Re-use: Allowing users to log in to your system
===============================================

.. sidebar:: Examples in this section

   - tutorial.login1
   - tutorial.login1bootstrap
   - tutorial.login2
   - tutorial.login2bootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

In the :doc:`previous section <sessions>`, a web application was built
into which users can log in using a password. As part of this, some
model code needed to be written -- to model such Users and their login
credentials.

If you are sick of having to re-write this functionality for each new
web application, you can opt to use such functionality that is
implemented by Reahl itself. You have options too: you can choose to
only use the model behind the scenes and write your own user
interface, or use both the model and user interface shipped by Reahl.

Re-using a domain model
-----------------------

To re-use a domain model is really easy. It basically just means
re-using a library of code shipped by someone. Reahl distributes such
code in components that are packaged as Python Eggs. The code to allow
users to log into a system is shipped in the `reahl-domain` component,
in the module `reahl.systemaccountmodel`.

In there is a class, `AccountManagementInterface` which is
session-scoped. In other words to get an AccountManagementInterface,
you just call AccountManagementInterface.for_current_session(). The
:class:`~reahl.systemaccountmodel.LoginSession` class is also in this module. It is session-scoped
and serves the same purpose as the LoginSession of :doc:`the
previous example <sessions>`.

An AccountManagementInterface has many :class:`~reahl.component.modelinterface.Field`\ s and :class:`~reahl.component.modelinterface.Event`\ s available for
use by user interface code. It allows for logging in and out, but also
for registration, verification of the email addresses of new
registrations, resetting forgotten passwords, etc.

The :class:`~reahl.systemaccountmodel.LoginSession` object itself is mostly only used for finding out who
is currently logged in.

Here is our simple login application, changed to use this code,
instead of its own little model:

.. literalinclude:: ../../reahl/doc/examples/tutorial/login1/login1.py

To be able to use the `reahl-domain` component in your code as shown
above, you have to show that your component needs it. This is
done by listing the `reahl-domain` component as a dependency in the
`.reahlproject` file of your own component. Here `reahl-domain` is
listed in the `.reahlproject` of this example:

.. literalinclude:: ../../reahl/doc/examples/tutorial/login1/.reahlproject
   :language: xml

Remember, each time you change a `.reahlproject` file, you need to
run ``reahl setup -- develop -N``, as explained in :doc:`models`.

Code is one thing, but re-using model code like this has other
implications. What about the database? Certainly some tables need to
be created in the database and maintained?

The underlying component framework will take care of creating the
correct database schema for all components that are listed as
dependencies in your `.reahlproject`. Once again, refer back to
:doc:`models` if you forgot how this works.

Exercising the application
--------------------------

Our example application would be difficult to fire up and play with,
because it has no user interface for registering new user accounts!

The tests can come to the rescue here. You can of course play with the
application indirectly by running (or even using pdb to step through)
the tests themselves, but it is always nice to just play with an
application to see what it does.

In order to do the latter, a special fixture can be created. The Reahl
extensions to nosetests let you run (and commit) the setup of a
particular fixture. This creates a database for you, populated with
whatever was created during the set up of that :class:`~reahl.tofu.Fixture`. After doing
this, you can serve the application using this database and play around.

DemoFixture in the example test is provided for this purpose. To use
it, execute:

.. code-block:: bash

   nosetests --with-run-fixture=reahl.webdev.fixtures:BrowserSetup --with-setup-fixture=reahl.doc.examples.tutorial.login1.login1_dev.login1tests:DemoFixture

Here is all the code of the test itself:

.. literalinclude:: ../../reahl/doc/examples/tutorial/login1/login1_dev/login1tests.py



Re-using the user interface as well
-----------------------------------

If you're really lazy, you can write even less code. You can re-use
the :class:`~reahl.web.fw.UserInterface` shipped with Reahl that contains  :class:`~reahl.web.fw.View`\ s  for logging in and
other related account management.

Re-using bits of web-based user interface traditionally has been quite
difficult. In part this is because each web application has a distinct
look and layout. How does one re-use a complete bit of "page flow" in
different web applications, each application with its own look and
layout?

The concepts of a :class:`~reahl.web.fw.UserInterface`, of a page and :class:`~reahl.web.ui.Slot`\ s exist to make
such re-use possible. The basics of these concepts is explained in
:doc:`slots`, but there's more to it than is explained
there. In examples thus far, each web application consisted of a few
related  :class:`~reahl.web.fw.View`\ s  packaged as a single :class:`~reahl.web.fw.UserInterface`. It is possible, however, to
compose your web application from multiple :class:`~reahl.web.fw.UserInterface`\ s. Hence, you can use
a :class:`~reahl.web.fw.UserInterface` that someone else has built beforehand.

In the `reahl-domainui` component, in the `reahl.domainui.accounts`
module, lives a :class:`~reahl.web.fw.UserInterface` called :class:`~reahl.domainui.accounts.AccountUI`. It contains  :class:`~reahl.web.fw.View`\ s  for
logging in, registering a new account, and more. In order to use it,
you will need to give it its own URL in your web application -- just
like you'd define a :class:`~reahl.web.fw.View` on a particular URL. The URLs of the  :class:`~reahl.web.fw.View`\ s  of
the :class:`~reahl.domainui.accounts.AccountUI` will then be appended to the URL you use for the
:class:`~reahl.web.fw.UserInterface` itself.

The page of your web application defines a number of :class:`~reahl.web.ui.Slot`\ s. The
writer of :class:`~reahl.domainui.accounts.AccountUI` (or any other :class:`~reahl.web.fw.UserInterface`) does not know what :class:`~reahl.web.ui.Slot`\ s
**your** application will have for plugging in its bits of user
interface. Hence, each :class:`~reahl.web.fw.UserInterface` writer chooses a couple of names for
:class:`~reahl.web.ui.Slot`\ s needed for its  :class:`~reahl.web.fw.View`\ s . When you use such a :class:`~reahl.web.fw.UserInterface`, you need to
specify which of the :class:`~reahl.web.fw.UserInterface`'s :class:`~reahl.web.ui.Slot`\ s plug into which of your own
application's :class:`~reahl.web.ui.Slot`\ s.

A :class:`~reahl.web.fw.UserInterface` and its :class:`~reahl.web.ui.Slot` names are analogous to a method and its
arguments: the method signature contains variable names chosen by the
programmer who wrote it. You can call that method from many different
places, passing in different values for those arguments. Specifying
the :class:`~reahl.web.ui.Slot`\ s when re-using a :class:`~reahl.web.fw.UserInterface` is similar.

In this example, we used a :class:`~reahl.web.layout.PageLayout` with a :class:`~reahl.web.bootstrap.grid.ColumnLayout` to add a :class:`~reahl.web.ui.Slot` named `main` to our MenuPage.  The :class:`~reahl.domainui.accounts.AccountUI` in turn has a :class:`~reahl.web.ui.Slot` named `main_slot`. Hence, it is necessary to
state that `main_slot` of :class:`~reahl.domainui.accounts.AccountUI` plugs into `main` of our MenuPage.

:class:`~reahl.domainui.accounts.AccountUI` also has its own requirements: it needs a number of
bookmarks. Specifically, it expects to be passed an object from which
it can get a bookmark for: a page listing the terms of service of the
site, the privacy policy of the site, and a disclaimer.

The code below is our entire little application, rewritten to use the
:class:`~reahl.domainui.accounts.AccountUI`. (Note that since our application does not have  :class:`~reahl.web.fw.View`\ s 
for all the legal bookmarks linked to by the :class:`~reahl.domainui.accounts.AccountUI`, the home
page of the application has been used for each legal bookmark in this
example.)

Just to show a few more bits of the :class:`~reahl.domainui.accounts.AccountUI`, the example has
been modified to include some more items in its :class:`~reahl.web.ui.Menu`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/login2/login2.py


Exercising the lazier application
---------------------------------

.. warning::

   You have to start our test email server before running this app.
   
   This application may try to send out email -- when you register, for
   example. And since you do not have an email server running on your
   development machine that will probably break. To solve this, run the
   following (in a different terminal):

   .. code-block:: bash

      reahl servesmtp

   This command runs a simple email server which just shows every email
   it receives in the terminal where it is running.


Of course, some tests are included for our lazy application. The tests once
again include a :class:`~reahl.tofu.Fixture` for setting up the application database as before:

.. code-block:: bash
   
   nosetests --with-run-fixture=reahl.webdev.fixtures:BrowserSetup --with-setup-fixture=reahl.doc.example.tutorial.login2.login2_dev.login2tests:DemoFixture


Finally, and for completeness, here is the test code:

.. literalinclude:: ../../reahl/doc/examples/tutorial/login2/login2_dev/login2tests.py
