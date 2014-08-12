.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
User interface basics
=====================

.. sidebar:: Examples in this section

   - tutorial.addressbook1

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

It is time to start work on the actual user interface of our
application. For a start, we'll only build a home page that lists all
our addresses.


Widgets
-------

:class:`~reahl.web.fw.Widget`\ s are the basic building blocks of a user interface. A :class:`~reahl.web.fw.Widget`
displays something to a user, and can be manipulated by the
user. :class:`~reahl.web.fw.Widget`\ s can have powerful behaviour that execute in a client
browser and/or on the server itself. A :class:`~reahl.web.fw.Widget` need not have
complicated behaviour, though. Simple :class:`~reahl.web.fw.Widget`\ s exist for things like
paragraphs, for example, which merely display something on screen.

A programmer constructs the user interface by stringing together a
number of existing :class:`~reahl.web.fw.Widget`\ s as children of another :class:`~reahl.web.fw.Widget`. For example,
let's string together two :class:`~reahl.web.ui.P`\ (aragraph)s onto a :class:`~reahl.web.ui.Panel`\ :

.. code-block:: python

   class ReahllyBadPoem(Panel): 
       def __init__(self, view):
           super(ReahllyBadPoem, self).__init__(view)
           self.add_child(P(view, text='Reahl is for real.'))
           self.add_child(P(view, text='You can use it in the real world.'))

To use an instance of the ReahllyBadPoem
:class:`~reahl.web.fw.Widget`, you add it as a child of another
:class:`~reahl.web.fw.Widget`. For example you can add it to the
``main`` column of the page used in our "hello" example like this:

.. code-block:: python

   class HelloPage(TwoColumnPage):
       def __init__(self, view):
           super(HelloPage, self).__init__(view)
           self.main.add_child(ReahllyBadPoem(view))


When rendered to a web browser, the resulting HTML would be:

.. code-block:: xml

   <div><p>Reahl is for real.</p><p>You can use it in the real world.</p></div>

:class:`~reahl.web.fw.Widget`\ s with complicated behaviour have a complicated
implementation. This implementation is, of course, hidden from the
programmer using such :class:`~reahl.web.fw.Widget`\ s. This makes using a complicated :class:`~reahl.web.fw.Widget`
just as simple as using the simple :class:`~reahl.web.fw.Widget`\ s in this example. Have a
look at the :doc:`tabbed panel example <../features/tabbedpanel>` to
see a more complicated :class:`~reahl.web.fw.Widget` in use.


A first-cut UserInterface for the address book application
----------------------------------------------------------

.. sidebar:: Remember the basics

   The basic elements of a user interface were :ref:`introduced with
   the Hello World application <the-simplest>`, but if you forgot,
   here is a quick summary:

   Each URL in a Reahl web application is defined by something called
   a :class:`~reahl.web.fw.View`. A
   :class:`~reahl.web.fw.UserInterface` is a collection of such
   :class:`~reahl.web.fw.View`\ s, as defined in its `.assemble()`
   method.

We need to create a :class:`~reahl.web.fw.UserInterface` for our
application, and add a :class:`~reahl.web.fw.View` to it, with a page
that contains the necessary :class:`~reahl.web.fw.Widget`\ s.

One creates a :class:`~reahl.web.fw.UserInterface` by inheriting from
:class:`~reahl.web.fw.UserInterface`, and overriding the method
`assemble()`. Inside this method, each :class:`~reahl.web.fw.View` is
defined:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/addressbook1.py
   :pyobject: AddressBookUI

AddressBookPage, in turn, is a :class:`~reahl.web.fw.Widget` which inherits from
:class:`~reahl.web.ui.TwoColumnPage`. This is pure lazyness:
:class:`~reahl.web.ui.TwoColumnPage` is a page with two columns, a
header and footer -- all nicely laid out already. We just add our
content to its `.main` column.

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/addressbook1.py
   :pyobject: AddressBookPage

Our content is in this example encapsulated in its own
:class:`~reahl.web.fw.Widget`, AddressBookPanel. This is not strictly
speaking necessary -- you could have made do with
AddressBookPage. Later on in the tutorial you will see though that
pages are often re-used with different contents. So, we're just
sticking to a habit here.

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/addressbook1.py
   :pyobject: AddressBookPanel

