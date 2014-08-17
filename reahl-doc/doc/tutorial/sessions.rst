.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
The web session problem
=======================

.. sidebar:: Examples in this section

   - tutorial.sessionscope

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

:ref:`Earlier on <factories>`, the oddities underlying a web
application are explained. In short -- there is no program that stays
in memory for the entire time during which a user uses a web
application. This is troublesome not only for web application
framework developers, but for programmers writing web applications as
well.

One crucial example of this issue is when you want users to be able to
log into your application. Let's say you have a separate login page on
which a user can log in. When the user does the actual logging in,
some code is executed on the server (to check login credentials,
etc). After this, the server sends a response back to the browser and
promptly releases from memory all the information thus gathered. 

Since nothing stays in memory between requests, what do you do? Where
do you save the User object (for example) representing the user who is
currently logged in so that it is available in subsequent requests?


User sessions
-------------

.. sidebar:: GUI Sessions

   Did you notice the similarity? For a GUI program, the user starts
   the application, and exits it when done using it. The GUI process
   itself is thus pretty much the GUI equivalent of a :class:`~reahl.systemaccountmodel.UserSession` on
   the web.

In order to deal with this problem, Reahl has the notion of a
:class:`~reahl.systemaccountmodel.UserSession`. A :class:`~reahl.systemaccountmodel.UserSession` is an object which represents one sitting
of a user while the user is interacting with the web application. When
a user first visits the web application, a :class:`~reahl.systemaccountmodel.UserSession` is created and
saved to the database. On subsequent visits, Reahl checks behind the
scenes (currently using cookies) for an existing :class:`~reahl.systemaccountmodel.UserSession` relating
to the browser which sent the current request. The :class:`~reahl.systemaccountmodel.UserSession` is
automatically destroyed if a specified amount of time passes with no
further interaction from the user.

The :class:`~reahl.systemaccountmodel.UserSession` provides a way for the programmer to persist objects
on the server side -- for a particular user while that user uses the
web application. The programmer can get to objects stored "in the
session" from any page. The stuff persisted as part of the :class:`~reahl.systemaccountmodel.UserSession`
typically disappears automatically when the :class:`~reahl.systemaccountmodel.UserSession` expires. An Object
that lives in the :class:`~reahl.systemaccountmodel.UserSession` is said to be *session scoped*.


An example: logging in
----------------------

To see how one can use the :class:`~reahl.systemaccountmodel.UserSession` in Reahl, let's build an
example which allows users to log in using an email address and
password. Reahl has a fancier built-in way of dealing with user logins
:doc:`explained later on <loggingin>`, but doing this from scratch
provides for a nice example.

Firstly, we'll need a bit of a model. This model needs some object
to represent the User(s) that can log in, and some session scoped object
that keeps track of who is currently logged in. How about a User
object then, and a LoginSession object:

.. figure:: sessions.png
   :align: center
   :width: 50%


   A model for letting Users log in.


The application itself will have two pages -- a home page on which the
name of the User who is currently logged in is displayed, and a page
on which you can log in by specifying your email address and a
password. There should also be a :class:`~reahl.web.ui.Menu` you can use to navigate to the
two different pages.


Declaring the LoginSession
--------------------------

In Reahl, if you want to persist an object just for the lifetime of a
:class:`~reahl.systemaccountmodel.UserSession`, that object should be persisted via the same persistence
mechanism used by your other persistent objects. It should also hold
onto the :class:`~reahl.systemaccountmodel.UserSession` so that it is discoverable for a particular
:class:`~reahl.systemaccountmodel.UserSession`.

When using SqlAlchemy, creating an object that has a `session scoped` lifetime is really
easy: just use the `@session_scoped` class decorator:

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscope/sessionscope.py
   :pyobject: LoginSession
   :prepend: @session_scoped

The responsibility of a LoginSession starts by keeping track of who is
logged in. That is why it has a `.current_user` attribute. Since
LoginSession is a persisted object itself, it is trivial to make it
hold onto another persisted object (User) via a relationship.

The other responsibility of the LoginSession is to actually log someone
in. The logic of doing this is quite easily followed by looking at
the implementation of the `.log_in()` method.

