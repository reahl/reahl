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

To use an instance of the ReahllyBadPoem :class:`~reahl.web.fw.Widget`, you add it as a
child of another :class:`~reahl.web.fw.Widget`, like this:

.. code-block:: python

   self.add_child(ReahllyBadPoem(view))


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

There are common user interface elements present on all the different
URLs of a web application. It would be cumbersome to have to add these
to each :class:`~reahl.web.fw.View` repeatedly. For this reason, each web application has a
single :class:`~reahl.web.fw.Widget` acting as its *main window*. A main window contains the
elements that are present on all URLs of the web application.

Whether the user is visiting the '/some' URL or the '/other' URL, the
user is always presented with the very same main window, even though
some of its contents get plugged in on the fly and will differ depending
on the URL (thus :class:`~reahl.web.fw.View`) visited.

Think of  :class:`~reahl.web.fw.View`\ s  as being different  :class:`~reahl.web.fw.View`\ s  *of the same main window*. The
main window contains some elements, but it also contains blank areas
that are filled in (differently) by different  :class:`~reahl.web.fw.View`\ s .

.. figure:: views.png
   :align: center
   :width: 90%

   A main window with two different views.

A :class:`~reahl.web.ui.Slot` is a special :class:`~reahl.web.fw.Widget` that represents such a blank area. A
useful main window should thus contain one or more :class:`~reahl.web.ui.Slot`\ s that
can be filled in by individual  :class:`~reahl.web.fw.View`\ s .

A :class:`~reahl.web.fw.View` defines what the contents of the main window should be for a
particular URL by stating which :class:`~reahl.web.fw.Widget` should go into which :class:`~reahl.web.ui.Slot` of
the main window for that URL.

The example in the :doc:`gettingstarted` shows how a simple web application
is created as a single :class:`~reahl.web.fw.UserInterface`. The `web.site_root` configuration setting 
indicates which :class:`~reahl.web.fw.UserInterface` is to be used as the root of the web application.



See it in action
----------------

.. sidebar:: Get a copy of this example by running

   .. code-block:: bash

      reahl example features.slots

Below is the source code for an application that demonstrates these
ideas.

The application has two  :class:`~reahl.web.fw.View`\ s . Its main window (a CustomPage) contains
an :class:`~reahl.web.ui.HMenu` (a horisontal menu) which allows one to navigate between the
two  :class:`~reahl.web.fw.View`\ s  of the application.

The home page looks as follows:

   .. figure:: ../_build/screenshots/slots1.png
      :align: center

Notice the two bits of text.  Each paragraph was plugged into a
separate :class:`~reahl.web.ui.Slot` of the main window.

In "Page 2", the same main window is displayed, but with different
text in those :class:`~reahl.web.ui.Slot`\ s:

   .. figure:: ../_build/screenshots/slots2.png
      :align: center

A :class:`~reahl.web.ui.TwoColumnPage` is a handy :class:`~reahl.web.fw.Widget`, since it contains a sensible page
with all sorts of sub-parts to which one can attach extra :class:`~reahl.web.fw.Widget`\ s.  Of
interest here are its `.header` element (a :class:`~reahl.web.ui.Panel` positioned well for
holding things like menu bars), and two of its predefined :class:`~reahl.web.ui.Slot`\ s:
"main" and "secondary". These two slots represent the two columns of
the :class:`~reahl.web.ui.TwoColumnPage` :class:`~reahl.web.fw.Widget`: "main" is to the right, and fairly large,
whereas "secondary" sits to the left of it, and is narrower.

In this example, a CustomPage is derived from :class:`~reahl.web.ui.TwoColumnPage`. That way
the CustomPage inherits all the abovementioned niceties from
:class:`~reahl.web.ui.TwoColumnPage`. To ba a useful main window for this application,
CustomPage only needs to add an :class:`~reahl.web.ui.HMenu` to the `.header` of the
:class:`~reahl.web.ui.TwoColumnPage` on which it is based.

One thing not explained so far is the concept of a :class:`~reahl.web.fw.Bookmark`. For
purposes of this example you just need to know that a :class:`~reahl.web.fw.Bookmark` is how
one refers to a :class:`~reahl.web.fw.View`, and that :class:`~reahl.web.ui.Menu`\ s create their :class:`~reahl.web.ui.MenuItem`\ s from such
:class:`~reahl.web.fw.Bookmark`\ s.

.. literalinclude:: ../../reahl/doc/examples/features/slots/slots.py




Factories
---------

