.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Basic building blocks
=====================

The language of Reahl
---------------------

If you are a developer working on a web based user interface, you do
not want to spend your brain power thinking and talking about the
intricacies of the latest HTML/CSS/HTML standard, or how JavaScript is
dealt with differently on different browsers. You want to spend your
brain power on deciding where to put :class:`~reahl.web.ui.Button`\ s
and what should be on a particular window in order to create the most
effective user interface.

Reahl lets you write code in terms of high level concepts like :class:`~reahl.web.ui.Button`,
:class:`~reahl.web.ui.Panel` and :class:`~reahl.component.modelinterface.Event`. You do this in a single programming
language -- Python. Reahl gives you vocabulary that lets you think
about and code using the concepts that you care about.

You will have to learn this new language to find out what it is really
about. That is going to require reading through this tutorial. Reading
is hard work, I know. But it is worth it, promise!

This chapter of the tutorial contains an explanation of most of what's
new and fundamental to Reahl.

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

Have you noticed how ``SomeWidget.factory()`` is used sometimes in the
code so far, instead of just constructing the widget?

A web application has to be very economical about when it creates
what. A :class:`~reahl.web.fw.Factory` is merely an object that can be
used at a later time (if necessary) to create something--using the
arguments passed when the :class:`~reahl.web.fw.Factory` was created.

When creating a :class:`~reahl.web.fw.UserInterface`, for example, it
does not make sense to create all the
:class:`~reahl.web.fw.ViewFactory` instances it could possibly
have. We rather specify how they will be created eventually, if
needed.

Understanding the lifecycle of all these mechanics will give you a
deeper understanding if you're interested. That's explained next--but
you can skip this bit though if you really want to.


The lifecycle of user interface mechanics
-----------------------------------------


The user interface elements of a Reahl application are created each
time a request is received by the server. First the
:class:`~reahl.web.fw.UserInterface` is created (and its
``.assemble()`` called.  The :class:`~reahl.web.fw.UserInterface` then
determines which of the :class:`~reahl.web.fw.View`\ s defined on it
should be shown for the URL visited. Finally the
:class:`~reahl.web.fw.View` is created with its page and all related
:class:`~reahl.web.fw.Widget`\ s present on that page. The result of
all this is sent back to the browser in the form of HTML and other
files, but then all of these objects are thrown away on the web server.

You may have wondered why `.factory()` was used in the `.assemble()`
of the HelloUI (above), but not in the code of ReahllyBadPoem
earlier. Well, ReahllyBadPoem is a :class:`~reahl.web.fw.Widget` and in the code shown it is
being constructed. It makes sense that as part of its own construction
it should also construct all of its children :class:`~reahl.web.fw.Widget`\ s, doesn't it? Why
wait any longer?

Conversely, when a :class:`~reahl.web.fw.UserInterface` is instantiated, it does not make sense to
immediately instantiate all of the :class:`~reahl.web.fw.Widget`\ s of all of the  :class:`~reahl.web.fw.View`\ s  it
contains. After all the current user is only interested in one
particular :class:`~reahl.web.fw.View` at this point. So the complications are necessary here.
