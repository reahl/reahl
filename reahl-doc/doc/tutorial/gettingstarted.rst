.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Getting started guide
=====================

Follow this guide to get Reahl installed in your development
environment and to get a skeleton web application going.

Requirements
------------

This version of Reahl requires at least version 2.7 of Python. We're
exited about Python 3, but changing over to Python 3 is a big job
which we still have to get to!

Other projects used
-------------------

A Reahl application uses a number of other projects. Some of these are
programming frameworks and libraries that you'd also have to
understand to be able to use Reahl. A basic knowledge of each of these
tools will be a benefit if you want to follow this tutorial. (Where
relevant, the tutorial does point this out, so there's no need to rush
off and learn them all right now...)

The most important projects you should know about are:

 - `virtualenv <http://pypi.python.org/pypi/virtualenv>`_
 - `distribute <http://pypi.python.org/pypi/distribute>`_
 - `nosetests <https://nose.readthedocs.org/en/latest/>`_
 - `SqlAlchemy <http://www.sqlalchemy.org/>`_
 - `Alembic <https://pypi.python.org/pypi/alembic/>`_; and
 - `Elixir <http://elixir.ematia.de/trac/wiki>`_ (optional, but used
   in the tutorial).

There are also projects that are used totally behind the scenes, and
you need not understand anything about them except how to get them
installed on your platform. The most visible of these is a database
back-end. For this purpose `SQLite <http://www.sqlite.org>`_ and
`PostgreSQL <http://www.postgresql.org>`_ are currently
supported. SQLite is used throughout the tutorial. You need not
understand much about SQLite in order to follow the tutorial
though. Just ensure that it has been installed.


Installation 
------------

In order to install Reahl, you need some non-Python software installed
on your system first. Installing these will differ from platform to
platform. If you are on Ubuntu (or another Debian-based distribution
of Linux), all these can be installed by simply issuing:

.. literalinclude:: ../../../scripts/makeenv.sh
   :language: bash
   :start-after: # non-python packages
   :end-before: # END non-python packages

If you're not on a Debian-based distro, you will have to find and
install equivalents for your platform.
 
For a development environment, it is recommended to run Reahl within a
sandboxed Python environment provided by `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_.  Doing this means that
your main Python installation is left in the state it currently is,
and that you do not need permissions of restricted users to install
all the extra Python packages.

Virtualenv should have been installed with the packages listed above,
allowing you to create a new virtualenv with:

.. code-block:: bash

   virtualenv ./reahl_env
   
This creates a new directory `./reahl_env` with an isolated Python
environment inside it.

In order to work inside that isolated environment, you need to execute
the following on the command line:

.. code-block:: bash

   source ./reahl_env/bin/activate

After activating your new environment, the prompt of the command line
changes to reflect the environment that is currently active.

.. sidebar:: For interest's sake

   Installing reahl[sqlite,dev,doc] results in an installation of Reahl
   with Sqlite support, the Reahl development tools and
   documentation. This is all you need for following the tutorial.

   If you want to play with Postgresql too, you have to additionally install the
   following non-Python packages:

   .. literalinclude:: ../../../scripts/makeenv.sh
      :language: bash
      :start-after: # non-python packages for postgresql
      :end-before: # END non-python packages for postgresql

   ...before you install Reahl with PostgreSQL support using pip:

   .. code-block:: bash

      pip install reahl[postgresql]

With your `virtualenv` activated, Reahl can be installed into it by
issuing the following command:

.. code-block:: bash

   pip install reahl[sqlite,dev,doc]

.. note::

   This may run a while, as it installs all of the projects Reahl
   depends on as well. Some of these dependencies are installed and
   built from source, hence, this process needs **all** the non-Python
   packages mentioned above to be installed before you ``pip install``
   Reahl itself.



Creating a Reahl project
------------------------

In Reahl, everything -- even your web application -- is a component. The
very first thing to do in order to create a web application is thus to
create an empty component and specify which other components it
depends on.

To do that, create an empty directory (for example called
`hello`) and put a file inside it called `.reahlproject`::

  hello
  |   
  `-- .reahlproject

The presence of the .reahlproject file in a directory alerts the
`reahl` script (a tool used while in development) that the directory
contains a Reahl component. The contents of `.reahlproject` is XML
which, in its most basic form, merely lists the other components that
this one depends on.  The following example contains a list of all the
Reahl components needed for a basic web application:

.. code-block:: xml

   <project type="egg">
     <deps purpose="run">
       <egg name="reahl-component"/>
       <egg name="reahl-web"/>
       <egg name="reahl-sqlalchemysupport"/>
       <egg name="reahl-web-elixirimpl"/>
     </deps>
   </project>

These are all the necessary components for a basic web application:

reahl-component 
  The basic component infrastructure of Reahl, and as
  such a necessary dependency of any Reahl component.

reahl-web
  The Reahl web framework resides in the `reahl-web` component.  

reahl-web-elixirimpl
  Parts of the Reahl web framework are dependent on the specific
  database technology used. This component contains an implementation
  of these bits of the framework using `SqlAlchemy
  <http://sqlalchemy.org>`_ and `Elixir <http://elixir.ematia.de/>`_.  

reahl-sqlalchemysupport
  The `reahl-sqlalchemysupport` component provides the necessary glue
  to be able to use `SqlAlchemy <http://www.sqlalchemy.org/>`_ (and
  `Elixir <http://elixir.ematia.de/trac/wiki>`_) with a Reahl program.

  

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
`reahl` script.  That just means a less complicated file and more
functionality.

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

Each URL a user can visit is defined by a :class:`~reahl.web.fw.View`, and a bunch of related
 :class:`~reahl.web.fw.View`\ s  are organised into a :class:`~reahl.web.fw.Region`.

A basic web application is a single :class:`~reahl.web.fw.Region`. The code above shows how
this :class:`~reahl.web.fw.Region` is created by deriving a new class from :class:`~reahl.web.fw.Region`.  Such a
class should have an `assemble` method inside of which the basic
structure of the application is defined.

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
  |-- etc
  |   `-- web.config.py
  |-- hello.py
  `-- .reahlproject

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