The idea of composing a user interface from :class:`~reahl.web.fw.Widget`\ s originated in the
world of graphical user interfaces. Reahl is an attempt to let you
program web applications using similar vocabulary. There is a
fundamental difference between web applications and GUI applications,
however:

When a user starts a GUI application, a single process is loaded into
the computer's memory and executed. This process sits there just
waiting for this single user to interact with it. Inside this process,
all the user interface elements are created by the program, and held
onto -- in memory -- until they are not needed anymore, or the program
is exited.

A web application is not such a simple, single entity. It is used by
many users simultaneously, and it does not have a single long-running
process that can hold onto :class:`~reahl.web.fw.Widget`\ s for each user using it. 

Parts of the web application execute on a server, and parts of it in
the many browsers of its many users. Each time a browser communicates
with the server, the server quickly loads just enough into the memory
of the server to be able respond to that specific request of the
specific user it is serving at that time. Once the server responds,
everything is removed from its memory again -- to free up the valuable
space for serving other users.

In a GUI application, one writes code to create a particular Window
with all its elements and keep the window and elements around in
memory for the duration of the program's execution.

In a web application, you need to write code that is able to create a
particular Window as and when needed -- and the same Window could be
recreated several times for a single user. The same Windows could also
be created slightly differently for different users (perhaps because
they have different security rights to the system).

This aspect of a web application is explicitly visible in a Reahl
application. Look at the following, for example:

.. code-block:: python

   class HelloApp(UserInterface):
       def assemble(self):
           self.define_main_window(TwoColumnPage)  
           self.define_view(u'/', title=u'Home')

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

Note that the specific :class:`~reahl.web.ui.TwoColumnPage` going to be used as main window
is not instantiated there.  The :class:`~reahl.web.fw.UserInterface` just keeps track of which class
to instantiate for obtaining a main window -- for when it needs a main
window.

In the next line, `define_view()` creates something called a
:class:`~reahl.web.fw.ViewFactory`.  Which is, simply put, just something that can be used to
create a :class:`~reahl.web.fw.View` later on.

A Reahl programmer needs to know about factories because they are
often used given the nature of web applications. For example:

.. code-block:: python

   class HelloApp(UserInterface):
       def assemble(self):
           self.define_main_window(TwoColumnPage)  
           home = self.define_view(u'/', title=u'Home')
           home.set_slot(u'main', P.factory(text=u'Look ma, no P\'s'))

Looking at the last line, you can see that it states that the 
'/' :class:`~reahl.web.fw.View` for any user will have its `main` :class:`~reahl.web.ui.Slot` filled with
a :class:`~reahl.web.ui.P` made a certain way.





The lifecycle of user interface mechanics
-----------------------------------------

User interface elements in Reahl are :class:`~reahl.web.fw.Widget`\ s. There are however other 
related “machinery” as well, such as  :class:`~reahl.web.fw.View`\ s  and :class:`~reahl.web.fw.UserInterface`\ s.

All of these things have a very short lifespan:

When an HTTP request comes into the web server, the correct :class:`~reahl.web.fw.UserInterface` is
first instantiated. The :class:`~reahl.web.fw.UserInterface` is used in turn to find and instantiate
the applicable :class:`~reahl.web.fw.View`. At this point, the main window is instantiated,
and the current :class:`~reahl.web.fw.View` is plugged into it. All the :class:`~reahl.web.fw.Widget`\ s needed by the
current :class:`~reahl.web.fw.View` are instantiated when the :class:`~reahl.web.fw.View` is plugged into the main
window.

At this point these elements of the user interface are ready to serve
the request. After doing its execution, the main window is rendered to
HTML, JavaScript and CSS files, which are sent back to the browser
where they will be executed further.

On the server, the :class:`~reahl.web.fw.UserInterface`, :class:`~reahl.web.fw.View`, main window and all related :class:`~reahl.web.fw.Widget`\ s
are discarded after sending back a response.

You may have wondered why `.factory()` was used in the `.assemble()`
of the HelloApp (above), but not in the code of ReahllyBadPoem
earlier. Well, ReahllyBadPoem is a :class:`~reahl.web.fw.Widget` and in the code shown it is
being constructed. It makes sense that as part of its own construction
it should also construct all of its children :class:`~reahl.web.fw.Widget`\ s, doesn't it? Why
wait any longer?

Conversely, when a :class:`~reahl.web.fw.UserInterface` is instantiated, it does not make sense to
immediately instantiate all of the :class:`~reahl.web.fw.Widget`\ s of all of the  :class:`~reahl.web.fw.View`\ s  it
contains. After all the current user is only interested in one
particular :class:`~reahl.web.fw.View` at this point. So the complications are necessary here.
