.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Get developing
==============

This chapter explains the very basics necessary to run a Reahl
application, at the hand of a simple "Hello World" example. These are
things like: the layout of the source code making up an
application; dealing with Python eggs in development; Reahl
configuration or how to manage the database that underlies your
application.

This explanation assumes `that you have installed Reahl in a
virtualenv, and that you have activated the virtualenv <gettingstarted-install>`_.

With Reahl, these topics are simple enough to be explained quickly,
and you can do everything by hand -- there's no need to ask a script
to build a skeleton application for you.

.. _the-simplest:

The simplest application
------------------------

Our example application has a single page sporting a paragraph that
says "Hello World!". Let's start by examining its Python source code:

.. literalinclude:: ../../reahl/doc/examples/tutorial/hello/hello.py

The application consists of only one
:class:`~reahl.web.fw.UserInterface`, which contains a single
:class:`~reahl.web.fw.View`, defined on its ``/`` URL. The contents of
the :class:`~reahl.web.fw.UserInterface` are defined in its
``.assemble()`` method.

To give the :class:`~reahl.web.fw.View` itself some contents,
HelloPage is derived from :class:`~reahl.web.ui.TwoColumnPage` -- a
handy Widget that represents an :class:`~reahl.web.ui.HTML5Page` which
already has a header, footer and two columns where you can add more
Widgets. In this case, we just add a paragraph of text
(:class:`~reahl.web.ui.P`) to the ``main`` column of the page.

Each URL a user can visit is defined by a :class:`~reahl.web.fw.View`,
and a bunch of related :class:`~reahl.web.fw.View`\ s are organised
into a :class:`~reahl.web.fw.UserInterface`.


.. _create-component:

Creating a Reahl component
--------------------------

In Reahl, everything -- even your web application -- is a component
(and, Reahl components are Python eggs). The very first thing to do in
order to create a web application is thus to create a component
containing your source code, including some metadata about the new
component.

To do that, create a directory (for example called
`hello`) and add two files and one directory to it::

  hello/
  ├── etc/          - A directory for configuration files
  ├── hello.py      - A Python file containing the source of the app
  └── .reahlproject - Metadata about this component

.. sidebar:: Basic components used

   reahl-component 
     The basic component infrastructure of Reahl (a necessary dependency of any Reahl component).

   reahl-web
     The Reahl web framework itself.

   reahl-web-declarative
     An implementation of technology-dependent bits of Reahl, using
     using `SqlAlchemy <http://sqlalchemy.org>`_ and `Elixir <http://elixir.ematia.de/>`_.  

   reahl-sqlalchemysupport
     The necessary glue for using `SqlAlchemy <http://www.sqlalchemy.org/>`_ (and
     `Elixir <http://elixir.ematia.de/trac/wiki>`_) with a Reahl program.

The presence of the .reahlproject file in a directory alerts the
`reahl` script (a tool used while in development) that the directory
contains the source code of a Reahl component. The contents of
`.reahlproject` is XML which, in its most basic form, merely lists the
other components that this one depends on.  The following example
contains a list of all the Reahl components needed for a basic web
application (go ahead and copy this into your `.reahlproject`):

.. code-block:: xml

   <project type="egg">
     <deps purpose="run">
       <egg name="reahl-component"/>
       <egg name="reahl-web"/>
       <egg name="reahl-sqlalchemysupport"/>
       <egg name="reahl-web-declarative"/>
     </deps>
   </project>

.. _preparing-for-development:

Preparing for development
-------------------------

Before you can do anything with a new component, you need to register
it with your development environment. This is done by executing the
following from *within* the newly created `hello` directory::

  reahl setup -- develop -N

Programmers familiar with Python Eggs would immediately recognise that
this is equivalent to what you'd do for a Python Egg with a
`setup.py`: ``python setup.py develop -N``: the Reahl component
infrastructure is really just a thin layer built upon `Python eggs and
the Python distribute package
<http://pypi.python.org/pypi/distribute>`_.

When using Python Eggs, a programmer usually creates a file called
`setup.py` in the root directory of a new Python Egg. This file
contains a bit of Python code and information about the Egg. It is
usually executed via Python as a command line program which can
perform a number of special operations on a Python Egg.

In Reahl, `setup.py` has been replaced by `.reahlproject` and the
`reahl` script. The actual (and more complicated) `setup.py` will be
generated from the information in `.reahlproject`. That just means a
less complicated file and more functionality. However, any Reahl
component is still a Python Egg, and as with all Eggs, it should be
prepared for use in a development environment.

.. note:: 

   The `reahl setup` command runs normal `setup.py` functionality,
   passing the parameters following after the "``--``" on to
   `setup.py`.


Configuration
-------------

The next step is to give some basic configuration for the application,
after which you need to initialise the application database.

The configuration for a Reahl program is split into different files
located in :ref:`the configuration directory you created earlier
<create-component>`. To see what configuration is missing, use the
`reahl-control` script from within your `hello` directory, like this::

  reahl-control listconfig --missing --files --info etc 

Executing this command shows the configuration settings missing from
the `etc` directory, and states in which file each setting should be
set (and also what each setting means)::

  Listing config for ./etc
  web.site_root       web.config.py    The UserInterface class to be used as the root of the web application

There's only one missing setting. Hence, we need to add the file
`web.config.py`, and specify one setting inside it. As one may surmise
from the name of the config file, Reahl config files contain Python
code. Inside these files, you can use dotted notation to access or set
different configuration settings.  Here is what is needed in the
`web.config.py` for our example project:

.. code-block:: python

   from hello import HelloUI

   web.site_root = HelloUI


A Reahl application has a configuration *directory* which may contain
many configuration files because any given Reahl application
consists of a number of components.  Each component needs its own
configuration file. The vast majority of configuration information is
defaulted sensibly though, which means only a small number of
configuration items (and files) are necessary for a given application.

By convention the configuration directory used for development forms
part of its source code, and is called `etc`.

After adding this file, the total files needed so far are::

  hello/
  ├── etc/
  │   └── web.config.py
  ├── hello.py
  └── .reahlproject


You can see info about all the configuration settings used by executing::

  reahl-control listconfig --files --info etc

Or, to see the other possibilities related to `listconfig`, use::

  reahl-control listconfig -h etc


Preparing the database
----------------------

The last step necessary before the web application can be started is to create a
database for it. This is necessary for any web application because the
web framework itself uses a database. The default configuration
settings are set up to use a SQLite database.

You need to create the database user, then the database itself and
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

.. note:: 

   Remember, :ref:`like with any other project
   <preparing-for-development>`, you need to run ``reahl setup -- develop
   -N`` inside the local copy of the example before you try to run it.

You can also see what other examples are available by running::

  reahl listexamples
