.. Copyright 2010, 2011, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
The context in which code executes
----------------------------------

UserSession
~~~~~~~~~~~

In a multi-user, server based system there is the concept of a
UserSession.  A UserSession keeps track of who the current user is,
whether this person is logged on, how long the user has been logged in
for, etc.

On the web, for example, many frameworks keep track of the user's
"session data" and each framework has some way of doing this. It
enables the server to relate subsequent HTTP requests to one sitting
as it were.  However, the idea of a UserSession can apply to a non
web-based server or even standalone program as well.

ExecutionContext
~~~~~~~~~~~~~~~~

Most code inside a system executes within an ExecutionContext.  The
ExecutionContext is an object that can easily be obtained from
anywhere in the code without the need for passing it as an argument.

The ExecutionContext keeps track of the following things:
 - the configuration used by the system (configuration, as in variables set in config files)
 - the current database transaction
 - the current UserSession

The ExecutionContext is short-lived: when a user event triggers some
code to execute on the server, that code runs inside an
ExecutionContext. The purpose of the ExecutionContext is to allow
access to its variables from anywhere in the code and hide concurrency
and other issues.

[There are different ways of implementing an ExecutionContext. One is
to make it a thread-local variable. We do it a different way - the
focus in this narrative is on the concept, not its implementation.]

State machine anomalies
~~~~~~~~~~~~~~~~~~~~~~~

Usually a finite state machine is in total control of which state it
is in. In this case, however, it is possible for a user to jump to an
arbitrary View by following a link or a bookmark, for example.  And,
it may be that that View is not currently valid according to the
finite state machine.  For example, it does not make sense to present
a View allowing a user to log in while the user is already logged in -
in this case the user should rather be logged out first or directed
elsewhere.

To mitigate this sort of problem, Preconditions can be added to
particular Views.  If the Controller computes the current View, it
first checks the Preconditions of that View.  If a Precondition fails,
it raises an exception which has the effect of forcing the user to a
different View.

Currently, there are two such exceptions: a Redirect and a Detour.

Redirecting the user somewhere else, merely directs the browser to a
valid View for the given situation.

Sending the user on a Detour also redirects to a different View, but
with a difference.  While redirecting, it also specifies a View to
come back to after it has completed what was necessary on the
"Detour".

[motivating examples necessary]
[more on how to return - ReturnTo]




Validation detail
-----------------

A number of Constraints can be added to each Field. A Constraint has
two methods related to validation: "validate_input" and
"validate_parsed".  To implement a specific Constraint, one subclasses
from Constraint and overrides one or more of these methods.
"validate_input" is executed to check that a unicode string typed by a
user is formatted correctly. Upon validation, this method is first
called to ensure the input is valid. Next, the value is translated
from the unicode string to a python object.  This value is then passed
to a call to "validate_parsed" to do further validation checks on the
python object resulting from having translated it from a string.  To
create a new Field, one subclasses from Field and overrides its
"parse_input" method.  This method expects validly formatted input,
and returns a python object constructed from that input.


Validation is done on a Field when an attempt is made to input values
into it (a method is called to do this).  Upon validation, each
Constraint is checked in turn, the first one that fails is considered
to be the current validation error.  This Constraint is then raised as
an exception.


A Field can also be asked to set its parsed value on its associated
domain object.



DomainExceptions
----------------

Both validation and the firing of an Event is fired inside a
substransaction.  If a DomainException is raised by code while this is
happening, the exception contains a flag which specifies whether or
not database changes (in that sub-transaction) should be committed or
rolled back. In either case however, the exception is persisted
(linked to its form), and all input supplied to by the form is also
saved.  The browser is then redirected to the same page from which the
form was submitted.

When an Event fires without producing a DomainException, any possible
saved DomainExceptions or user supplied input linked to its form are deleted.

A ValidationException (raised when validation fails) is also a form of
DomainException.


Flows
-----------------

A Flow specifies how a user is transitioned between several pages, depending 
on which events the user triggers along the way in each page.

A Face can contain several Flows.

A Flow is associated with a Controller. Some Flows return, some just end on
a particular page.

A Detour is a way of "calling" a Flow. It will take the user to a flow 
and make sure the user is returned to where it was originally "called" from.

3 flows:
register    ( /register/apply -> /register/congrats )  (/register)
logoutfirst ( /logoutfirst/logout -> 0 )               (/logoutfirst)
verify      ( /verify/login -> /verify/thanks )        (/verify)

[1.1]GET      /register
[1.1][2.1]REDIRECT /logoutfirst?returnTo=/register
POST REDIRECT
[1.1]GET /register
POST (submit) REDIRECT
[1.2]-GET /congratulations

[3.1]GET /verify
POST (submit) REDIRECT
[4.1]GET /prefs/privacy
POST (submit) REDIRECT
[4.2]GET /prefs/personalInfo
POST (submit) REDIRECT
[3.2]GET /prefs/thanks


GET /df
POST /df/_login_events REDIRECT
GET /df
[4.1] DETOUR GET /prefs/privacy?returnTo=/df
[4.2]
POST (submit) REDIRECT (get next out of url)
GET /df


CSS framework...
----------------
Each widget can be assembleed to a CSS class identifying it.  We package
basic CSS using that class to do the basic layout of the Widget.


A particular site can also supply extra CSS to add site-specific styling, such as colors, fonts, etc.

Opsoek na standards in hierdie gebied...
 - Input word gegenerate met class="error"as hy validation fail?
 - Ekstra label word gegenerate met class=error met die error message as text, as validation fail
 - By BlockLabelledInputs bv, word die class=error ook gekppel aan sy main container
 
 
Classes gebruik:
 reahl-button
 reahl-labelledinput
 reahl-labeloverinput
 reahl-horizontal
 reahl-vertical
 reahl-haccordion
 
 reahl-priority-secondary
 reahl-priority-primary
 error
 reahl-state-error
 
 html5-active
 
 the Yui-classes (first, yui-u etc)


HAccordion widget
-----------------
What it is, keeps state, etc





On the web, the session also keeps track of UI state. Ie: the slot_contents for that session.



Each user has a profile.  The profile states what the user's timezone, language and other locale preferences are.




We do not use reahl.sqlalchemysupport.session in code, all db controlling happens via the orm_control which can be obtained from the config.



Daar is iets soos 'n validation exception.
Daar is iets soos 'n constraint.

Ons add constraints by 'n field, elke c check iets, en, if not ok, gooi validation exeption (passing homself).


Validation:
 validation is 2-step process:
  validate_input
  validate(parsed)
 dit beteken validate die value regtig - don't care about required/not
 
Field is validated only if it has a value and is required

Constraints
 - hoe main_windows werk
 - hoe validate hulle
 - hoe render hulle in js/html
   - hoe error messages by js uitkom
 - dealing with required
