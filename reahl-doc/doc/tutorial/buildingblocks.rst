.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Basic building blocks
=====================

This chapter introduces a few concepts that are fundamental to Reahl.


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
           self.add_child(P(view, text=u'Reahl is for real.'))
           self.add_child(P(view, text=u'You can use it in the real world.'))

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


Structural elements of a user interface
---------------------------------------

Each URL in a Reahl web application is defined by something called a
:class:`~reahl.web.fw.View`.

A collection of  :class:`~reahl.web.fw.View`\ s  are usually created to work together with one
another.  One :class:`~reahl.web.fw.View` may refer to another in order to transition a user
from the one :class:`~reahl.web.fw.View` to the other, for example. A collection of  :class:`~reahl.web.fw.View`\ s 
that are designed to work together like this is called a :class:`~reahl.web.fw.UserInterface`.

A simple web application is just that: a collection of  :class:`~reahl.web.fw.View`\ s  designed to 
work together. Complicated web applications may be composed of several
different :class:`~reahl.web.fw.UserInterface`\ s (as explained much later).


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

Have you noticed how ``HelloPage.factory()`` is used :ref:`in the code
for our Hello World app <the-simplest>`, instead of just constructing
the widget?

A web application has to be very economical about when it creates
what. A :class:`~reahl.web.fw.Factory` is merely an object that can be
used at a later time (if necessary) to create something -- using the
arguments passed when the :class:`~reahl.web.fw.Factory` was created.

When creating a :class:`~reahl.web.fw.UserInterface`, for example, it
does not make sense to create all the
:class:`~reahl.web.fw.View` instances it could possibly
have. We rather specify how they will be created eventually, if
needed.

Understanding the lifecycle of all these mechanics is useful:


The lifecycle of user interface mechanics
-----------------------------------------

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

