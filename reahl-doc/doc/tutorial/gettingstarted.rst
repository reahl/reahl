.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Getting started guide
=====================

Follow this guide to get Reahl installed in your development
environment and to get a skeleton web application going.

We have split the guide into parts:

.. toctree::

   gettingstarted-install
   gettingstarted-develop


Requirements
------------

This version of Reahl requires at least version 2.7 of Python. We're
excited about Python 3, but changing over to Python 3 is a big job
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

