.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Re-use: Allowing users to log in to your system
===============================================

.. sidebar:: Examples in this section

   - tutorial.login1bootstrap
   - tutorial.login2bootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


There's no need to build login functionality yourself, Reahl provides this already.

You can opt to use only the provided model and write your own user
interface, or use both the model and the user interface shipped by Reahl.

Re-using a domain model
-----------------------

.. sidebar:: What about database tables?

   Because you declared a dependency on `reahl-domain` in your .project
   file, Reahl is aware that this component needs tables. Refer to
   :doc:`persistence` for the commands to manage the database schema.

The user and system account functionality is in the `reahl-domain` component,
in the module `reahl.systemaccountmodel`.

To be able to use it in your code, list the `reahl-domain` component as a dependency in the
`.reahlproject` file of your own project:

.. literalinclude:: ../../reahl/doc/examples/tutorial/login1/.reahlproject
   :language: xml

Remember, each time you change a `.reahlproject` file, you need to
run ``reahl setup -- develop -N``, as explained in :doc:`persistence`.


Use :class:`~reahl.systemaccountmodel.AccountManagementInterface` in
your code to find the current
:class:`~reahl.systemaccountmodel.LoginSession`.


An :class:`~reahl.systemaccountmodel.AccountManagementInterface` has
many :class:`~reahl.component.modelinterface.Field`\ s and
:class:`~reahl.component.modelinterface.Event`\ s available for use by
user interface code. It allows for logging in and out, but also for
registration, verification of the email addresses of new
registrations, resetting forgotten passwords, etc.

.. literalinclude:: ../../reahl/doc/examples/tutorial/login1bootstrap/login1bootstrap.py




Exercising `tutorial.login1bootstrap`
-------------------------------------

When you fire up the example application, there will be no users
registered to play with. To create some, run:

.. code-block:: bash

   reahl demosetup

This creates a user and password as per:

.. literalinclude:: ../../reahl/doc/examples/tutorial/login1bootstrap/login1bootstrap_dev/test_login1bootstrap.py
   :pyobject: LoginFixture





Re-using the user interface as well
-----------------------------------

To use the provided :class:`~reahl.domainui.accounts.AccountUI`
|UserInterface| graft it onto its own URL in LoginUI. The URLs of the
:class:`~reahl.web.fw.View`\ s of
:class:`~reahl.domainui.accounts.AccountUI` are then appended to that
URL.

Call :meth:`~reahl.web.fw.UserInterface.define_user_interface` to graft |AccountUI| onto LoginUI.

In this call you need to specify which |Slot| name as declared by
|AccountUI| plugs into which |Slot| names we have available on MenuPage..

|AccountUI| expects a number of special |Bookmark|\s. These are sent
through as an additional keyword argument to
:meth:`~reahl.web.fw.UserInterface.define_user_interface`.

.. literalinclude:: ../../reahl/doc/examples/tutorial/login2bootstrap/login2bootstrap.py


Exercising `tutorial.login2bootstrap`
-------------------------------------

This example sends out emails (eg, when you register). Run our fake
email server to catch these. The fake email server just displays each
email in the terminal where it runs. Start it before you use the
example app:

.. code-block:: bash

   reahl servesmtp

