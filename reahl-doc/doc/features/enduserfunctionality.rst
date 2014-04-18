.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Off-the-shelf functionality
===========================

.. sidebar:: Behind the scenes

   Reahl components are based on `Python eggs and the Python
   distribute package <http://pypi.python.org/pypi/distribute>`_.

Not everyone wants to build everything from scratch. Ideally, one
wants to glue together a couple of pre-built components (perhaps mixed
with some custom code also) when building a new web application.

User interface concepts in Reahl have been designed specifically to
allow bits of user interface to be plugged into many *different* web
applications without forcing the look or layout of the target web
application to conform to the reused part.

Reahl web applications can be composed of individually distributed,
reusable components. Each such component contains code (including user
interface code), information about its roots in the database and the
configuration information it needs to run. Infrastructure is provided
which allows one to create the database schema for an application that
consists of many such components, or migrate data from an older schema
to a newer one, etc.

Some pre-built components are also shipped with Reahl. 

The code below shows how one would use the shipped functionality that
would allow users to register and log into a website:

First, the web application needs to indicate that it uses these
components by adding them as dependencies to its `.reahlproject` file:

.. code-block:: xml

  <deps purpose="run">
    <egg name="reahl-domainui"/>
    <egg name="reahl-domain"/>
    ...
  </deps>

In code, the user interface needs to be grafted onto your web
application:

Any web application is accessed by means of the URLs it exposes.  The
URLs of a web application form a hierarchy.

A Region in Reahl is such a hierarchy -- but with a twist: A Region can
be grafted onto another Region. And that is exactly what happens in
the code above: An AccountApp is grafted onto ExampleApp, at the
URL "/accounts". Of course, ExampleApp is also just a Region
itself. We just chose to use it as the root of our entire application.

AccountApp has an URL "/login" (amongst others). But, from now on,
"/accounts/login" will refer to "/login" of the AccountApp grafted
onto "/accounts" in our web application.

.. code-block:: python

   class ExampleApp(Region):
       def assemble(self):
           # some other Regions added here, and the bookmarks asked from them

           self.define_region(u'/accounts', AccountApp,
                           {u'main_slot': u'maincontent'},
                           u'accounts', bookmarks)
  




