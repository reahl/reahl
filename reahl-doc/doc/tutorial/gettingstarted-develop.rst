.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Get developing
==============

There are a few basic things you need to know when you develop a Reahl
application. Things like the layout of the source code making up an
application, dealing with Python eggs in development or how to manage
the database that underlies your application.

With Reahl, these topics are simple enough to be explained quickly,
and you can do everything by hand -- there's no need to ask a script
to build a skeleton application for you.

This explanation assumes `that you have installed Reahl in a
virtualenv, and that you have activated the virtualenv <gettingstarted-install>`_.

Creating a Reahl project
------------------------

.. sidebar:: Basic components used

   reahl-component 
     The basic component infrastructure of Reahl (a necessary dependency of any Reahl component).

   reahl-web
     The Reahl web framework itself.

   reahl-web-elixirimpl
     An implementation of technology-dependent bits of Reahl, using
     using `SqlAlchemy <http://sqlalchemy.org>`_ and `Elixir <http://elixir.ematia.de/>`_.  

   reahl-sqlalchemysupport
     The necessary glue for using `SqlAlchemy <http://www.sqlalchemy.org/>`_ (and
     `Elixir <http://elixir.ematia.de/trac/wiki>`_) with a Reahl program.

In Reahl, everything -- even your web application -- is a component
(and, Reahl components are Python eggs). The very first thing to do in
order to create a web application is thus to create an empty component
and specify which other components it depends on.

To do that, create an empty directory (for example called
`hello`) and put a file inside it called `.reahlproject`::

  hello
  └── .reahlproject

The presence of the .reahlproject file in a directory alerts the
`reahl` script (a tool used while in development) that the directory
contains the source code of a Reahl component. The contents of
`.reahlproject` is XML which, in its most basic form, merely lists the
other components that this one depends on.  The following example
contains a list of all the Reahl components needed for a basic web
application:

.. code-block:: xml

   <project type="egg">
     <deps purpose="run">
       <egg name="reahl-component"/>
       <egg name="reahl-web"/>
       <egg name="reahl-sqlalchemysupport"/>
       <egg name="reahl-web-elixirimpl"/>
     </deps>
   </project>

Preparing for development
-------------------------

The Reahl component infrastructure is really just a thin layer built
upon `Python eggs and the Python distribute package
<http://pypi.python.org/pypi/distribute>`_.

If you are familiar with Python Eggs, you would know that a programmer
usually creates a file called `setup.py` in the root directory of a
new Python Egg. This file contains a bit of Python code and
information about the Egg. It is usually executed via Python as a
command line program which can perform a number of special operations
on a Python Egg.

In Reahl, `setup.py` has been replaced by `.reahlproject` and the
`reahl` script. The actual (and more complicated) `setup.py` will be
generated from the information in `.reahlproject`. That just means a
less complicated file and more functionality.

However, any Reahl component is still a Python Egg, and as with all
Eggs, it should be prepared for use in a development environment.
This is done by executing the following from *within* the newly
created `hello` directory::

  reahl setup -- develop -N

Programmers familiar with Python Eggs would immediately recognise that
this is equivalent to what you'd do for a Python Egg with a
`setup.py`: `python setup.py develop -N`

.. note:: 

   The `reahl setup` command runs normal `setup.py` functionality,
   passing the parameters following after the "``--``" on to
   `setup.py`.


The simplest application
------------------------

The most basic running Reahl web application one can build is an
application with an empty home page. Here is an example of just such a
program -- you can put it in a file `hello.py` inside the `hello`
directory:

.. literalinclude:: ../../reahl/doc/examples/tutorial/hello/hello.py

In Reahl, a web application has a single `main window` which contains
the basic layout of the web site and the elements that would be
present on all pages. (Think header, footer, etc.)

Each URL a user can visit is defined by a :class:`~reahl.web.fw.View`,
and a bunch of related :class:`~reahl.web.fw.View`\ s are organised
into a :class:`~reahl.web.fw.Region`.

A basic web application is a single :class:`~reahl.web.fw.Region`. The
code above shows how this :class:`~reahl.web.fw.Region` is created by
deriving a new class from :class:`~reahl.web.fw.Region`.  Such a class
should have an `assemble` method inside of which the basic structure
of the application is defined.

In this case, a :class:`~reahl.web.ui.TwoColumnPage` is added as the main window. Also, a
:class:`~reahl.web.fw.View` is specified for the URL "/", and given the title "Home".


Configuration
-------------

A Reahl application has a configuration *directory* which may contain
many configuration files. This is because any given Reahl application
consists of a number of components -- each of which needs its own
configuration file. The vast majority of configuration information is
defaulted sensibly though, which means only a small number of
configuration items (and files) are necessary for a given application.

By convention the configuration directory used for development forms
part of its source code, and is called `etc`.

You can see what configuration is needed by using the `reahl-control`
script.  First, create an empty directory underneath that of your
component, named `etc`. Then try out the following command::

  reahl-control listconfig --missing --files --info etc 

Executing this yields a listing of missing configuration settings and
states for each setting where it should be set and what it means::

  Listing config for ./etc
  web.site_root       web.config.py    The Region class to be used as the root of the web application

Luckily, there's only one missing setting. Hence, we need to add the
file `web.config.py`, and specify one setting inside it.

Adding this file brings the total files needed so far to::

  hello
  ├── etc
  │   └── web.config.py
  ├── hello.py
  └── .reahlproject

As one may surmise from the name of the config file, Reahl config
files contain Python code. Inside these files, you can use dotted
notation to access or set different configuration settings.  Here is
what is needed in the `web.config.py` for our example project:

.. code-block:: python

   from hello import HelloApp

   web.site_root = HelloApp

You can see info about all the configuration settings used by executing::

  reahl-control listconfig --files --info etc

Or, to see the other possibilities related to `listconfig`, use::

  reahl-control listconfig -h etc


Preparing the database
----------------------

Before the web application can be started, you need to create a
database for it. This is necessary for any web application because the
web framework itself uses a database. By default, Reahl uses the
SQLite database.

Here we first create the database user, then the database itself and
finally the database tables needed::

  reahl-control createdbuser etc

  reahl-control createdb etc

  reahl-control createdbtables etc 

.. note:: 

   When running these commands you will notice warnings logged to the
   console. You can safely ignore these for now. Some config values
   are defaulted in ways that will only work in development, but may
   cause problems in a production environment. These warnings are meant
   to alert a user of such "dangerous" default config values.


Running it
----------

It is not necessary to install a web server in your development
environment. To run your application just execute the following from
the main `hello` directory::

  reahl serve etc

You should now be able to point your browser to http://localhost:8000
and see a page which looks empty and is titled "Home".


Checking out an example
-----------------------

You can get a local copy of this example by using the `reahl` script::

  reahl example tutorial.hello

You can also see what other examples are available by running::

  reahl listexamples
