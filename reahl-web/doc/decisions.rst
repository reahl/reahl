.. Copyright 2009, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 

Important design decisions
==========================


The ExecutionContext idea:
 Passing all this info around in parameters clutters code. You add
 parameters to methods which logically do not need them. This is an
 example of coding the HOW instead of the WHAT.

The fact that the UserSession is not only a Web thing, but that it
embodies the responsibilities around logging in/not etc.

Use of Widgets, written in a programming language instead of HTML.
How these generate all the needed html, JS and CSS.

Standardisation on Jquery and jquery-ui.

Standardisation on html5. Because we want to be aligned with the
future as well as possible.  HTML5 that does not exist now can be
implemented in JS; what we cannot fake like this, we ignore.  HTML5
elements and details will work on (html5) browsers with JS switched
off.

Not using jquery-ui CSS framework for our own stuff: they are not as
aligned with HTML5 as we are.

Using standard, and up to date CSS selectors and features. Also - to
be aligned with the future.  We can fake this for browsers that do not
have it with JS.

Using standards

Ignoring performance until it becomes a problem.

Standardisation on sqlalchemy.




Important rules of thumb
========================

Write a test for each logical fact / statement you'd have in an
explanatory narrative.

Write code (including tests) with the aim of explaining WHAT you are
doing/representing instead of its stating HOW you are doing it.

If a test starts to suffer from combinatorial explosion, split it into
smaller tests, one for each variable.

Use EmptyStub instance instead of just None in a test, that way
breakage is easier to debug.