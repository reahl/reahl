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
supports, it is easier to use a .reahlproject file instead.





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