.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.

Component framework - packaging and distributing more than just code
====================================================================

The Reahl component framework extends setuptools distribution packages to package and distribute more than just code.

Why this?
---------

Pip and PyPI do a good job of enabling the distribution of Python code. The projects ensure that when you install a
package you get all its correct dependencies as well.

When your code contains classes mapped by an ORM (such as SqlAlchemy) to tables in a database, things become more
complicated:

The selection of packages used together in the same database cannot be foreseen by individual package authors.
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

.. seealso::

  :ref:`<create-component>`
     How to create a basic component using a `.reahlproject` file.

  `<../devtools/xmlref>`
     Reference documentation for a .reahlproject file.

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

Basics of .reahlproject
-----------------------

.. seealso::

  `<../devtools/xmlref>`
     Reference documentation for a .reahlproject file.

The `.reahlproject` file is XML, and contains a :ref:`\<project type="egg"\> <xml_project>` tag at its root.

In the <project> tag, there should be a :ref:`\<metadata\> <xml_metadata>` tag which specifies the name of
your project and its version.

There should also be one or more :ref:`\<version\> <xml_version>` entries for each minor version of your project,
including one that matches the major.minor part of the version specified in the metadata tag.

List all the dependencies of a particular version by adding a :ref:`\<deps purpose="run"\> <xml_deps>` inside the
appropriate <version> tag, and a :ref:`\<thirdpartyegg\> <xml_thirdpartyegg>` tag for each dependency.

Each time you change `.reahlproject`, be sure to regenerate the egg metadata:

.. code-block:: bash
   reahl develop -N

Reahl commandline
-----------------

The Reahl commandline is installed when you install `reahl-component` and is invoked with the command `reahl`. The set
of commands it offers depends on other Reahl components you install.

The commands in `reahl-commands` and `reahl-dev` pertain to the functionality of `reahl-component` as explained here.
Below is a more complete list of which commands other components add:

`reahl-dev`
  Commands to work with components defined by .reahlproject files instead of setup.py files.

`reahl-commands`
  Commands for working with the extra functionality provided by Reahl components. This includes managing databases,
  schemas and performing migrations as well as dealing with things like internationalisation and configuration.

`reahl-workstation`
  When using `the Reahl development Docker image <../devmanual/devenv.rst>` `reahl-workstation` is installed on the
  host machine to provide commands to help share GUI windows of terminal access via `Ngrok <https://ngrok.com>`_ or
  `Xpra <https://xpra.org>`_.

`reahl-webdev`
  Helpful commands when using web development using the Reahl web framework (`reahl-web`).

`reahl-doc`
  Commands for working with examples included in the overall Reahl documentation.


Persistence
-----------

.. seealso::

  `<../tutorial/persistence>`
     How to register persisted classes with your component and use the commandline to create a database schema.

The `reahl-component` infrastructure is extended by other Reahl components to be able to deal with differing
implementations of ORM or database systems.

To use a particular database, use the support package matching the database you want to use:

- `reahl-postgresqlsupport`
- `reahl-mysqlsupport`
- `reahl-sqlitesupport`

You also should use `reahl-sqlalchemysupport` which provides support for `SQLAlchemy <https://www.sqlalchemy.org/>`_
which is the only supported ORM.

Your component should list the required packages as well as `reahl-component` as its dependencies.

The <project> tag can also contain a single :ref:`\<persisted\> <xml_persisted>` tag. List each persisted class in
your component using a :ref:`\<class\> <xml_class>` tag inside the <persisted> tag.

You can now use the following commands (amongst others) from `reahl-commands` to manage the database::

    reahl createdbuser <config_directory>
    reahl createdb <config_directory>
    reahl createdbtables <config_directory>


Database migration
------------------

.. seealso::

  `<../tutorial/schemaevolution>`
     How to write migrations, define new versions of a Reahl component and upgrade a database to the new version.

The author of one component has no knowledge of other components which might inhabit the same database when used
together. However, when component A depends on component B, the author of A will know that B is being used. The classes
of A can be written such that they result in foreign keys to tables created by component B.

This creates a dependency on the database level with some implications:

1. When creating database tables, the tables of component B have to be created before those of A to ensure A's foreign
   key constraints will not be violated.
2. When changing the schema for B, the foreign key constraints of A (to B) first have to be removed before changes are
   made to the schema of B. Then the foreign key constraints of A can be reinstated possibly referring to renamed
   tables or columns in B.

If B's author brings out a new version of B in which tables or column names have changed as in (2) above, version 2 of
B will contain a |Migration| which takes care of changing B's schema from the old version.

If A's author wants to bring out a new version of A that uses B v2, A's author needs to write a |Migration| as part of
A v2 which adjusts the old A v1 foreign key constraints to be compatible with the changes in B v2.

In a real world project, there could be a large number of such components by diverse authors. In order to migrate
the whole database from one version to another, Reahl computes a dependency graph that spans all the versions of all
the components in play. It then runs different parts of each |Migration| in the correct order to ensure all database
level dependencies and constraints are honoured.

In order to facilitate this functionality, each version of a Reahl component can have its own set of |Migration|\s
which are performed when upgrading to that version from its predecessor. For this reason your <project> tag contains
one or more <version> tags. Since your project's dependencies can differ between versions, <deps purpose="run"> are
specified inside each <version> tag. The list of <version> tags in your project never changes - it is only added to.

A change in dependency or in database schema is seen as at least a minor version change, therefore <version> tags only
specify major.minor version numbers, not an additional patch version.

Each |Migration| is written such that user code only schedules each necessary change in a so-called 'phase'. The final
order in which the |Migration| itself and each individual phase of the |Migration| will be executed is determined by Reahl
at runtime taking all components into account.

If you schedule more than one action in a single phase in your |Migration|, these actions will retain their order
relative to one another.

The following useful commands are available related to migration::

    reahl migratedbdb <config_directory>
    reahl diffdb <config_directory>
    reahl listversionhistory <config_directory>
    reahl listdependencies <config_directory>



Configuration
-------------

.. seealso::

  `<../tutorial/owncomponent>`
     How to define and use configuration for your own component.



Internationalisation
--------------------

.. seealso::

  `<../tutorial/i18n>`
     How to make strings in your application translatable and work with translations in other languages.


Context of execution
--------------------
