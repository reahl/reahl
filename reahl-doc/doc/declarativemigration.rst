.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Elixir to Declarative migration guide
=====================================

This guide is meant for those who opt to change older Elixir-based
model classes to use SqlALchemy Declarative instead. If you go down
this route, you will have to change your code to use Declarative and
you may need some Migrations for your own code. SqlAlchemy and
Declarative have excellent documentation to help users use
Declarative. This guide explains what changed in the database, and how
to migrate to cater for these changes.

Reahl 3.0 also includes a class you can inherit your own Migrations
from which includes a number of handy methods related to the Elixir ->
Declarative migration.

Summary of changes
------------------

 * The new SqlAlchemy provides a mechanism for dictating the naming
   convention used to name database objects (constraints, etc). Using
   this means the same conventions will be used across different
   database backends -- something that will make migrations easier in
   future. Reahl 3.0 now uses these conventions, and they differ from
   names chosen automatically by PostgreSQL in the past. 

   This means that all of the following need to be dropped, and 
   recreated with their new names:
    - primary keys
    - foreign keys

 * All our Elixir classes used joined table inheritance (where they did indeed inherit).
   Perhaps yours do too... In this case, Elixir automatically created a column on the table
   of a child class to refer to the table of the parent class. This column if a primary key
   but is also a foreign key to the parent. It is also used for joins to implement polymorphism.

   Elixir used to include the name of the parent in this column name, ie: party_id. In your
   own code, you can stick to that convention to ease the migration. We opted to clean house
   and rename all these just to 'id'. 

 * In the Elixir implementation, any object decorated with @session_scoped had 
   a column (acting as foreign key) added, named 'session_id'. The name of this column
   was changed to 'user_session_id' for clarity.

   For any @session_scoped classes, this column needs to be renamed, and its associated
   foreign key constraint should be updated.

 * 
