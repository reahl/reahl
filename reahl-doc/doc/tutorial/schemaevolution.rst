.. Copyright 2013, 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.


.. |Migration| replace:: :class:`~reahl.component.migration.Migration`
.. |Configuration| replace:: :class:`~reahl.component.config.Configuration`
.. |ExecutionContext| replace:: :class:`~reahl.component.context.ExecutionContext`

.. _database-schema-evolution:

Database schema evolution
=========================

.. sidebar:: Examples in this section

   - tutorial.migrationexamplebootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


.. sidebar:: Behind the scenes

   Important parts of the database migration functionality in Reahl is
   done using the `Operations` object of the `Alembic
   <https://pypi.python.org/pypi/alembic>`_ project.

.. note::
   
   The Sqlite database itself does not support migration of existing
   data very well, and as a result migration is restricted to
   PostgreSQL and MySQL databases, even though MySQL also has some migration quirks.
   See these posts for more information on
   the issue: `one of the last bullets of goals of alembic
   <https://github.com/sqlalchemy/alembic>`_ and `Christopher Webber's
   rant about the issue <https://dustycloud.org/blog/sqlite-alter-pain/>`_.


Once your application is running in production you may want to
develop a new version. If code changes in the new version require
changes to the database schema, you need to migrate the current
database to preserve its data while matching the new schema.


A migration example
^^^^^^^^^^^^^^^^^^^

The example migration is quite elementary so the default sqlite database can be used
to illustrate the concept.

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexamplebootstrap/migrationexamplebootstrap.py
   :pyobject: Address

To try it out, do:

.. code-block:: bash

   reahl example tutorial.migrationexamplebootstrap
   cd migrationexamplebootstrap
   python -m pip install --no-deps -e .
   reahl createdbtables etc
   python migrationexamplebootstrap_dev/create_demo_data.py etc/

Doing all of this simulates an application that ran somewhere for a
while, with some data in its database.

Now change the application to a newer version:

- comment out the 'TODO' version of `added_date` in the Address class, and uncomment the
  version with the Column (this simulates a change in schema)
- edit the `setup.cfg` file and :ref:`add a new version table <setup_cfg_versions>` for 0.2 which
  includes a migration. Also create a version table for 0.1 (the previous version) to keep track
  of what that version used to depend on:

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexamplebootstrap/setup.cfg.new
   :start-after:  # List all major.minor versions:


- edit the `setup.cfg` file and increase the version of the 
  :ref:`component <create-component>` to 0.2:

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexamplebootstrap/setup.cfg.new
   :start-after:  [metadata]
   :end-before:   [options]
   :prepend:      [metadata]

.. note::

   Your :ref:`component <create-component>` had version 0.1 at first.
   In order to trigger a migration, you need a new, higher version.
   Database schema changes require new major or minor version; patch versions
   are ignored.
   

To simulate installing the newer version, run:

.. code-block:: bash

   python -m pip install --no-deps -e .

This command regenerates setuptools metadata that is derived from your
`setup.cfg`. Only after running it will the setuptools machinery
pick up the changed version number and the added |Migration|.

Now that a new version of your component has been installed, run the
following in order to migrate the old database:

.. code-block:: bash

   reahl -l INFO migratedb etc


Migration basics
^^^^^^^^^^^^^^^^

Create a |Migration| subclass for each logical change that needs to be made to
the schema (and perhaps data) of the previous version.

In your AddDate |Migration|, override
:meth:`~reahl.component.migration.Migration.schedule_upgrades` with
code that makes the schema changes:

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexamplebootstrap/migrationexamplebootstrap.py
   :pyobject: AddDate

Register each of your |Migration|\s :ref:`in the 'setup.cfg' file <setup_cfg_migrations>`, in :ref:`the version table <setup_cfg_versions>` each migration is for:

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexamplebootstrap/setup.cfg.new
   :start-after: [versions."0.2"]
   :end-before:  [versions."0.1"]


The `migratedb` command checks to see which version of your component
the current database schema corresponds with. It then runs only those
|Migration|\s needed to bring the existing schema up to date with your
new code.


Writing a :meth:`~reahl.component.migration.Migration.schedule_upgrades`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. sidebar:: Pitfalls

  The code of a |Migration| should never call your domain code. The |Migration|
  will stay in your component as you change it over time and make new releases,
  but the code of the actual component itself might diverge with each new version.

Schema changes are written using the `alembic.op` module of
SqlAlchemy's migration tool: `Alembic
<https://pypi.python.org/pypi/alembic>`_

A given application can consist of many components, and each of these
may have its own |Migration|\s. For this reason, you do not actually
call functions of :mod:`alembic.op` in your
:meth:`~reahl.component.migration.Migration.schedule_upgrades`. You
just schedule such calls to be run at the appropriate time using
:meth:`~reahl.component.migration.Migration.schedule`.  Actual
execution of these calls happen only once all components had a chance
to schedule their migration calls.


Execution of these calls happen in a number of predefined
*phases*. You schedule a call to run during a particular phase.

**Phases, in order:**

 drop_fk
   Foreign keys are dropped first, because they refer to other columns.

 drop_pk
   Primary keys are dropped next, they may also prevent other actions from completing.

 pre_alter
   Sometimes some code needs to be executed before tables are altered -- saving some data
   in a temporary table, for example, or disabling some other constraints.

 alter
   Now that all possible constraints have been disabled, tables and columns may be altered.

 create_pk
   Then, primary keys can be created again.

 indexes
   Followed by indexes dependent on those primary keys.

 data
   With a schema mostly fixed, data can be inserted or moved to new locations.

 create_fk
   A last chance to recreate foreign keys to possible newly moved data in the new schema.

 cleanup
   Use this phase if any cleanup is needed of temporary tables, etc.


Dependency management
^^^^^^^^^^^^^^^^^^^^^

Declare a dependency on component B in the `setup.cfg` of component A:

- If component A declares a foreign key to a table that belongs to component B
- If component A imports code from component B

The migration machinery computes a complicated order in which |Migration|\s are scheduled 
and run. This ordering relies on correct dependencies among components.

