.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
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

A UserInterface in Reahl is such a hierarchy -- but with a twist: A UserInterface can
be grafted onto another UserInterface. And that is exactly what happens in
the code above: An AccountUI is grafted onto ExampleUI, at the
URL "/accounts". Of course, ExampleUI is also just a UserInterface
itself. We just chose to use it as the root of our entire application.

AccountUI has an URL "/login" (amongst others). But, from now on,
"/accounts/login" will refer to "/login" of the AccountUI grafted
onto "/accounts" in our web application.

.. code-block:: python

   class ExampleUI(UserInterface):
       def assemble(self):
           # some other UserInterfaces added here, and the bookmarks asked from them

           self.define_user_interface('/accounts', AccountUI,
                           {'main_slot': 'maincontent'},
                           'accounts', bookmarks)
  