Note how AddressBookPanel is composed by adding children :class:`~reahl.web.fw.Widget`\ s to it in its constructor: first the heading, and then an AddressBox for each address in our database. An AddressBox, in turn only contains a :class:`~reahl.web.ui.P` with text gathered from the address it is meant to display:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/addressbook1.py
   :pyobject: AddressBox


.. _factories:

Factories
---------

.. sidebar:: Hint

   Usually, to obtain a factory for some kind of :class:`~reahl.web.fw.Widget`, you can
   call `.factory()` on its class. This method always takes the same
   arguments as the constructor of that class, but omits the first
   argument which always is the current `view`.

   Methods starting with `define_` are convenience methods that
   take a number of arguments and create a factory for something
   for you.  These will do something with the factory created (like
   adding a :class:`~reahl.web.fw.ViewFactory` to the :class:`~reahl.web.fw.UserInterface`), and then return the
   factory in case you need it further.

Have you noticed how ``.factory()`` is used in the example code so
far, instead of just constructing the widget?

A web application has to be very economical about when it creates
what. A :class:`~reahl.web.fw.Factory` is merely an object that can be
used at a later time (if necessary) to create something -- using the
arguments passed when the :class:`~reahl.web.fw.Factory` was created.

When creating a :class:`~reahl.web.fw.UserInterface`, for example, it
does not make sense to create all the
:class:`~reahl.web.fw.View` instances it could possibly
have. We rather specify how they will be created eventually, if
needed.

.. sidebar:: Test your understanding

   You may have wondered why `.factory()` was used in the
   `.assemble()` of the HelloUI, but not in the code of
   ReahllyBadPoem. Well, ReahllyBadPoem is a
   :class:`~reahl.web.fw.Widget` and in the code shown it is being
   constructed. It makes sense that as part of its own construction it
   should also construct all of its children
   :class:`~reahl.web.fw.Widget`\ s, doesn't it? Why wait any longer?

   Conversely, when a :class:`~reahl.web.fw.UserInterface` is
   instantiated, it does not make sense to immediately instantiate all
   of the :class:`~reahl.web.fw.Widget`\ s of all of the
   :class:`~reahl.web.fw.View`\ s it contains. After all the current
   user is only interested in one particular
   :class:`~reahl.web.fw.View` at this point. So the complications are
   necessary here.

Understanding the lifecycle of all these mechanics is useful:

The user interface elements necessary to fulfil a particular request
from a client browser are created briefly on the server for just long
enough to serve the request, and are then destroyed again.

This is what happens on the server to handle a request:

 - First the :class:`~reahl.web.fw.UserInterface` is created (and its
   ``.assemble()`` called).  
 - The :class:`~reahl.web.fw.UserInterface` then
   determines which :class:`~reahl.web.fw.View` (of the many defined on the :class:`~reahl.web.fw.UserInterface`)
   should be shown for the particular URL of the current request. 
 - Next, the relevant :class:`~reahl.web.fw.ViewFactory` is used to create the necessary 
   :class:`~reahl.web.fw.View`, its page and all related
   :class:`~reahl.web.fw.Widget`\ s present on that page. 
 - The result of
   all this is translated to HTML (and other things, such as JavaScript) and sent back to the browser
 - Lastly, all of these objects are thrown away on the web server.


.. _trying-out:

Try it out
----------

Finally, we have something we can run and play with in a web browser.

When you try to run this app, remember the following gotchas:

 - Your project needs a `.reahlproject` file in its root.
 - Run ``reahl setup -- develop -N`` each time you update
   the `.reahlproject` file
 - Use `reahl-control` to create the database and the database tables
   before you run your application. 
 - For now, drop your old database and recreate a new one if you
   changed anything related to its schema.
 - All persisted classes need to be added to the `.reahlproject` file.
 - If you have more than one version of a project, put them in
   directories of which the names differ! Reahl assumes that your
   component is named for the directory in which it resides.
 - Your app will not list any addresses at first, because there are none in the database yet!

Here is the complete source so far:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/addressbook1.py

