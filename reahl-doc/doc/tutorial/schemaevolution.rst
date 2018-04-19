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
   data very well, and as a result migration is only possible on
   PostgreSQL databases. See these posts for more information on
   the issue: `one of the last bullets of goals of alembic
   <https://bitbucket.org/zzzeek/alembic>`_ and `Christopher Webber's
   rant about the issue <https://dustycloud.org/blog/sqlite-alter-pain/>`_.


Once your application is running in production you may want to
develop a new version. If code changes in the new version require
changes to the database schema, you need to migrate the current
database to preserve its data.


A migration example
^^^^^^^^^^^^^^^^^^^

In order to simulate a program that changes over time, the
`tutorial.migrationexamplebootstrap` example contains an extra
`added_date` column in Address. This code is commented out to make it
possible to run the application with a database schema that does not
include `added_date` at first. A new schema will be needed when the
actual `added_date` is uncommented.

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexamplebootstrap/migrationexamplebootstrap.py
   :pyobject: Address

To try it out, do:

.. code-block:: bash

   reahl example tutorial.migrationexamplebootstrap
   cd migrationexamplebootstrap
   reahl setup -- develop -N
   reahl createdbtables etc
   reahl demosetup

Doing all of this simulates an application that ran somewhere for a
while, with some data in its database.

Now change the application:

- comment out the 'TODO' version of `added_date`, and uncomment the
  version with the Column
- edit the `.reahlproject` file and increase the version of the
  component to 0.1

To simulate installing the newer version, run:

.. code-block:: bash

   reahl setup -- develop -N

After installing a new version of your component, run the
following in order to migrate the old database:

.. code-block:: bash

   reahl migratedb etc


Migration basics
^^^^^^^^^^^^^^^^

Create a |Migration| subclass for each change that needs to be made to
the schema (and perhaps data) of the previous version.

In your AddDate |Migration|, override
:meth:`~reahl.component.migration.Migration.schedule_upgrades` with
code that makes the schema changes.  AddDate needs a class attribute
:attr:`~reahl.component.migration.Migration.version` which states
which version of your component it is for:

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexamplebootstrap/migrationexamplebootstrap.py
   :pyobject: AddDate

Register all your |Migration|\s in the `.reahlproject` file:

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexamplebootstrap/.reahlproject
   :start-after:   <migrations>
   :end-before:   </migrations>
   :prepend:   <migrations>
   :append:   </migrations>

The `migratedb` command checks to see which version of your component
the current database schema corresponds with. It then runs only those
|Migration|\s needed to bring the existing schema up to date with your
new code.


Writing a :meth:`~reahl.component.migration.Migration.schedule_upgrades`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. sidebar:: Pitfalls

  |Migration|\s should not use the code in your component, because all
  the |Migration|\s you write will stay in your component forever, as
  is, even if the code of the actual component itself changes over
  time.

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



