.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Elixir to Declarative database schema migration guide
=====================================================

This guide is meant for those who opt to change older Elixir-based
model classes that they wrote themselves to use SqlALchemy Declarative
instead. If you go down this route, and you need to upgrade a
database, then you may need some Migrations for your own
code. 

This guide explains what changed in the database, and how to migrate
to cater for these changes. 


Summary of changes
------------------

 * Any object decorated with @session_scoped has a column (used as a
   foreign key to the session). In the Elixir implementation, this
   column was named 'session_id'. The name of this column was changed
   to 'user_session_id' for clarity: the word 'session' is used for
   SqlAlchemy's Session as well as for Reahl UserSession. This name
   makes explicit which 'session' it refers to.

   For any @session_scoped classes, this column needs to be renamed,
   and its associated foreign key constraint should be updated.

 * The new (0.9) SqlAlchemy provides a mechanism for dictating the
   naming convention used to name database objects (constraints, indexes,
   etc). Using this means the same conventions will be used across
   different database backends -- something that will make migrations
   easier in future. Reahl 3.0 now uses these conventions, and they
   differ from names chosen automatically by PostgreSQL in the past.

   This means that all of the following need to be dropped, and 
   recreated with their new names:
    - primary keys
    - foreign keys
    - indexes

 * All our Elixir classes used joined table inheritance (where they did indeed inherit).
   Perhaps yours do too... In this case, Elixir automatically created a column on the table
   of a child class to refer to the table of the parent class. This column is a primary key
   but is also a foreign key to the parent. The column is used for joins to implement polymorphism.

   Elixir used to include the name of the parent in this column name, ie: party_id. In your
   own code, you can stick to that convention to ease the migration. We opted to clean house
   and rename all these just to 'id'. 

 * As mentioned, previously, a Party always had a SystemAccount. It
   makes more sense to be able to have Party objects with or without
   SystemAccounts, hence the relationship was changed. Going forward, a Party
   does not have any knowledge of a SystemAccount, but a SystemAccount
   has an 'owner', which is a Party.



The MigrateElixirToDeclarative class
------------------------------------

Reahl 3.0 includes the class
:class:`reahl.sqlalchemysupport.elixirmigration.MigrateElixirToDeclarative`. You
can inherit from this class to create your own Migrations relating to
this move from Elixir to Declarative. It includes a number of handy methods
you can call:


MigrateElixirToDeclarative
""""""""""""""""""""""""""

.. autoclass:: reahl.sqlalchemysupport.elixirmigration.MigrateElixirToDeclarative
   :members:
