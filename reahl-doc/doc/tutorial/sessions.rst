.. Copyright 2013, 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
The web session problem
=======================

.. sidebar:: Examples in this section

   - tutorial.sessionscope
   - tutorial.sessionscopebootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


User sessions
-------------

You can persist objects on the server for the duration of a
|UserSession| by making them "session scoped". Session scoped
persisted objects are retained for as long as the |UserSession|
exists.

Reahl has functionality to let users log into your site as
:doc:`explained later on <loggingin>`. In the example here we build a
simplified version of similar functionality to show how session
scoped objects can be used.

The example consists of User object and a LoginSession object:

.. figure:: sessions.png
   :align: center
   :width: 50%


   A model for letting Users log in.


The application itself has two pages---a home page on which the
name of the User who is currently logged in is displayed, and a page
on which you can log in using your email address and a
password. 



Declaring the LoginSession
--------------------------

Create a LoginSession persisted class and decorate it using the
:meth:`~reahl.sqlalchemysupport.sqlalchemysupport.session_scoped`
decorator.

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscopebootstrap/sessionscopebootstrap.py
   :pyobject: LoginSession

The LoginSession keeps track of who is currently logged in through its
`.current_user` relationship to a User.

Just one trick: the `email_address` and `password` needed to actually
log someone in have to be provided by a user. That is why these are
:class:`~reahl.component.modelinterface.Field`\ s on the LoginSession -- they are to be linked to Inputs on the
user interface.  (The same goes for the `log_in` :class:`~reahl.component.modelinterface.Event`.)

To complete the model itself, here is the implementation of
User. Because only the paranoid survive, we've done the right thing
and refrained from storing our User passwords in clear
text. (Actually... for a real-life application password hashes should
be salted as well.) Besides that, there's really nothing much
unexpected to the User class:

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscopebootstrap/sessionscopebootstrap.py
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
to obtain the LoginSession for the current UserSession. The
`@session_scoped` decorator adds a method to the class it decorates
for this purpose. `LoginSession.for_current_session()` will check
whether there is a LoginSession for the current UserSession and create
one if necessary. Either way it returns what you expect:

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscopebootstrap/sessionscopebootstrap.py
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
UserSession-related problems for the framework. Understanding some of
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

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscopebootstrap/sessionscopebootstrap.py
   :pyobject: LoginForm

Can you spot the UserSession at work here? The input values and an
exception were available during the POST, but has to be saved in
session scope for them to be retrievable in a subsequent GET request
again.

The easy (but wrong) way around the problem could be for the framework
to send back a rendition of the same page (including exception) in
response to the POST request. That way all the information it needs to
re-render the login page would still have been available without the need
for a UserSession. This solution, however is not what was intended by
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

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscopebootstrap/sessionscopebootstrap.py

.. literalinclude:: ../../reahl/doc/examples/tutorial/sessionscopebootstrap/sessionscopebootstrap_dev/sessionscopebootstraptests.py
