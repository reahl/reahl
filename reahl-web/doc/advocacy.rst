.. Copyright 2011, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Some adocacy: reasons why you may want to use Reahl
---------------------------------------------------

The Reahl web framework speeds up web application development and
results in high quality web applications.

Its approach is centered around two themes:

Firstly - when something is cumbersome to build, it makes sense to
reuse pre-built parts rather than to build everything you need from
scratch. Most web frameworks make reuse difficult or impossible. Reahl
enables reuse on many different levels and in different ways.

Secondly - usually a lot of the attention of a web application
programmer goes into low-level details regarding web technologies and
the oddities of the web as an application platform.  Reahl presents a
neat set of concepts that abstracts away all of the irrelevant and
complex details not directly related to the problem at hand.


Widgets and a normal programming language
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implementing anything on the web usually means that in addition to a
programming language, a programmer also needs to understand a wide
variety of technologies: HTML, CSS, JavaScript and often also various
configuration files in XML, some templating language and JavaScript
libraries.

In any one web application bits of code for all these various
technologies may lie scattered amongst several files and directories
that are difficult to keep track of.

Besides, it is cumbersome to keep up with these technologies and the
associated techniques for getting some effects right.  Working on that
low level is a bit like using assembly language.

With Reahl everything happens in one language - a programmer-friendly
one at that. Moreover, Each Widget hides behind it intricate
implementation details: bits of all the web technologies but even
extra dynamically generates URLs on the server (such as for embedded
images).

The concept of using Widgets to build user interfaces is certainly not
new - there are even several web frameworks that support this. But,
implementing Widgets on the web is difficult and web Widgets are often
limited in terms of what they can do. 

We'd like to think that Reahl got it right: it was built from the
ground up to enable the concept of a Widget and to allow everything a
Widget needs to be implemented.

The fact that a Widget is reusable means a lot: no need anymore to
understand all those details everywhere you use the Widget. 

And, when the programmer comes across a better way of implementing
that Widget (or to add features to it), then there's a single place to
go and change.  All existing locations where the changed Widget is
used will make use of this improvement with no extra effort.

Reahl also ships with a number of Widgets that can be used out of the
box. The shipped Reahl Widgets are carefully designed to:

 - make them accessible
 - make them search-engine friendly
 - make their look customisable with simple CSS; and
 - make them work on all major browsers

Reahl ships with very powerful Widgets representing things like
Inputs, Calendars, Tabs and more. Programmers new to Reahl can easily
combine these into complicated "windows". And, programmers who are
willing to learn more can build their own powerful Widgets.  There
literally is nothing visual on a web application that a programmer
cannot wrap into a Reahl Widget.


Validation of input
~~~~~~~~~~~~~~~~~~~

A user could still bypass these validations by turning off the
browser's JavaScript capabilities.  For this reason the exact same
checks will also be performed server-side. And, the checks will result
in exactly the same error messages.


Typically, a programmer would need to attend to a fair number of
things to be able to validate user input and execute server-side code
in response to user actions.  There's a long list of such potential
implementation details ranging from database transaction handling to
really human-unfriendly XML files somewhere (depending on the
framework).

A Reahl programmer can think in terms of *what* happens in the
application being built. Reahl takes care of *how* that is
implemented.  The code above is the only thing necessary - all in one
place, and simple to understand and read.

Notice also how an Event and the Widget's reaction to it are defined
separately from an actual Button.  This allows the programmer to
attach more than one Button to the same Event: Another small way to
write something once, and use it multiple times.  This feature comes
in handy in more complicated scenarios where multiple Widgets can set
off the same Event.

This way of dealing with user actions is very simple but has its
limitations.  Reahl provides some modifications to EventHandlers and
even special EventHandlers that allow a programmer to easily deal with
more complex web applications.

What you have just gained
~~~~~~~~~~~~~~~~~~~~~~~~~

Web applications present many different web pages to users. All of
these pages have important common elements. By developing one main
window per web application the programmer ensures that there is only
one place where these common elements are specified. That also means
one place to change if the main layout of the web application needs to
be changed.

However, the big deal here is that individual Views contain no
knowledge of the actual window they will be displayed in.

This means that a View can be developed and re-used in different web
applications that use entirely different main windows.

Reahl also ships with Widgets suitable for use as a main window - such
as the TwoColumnPage above.  When using these Widgets the main layout
of a web application's pages is already sorted out for the programmer.

This sort of layout of web pages is a tricky subject and difficult to
do in standards-compliant, accessible ways while catering for browser
incompatibilities.

By using something like TwoColumnPage the programmer in effect only
states what is needed. How that is accomplished is done by
TwoColumnPage.

What you have just gained
~~~~~~~~~~~~~~~~~~~~~~~~~

Simple examples would never be able to demonstrate the need for a
construct such as Region. Every programming language typically has an
analogous construct though - with the same goal:

A programmer needs the concept of a Region to be able to split a large
real world web application into smaller parts.  Added to that - such
smaller parts can be reused in totally different web applications.

In fact, Reahl includes a number of such re-usable Regions for common
functionality one would not want to be bothered with when developing a
new web application.  For instance, assume multiple users would need
to register and log into your web application.

You could opt to develop that functionality and the user interface
for it from scratch, or you could opt to just use a suitable Region
shipped with Reahl.

Web frameworks typically do not allow reuse on this level. Content
management systems have "plugins" that compare - but web frameworks do
not.  However, Content management systems typically do not have the
flexibility of a web framework.

Reahl gives you the best of both these worlds.

