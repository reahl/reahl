.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.

Component framework - packaging and distributing more than just code
====================================================================

The Reahl component framework extends setuptools distribution packages to package and distribute more than just code.

Why this?
---------

Pip and PyPI do a good job of enabling the distribution of Python code. The projects ensure that when you install a
package you get all its correct dependencies as well.

When your code contains classes mapped by an ORM (such as SqlAlchemy) to tables in a database things become more
complicated:

The selection of packages used together in the same database cannot be foreseen by the individual package authors.
How do you create a database schema sufficient for the n packages you have decided to use together in your project?

What happens if a new version of a package requires a different database schema to a previous version? How
do you migrate the schema of an existing database to the new schema? This, in the context of there being several
packages mixed into a single database - with possible foreign key constraints forming dependencies between packages on
the database level.

The Reahl component framework is an attempt to build such distributable packages that are database-aware. It solves
all the surprisingly difficult accompanying problems. It calls such packages "components".

Components are not only database-aware. Each component can include:

- its own configuration, which will be read from a separate file.
- its own natural language translations to support multiple languages (i18n).
- annotations of the data and features of its domain objects which can be used by, for example,
  a web framework, to manipulate such objects.

.. note:: API docs
   Please see :doc:`for the complete API <index>`.


Defining a component
--------------------

A Reahl component is just a setuptools package with extra metadata.

The Reahl component infrastructure will recognise any package with an
`entrypoint <https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points>`_ named 'Egg', advertised
in the group 'reahl.eggs' which points to the :class:`reahl.component.eggs.ReahlEgg` class as a Reahl component.

One can create such a package using a setup.py, but due to all the extra metadata which is encoded into what setuptools
supports, it is easier to use a .reahlproject file instead. To use a .reahlproject file, you need to install `reahl-dev`
in your development environment where you will build packages.  With `reahl-dev` installed, the `reahl` commandline tool is
extended with extra commands, some of which are:

- reahl setup <usual arguments to setup.py>
  This invokes the normal functionality provided by setup.py, but uses the your .reahlproject file as a source.
- reahl build
  This builds distribution packages as defined in your `.reahlproject` file.
- reahl shell [-g]
  This runs a shell command for one or more projects, each with a `.reahlproject` file. The `-g` option
  generates a setup.py for the duration of the shell command's execution. Hence, to run a shell command
  which expects a setup.py (such as tox), you would run, for example::
    reahl shell -g tox
  And to just generate a setup.py, you copy the generated file elsewhere::
    reahl shell -g cp setup.py setup.generated.py
    

Reahl commandline
-----------------

The Reahl commandline is installed when you install `reahl-component` and is invoked with the command `reahl`.
It has several commands, and depending on what else you install, its list of commands is extended.

Installing `reahl-dev` gives it a bunch of commands that work with components that use .reahloroject files.
`reahl-dev`
~~~~~~~~~~~
  With reahl-dev installed, `reahl` gains commands that build packages, run arbitrary commands via setup.py, etc.

`reahl


    







Persistence
-----------


Database migration
------------------


Configuration
-------------


Internationalisation
--------------------


Context of execution
--------------------