Just one trick: the `email_address` and `password` needed to actually
log someone in have to be provided by a user. That is why these are
:class:`~reahl.component.modelinterface.Field`\ s on the LoginSession -- they are to be linked to Inputs on the
user interface.  (The same goes for the `log_in` :class:`~reahl.component.modelinterface.Event`.)

To complete the model itself, here is the implementation of
User. Because only the paranoid survive, we've done the right thing
and refrained from storing our User passwords in clear text. Besides
that, there's really nothing much unexpected to the User class:

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscope/sessionscope.py
   :pyobject: User


Using a session scoped object
-----------------------------

In this example, the current LoginSession is needed for two
purposes. On the home page, we need to display who is logged in. On
the login page, we need the LoginSession to be able to link its
`.fields` and `.events` to :class:`~reahl.web.fw.Widget`\ s on that page.

In this example, we obtain the current LoginSession at the beginning
of `.assemble()` of the :class:`~reahl.web.fw.UserInterface`, and send it around as argument to the
login page. Most of that is old hat for you, except the bit about how
to obtain the LoginSession for the current :class:`~reahl.systemaccountmodel.UserSession`. The
`@session_scoped` decorator adds a method to the class it decorates
for this purpose. `LoginSession.for_current_session()` will check
whether there is a LoginSession for the current :class:`~reahl.systemaccountmodel.UserSession` and create
one if necessary. Either way it returns what you expect:

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscope/sessionscope.py
   :pyobject: SessionScopeUI


Dealing with DomainExceptions
-----------------------------

This example provides the perfect place for introducing the concept of
a :class:`~reahl.web.fw.DomainException`. A :class:`~reahl.web.fw.DomainException` is an exception that can be raised
to communicate a domain-specific error condition to the user. A
:class:`~reahl.web.fw.DomainException` can be raised during the execution of an :class:`~reahl.component.modelinterface.Action`.

In this example it may happen that a user supplies an incorrect
password. That's why an InvalidPassword exception is raised in this
case inside the `.log_in()` method of LoginSession.

When a :class:`~reahl.web.fw.DomainException` is raised, this poses some more
:class:`~reahl.systemaccountmodel.UserSession`\ -related problems for the framework. Understanding some of
the underlying implementation is necessary to explain this well. So,
please bear with us going down that route:

To display the login page, the web browser issues a request to the
server to GET that page. The browser then displays the response to
the user. Next, the user proceeds to type an email address and
incorrect password, and hits the 'Log in' button. The browser
communicates this :class:`~reahl.component.modelinterface.Event` to the server by issuing a POST request to the
server, sending the supplied information with. During the processing of
this request, our code raises the InvalidPassword exception.

When a :class:`~reahl.web.fw.DomainException` is raised, the Reahl framework ignores all
:class:`~reahl.web.fw.Transition`\ s defined. Instead, it takes note of the exception that
happened as well as the input supplied by the user. Then it instructs
the browser to do its initial GET request again. (Another way of
saying this is that the user is Transitioned back to the same :class:`~reahl.web.fw.View`.)

Upon the second GET, the login page is rendered to the user
again. However, since the framework made a note of the values typed
(and, incidentally, whether they were valid or not) the same values
appear pre-filled-in for the user again.

The exception (which was also noted down) is available too, and a
Reahl programmer should check whether there is currently an exception
and render its messsage if need be. See how this is done in the
implementation of LoginForm below.

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscope/sessionscope.py
   :pyobject: LoginForm

Can you spot the :class:`~reahl.systemaccountmodel.UserSession` at work here? The input values and an
exception were available during the POST, but has to be saved in
session scope for them to be retrievable in a subsequent GET request
again.

The easy (but wrong) way around the problem could be for the framework
to send back a rendition of the same page (including exception) in
response to the POST request. That way all the information it needs to
re-render the login page would still have been available without the need
for a :class:`~reahl.systemaccountmodel.UserSession`. This solution, however is not what was intended by
the designers of the HTTP standard, and hence can cause the
back-button of the browser to behave strangely. It could even result
in users submitting the same form twice by mistake (not a nice thing
if the form instructs the system to pay someone some money...). See a
more detailed discussion of this `elsewhere
<http://www.google.com/search?q=redirect+after+post>`_.


The final example
-----------------

Here is the complete code for the example, and a test putting it
through its paces:

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscope/sessionscope.py

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscope/sessionscope_dev/sessionscopetests.py
