.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |AccountUI| replace:: :class:`~reahl.domainui.bootstrap.accounts.AccountUI`
.. |AccountManagementInterface| replace:: :class:`~reahl.domain.systemaccountmodel.AccountManagementInterface`
.. |UrlBoundView| replace:: :class:`~reahl.web.fw.UrlBoundView`
.. |Bookmark| replace:: :class:`~reahl.web.fw.Bookmark`
.. |Slot| replace:: :class:`~reahl.web.ui.Slot`
.. |defineUserInterface| replace:: :meth:`~reahl.web.fw.UserInterface.define_user_interface`
.. |LoginSession| replace:: :class:`~reahl.domain.systemaccountmodel.LoginSession`
.. |currentSession| replace:: :meth:`~reahl.domain.systemaccountmodel.LoginSession.for_current_session`

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

Re-using only a domain model
----------------------------

.. sidebar:: What about database tables?

   Because you declared a dependency on `reahl-domain` in your .project
   file, Reahl is aware that this component needs tables. Refer to
   :doc:`persistence` for the commands to manage the database schema.

The user and system account functionality is in the `reahl-domain` component,
in the module :mod:`reahl.domain.systemaccountmodel`.

To be able to use it in your code, list the `reahl-domain` component as a dependency in the
`setup.cfg` file of your own project:

.. literalinclude:: ../../reahl/doc/examples/tutorial/login1bootstrap/setup.cfg
   :language: ini

.. note:: Remember, each time you change a `setup.cfg` file, as explained in :doc:`persistence`, you need to
          run: ``python -m pip install --no-deps -e .``


Use |currentSession| in your code to find the current |LoginSession|.


An |AccountManagementInterface| has
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

This creates a user and password using the password and email address in:

.. literalinclude:: ../../reahl/doc/examples/tutorial/login1bootstrap/login1bootstrap_dev/test_login1bootstrap.py
   :pyobject: LoginFixture





Re-using the user interface as well
-----------------------------------

.. sidebar:: Exercising `tutorial.login2bootstrap`

   This example sends out emails (eg, when you register). Run our fake
   email server to catch these. The fake email server just displays each
   email in the terminal where it runs. Start it before you use the
   example app:

   .. code-block:: bash

      reahl servesmtp

If you want to use the provided user interface as well, you can graft
an |AccountUI| onto its own new URL
underneath LoginUI. The URLs of the :class:`~reahl.web.fw.View`\ s of
|AccountUI| are then appended to that
URL.

Call |defineUserInterface| to graft |AccountUI| onto LoginUI.

In this call you need to specify which |Slot| name as declared by
|AccountUI| plugs into which |Slot| names we have available on MenuPage.

|AccountUI| expects a number of |Bookmark|\s to |UrlBoundView|\s that
contain legal text specific to your site. These |Bookmark|\s are sent
as an additional keyword argument to
|defineUserInterface|, from where
it will be delivered to |AccountUI|.

.. literalinclude:: ../../reahl/doc/examples/tutorial/login2bootstrap/login2bootstrap.py



