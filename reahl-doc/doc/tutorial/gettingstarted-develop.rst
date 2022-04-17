.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |View| replace:: :class:`~reahl.web.fw.View`
.. |UserInterface| replace:: :class:`~reahl.web.fw.UserInterface`
.. |HTML5Page| replace:: :class:`~reahl.web.ui.HTML5Page`
.. |WidgetFactory| replace::  :class:`~reahl.web.fw.WidgetFactory`



Hello World!
============

.. sidebar:: Other projects used

    - `virtualenv <https://pypi.python.org/pypi/virtualenv>`_
    - `setuptools <https://pypi.python.org/pypi/setuptools/>`_
    - `pytest <https://pytest.org/>`_
    - `SqlAlchemy <http://www.sqlalchemy.org/>`_
    - `Alembic <https://pypi.python.org/pypi/alembic/>`_
    - `SQLite <http://www.sqlite.org>`_
    - `PostgreSQL <http://www.postgresql.org>`_
    - `Babel <http://babel.pocoo.org>`_

This explanation assumes :ref:`that you have installed Reahl in a
virtualenv, and that you have activated the virtualenv <install-reahl-itself>`.

Run it
------


You can get a local copy of *this* example by using the
`reahl` script and then run the example by doing::

  reahl example tutorial.hello
  cd hello
  python -m pip install --no-deps -e .
  reahl createdbuser etc
  reahl createdb etc
  reahl createdbtables etc
  reahl serve etc

Then browse to http://localhost:8000.

There is :doc:`more to know about running examples
<gettingstarted-examples>`. For now, you can see what other examples
are available by running::

  reahl listexamples


.. _the-simplest:

Source code
-----------

.. literalinclude:: ../../reahl/doc/examples/tutorial/hello/hello.py

In Reahl, each URL a user can visit is defined by a
|View|, and a bunch of related |View|\s are organised into a
|UserInterface|.

* The application consists of only one |UserInterface|: HelloUI.
* HelloUI contains a single |View|, tied to the ''/'' URL.
* The URLs (and thus |View|\s) defined by a |UserInterface| are set up
  in its ``.assemble()`` method.
* HelloPage is an |HTML5Page|, which is a |Widget| like everything
  else on a Reahl user interface.
* To give HelloPage some contents, just add a paragraph of text
  (:class:`~reahl.web.ui.P`) to the `.body` of the page.
* In the definition of the |View|, use a |WidgetFactory| for your
  HelloPage instead of constructing an actual HelloPage: the
  |WidgetFactory| is used to create a HelloPage, but
  only once that URL is visited.



.. _create-component:

The 'hello' component
---------------------

.. sidebar:: Required components

   reahl-component
     Our component infrastructure.

   reahl-web
     The Reahl web framework.

   reahl-sqlalchemysupport
     Allows you to use `SqlAlchemy <http://www.sqlalchemy.org/>`__ in your component.

   reahl-web-declarative
     Technology-dependent parts of the framework written using `SqlAlchemy <http://sqlalchemy.org>`__.

The 'hello' project is a :doc:`Reahl component <../component/introduction>`.

.. warning:: The word *component* is used by different people for different things.

   - We call a user interface element a :class:`~reahl.web.fw.Widget`
   - We use *component* to refer to a `project
     <https://packaging.python.org/glossary/#term-project>`_ that is
     packaged as `a distribution package
     <https://packaging.python.org/glossary/#term-distribution-package>`_ and
     which additionally uses the :doc:`reahl component infrastructure <../component/introduction>`.

Create a component by `creating a setuptools package with 'pyproject.toml' and 'setup.cfg' files <define_component>`_.

You did this above by running::

  reahl example tutorial.hello


The directory structure of `hello`::

  hello/
  ├── etc/           - A directory for configuration files
  ├── hello.py       - A Python file containing the source of the app
  ├── pyproject.toml - The standard (PEP518) python build system configuration
  └── setup.cfg      - Normal configuration for setuptools 


The `pyproject.toml` file should include as build dependencies: 'setuptools, 'toml' and 'reahl-component-metadata':

.. literalinclude:: ../../reahl/doc/examples/tutorial/hello/pyproject.toml

The `setup.cfg` file contains info about the component. To start,
just give your component a name, specify an empty 
`component =` option and list the requirements of your component:

.. literalinclude:: ../../reahl/doc/examples/tutorial/hello/setup.cfg

More information on the Reahl component infrastructure is in :doc:`its own introduction <../component/introduction>`.     
     
.. _preparing-for-development:

Development mode
----------------

Components are `setuptools projects
<https://setuptools.readthedocs.io>`_ with some extra metadata added.

When you are still busy developing a project, install your project in
`"development mode"
<http://setuptools.readthedocs.io/en/latest/setuptools.html?#development-mode>`_. From
*within* the newly created `hello` directory, run::

  python -m pip install --no-deps -e .



Configuration
-------------

You need one config setting to be able to run an application. In the config directory (`etc`), add a file
`web.config.py`::

  hello/
  ├── etc/
  │   └── web.config.py
  ├── hello.py
  ├── pyproject.toml - The standard (PEP518) python build system configuration
  └── setup.cfg      - Normal configuration for setuptools 

Config files contain Python code, but you can use dotted notation to
access settings:

.. code-block:: python

   from hello import HelloUI

   web.site_root = HelloUI


Each component you use has its own config file in `etc`. Most are
optional. To see what is missing, do::

  reahl listconfig --missing --files --info etc

Here's example output::

  Listing config for ./etc
  web.site_root       web.config.py    The UserInterface class to be used as the root of the web application


You can see info about all the configuration settings used by executing::

  reahl listconfig --files --info etc

Or, to see the other possibilities related to `listconfig`, use::

  reahl listconfig -h etc


Prepare the database
--------------------

Even a Hello World app needs a database. To create it, do::

  reahl createdbuser etc

  reahl createdb etc

  reahl createdbtables etc

.. note::

   Ignore the warnings about "dangerous" default config settings for
   now. They are meant to alert you to not use these settings in a
   production environment.


Development web server
----------------------

To run your application just execute the following from
the main `hello` directory::

  reahl serve etc

The web server monitors the current directory recursively, and
restarts when a file change is detected. For more options, see::

  reahl serve -h


