.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
What changed in version 2.1
===========================

Based on some feedback from first users, changes were made to simplify
the learning curve of getting to know Reahl.  Backwards-compatibility
remains, just in case...

Renames
-------

Certain classes and methods were renamed:

 - `Region` is now called :class:`~reahl.web.fw.UserInterface`
 - The `.define_main_window()` method was renamed to `.define_page()`
 - `ReahlWebApplication` is now called :class:`~reahl.web.fw.ReahlWSGIApplication`

The `Region` rename also prompted the following methods to be renamed:

 - `.define_region()` to `.define_user_interface()`
 - `.define_regex_region()` to `.define_regex_user_interface()`


Pages directly on Views
-----------------------

One can now directly specify the page to be rendered for a
:class:`~reahl.web.fw.View` upon calling `.define_view()`. This means
that it is not necessary to understand the concept of a
:class:`~reahl.web.ui.Slot` and related complexities when just
building a simple app.

Migrations (since 2.1.2)
------------------------

Migrations have grown up a bit in version 2.1.2 to easy with the
anticipated migration that will be necessary to move from version 2.x
to 3.x.

Migrations now consist of calls that are scheduled for executed during
one of several predefined migration phases, ordered to deal with possibly 
dependencies between database objects. See :ref:`Database schema evolution <database-schema-evolution>` 
for a full explanation.

Table support (since 2.1.2)
---------------------------

Previous versions did not support tables. In this version :class:`reahl.web.ui.Table`
was added for basic table support. Tables can also be generated complete with headers
and data for a given list of data items. See :meth:`reahl.web.ui.Table.from_columns` 
for more information.

:class:`reahl.web.table.DataTable` adds support for displaying tables that are too
big to fit on a single page. Such tables are spread amongst different pages, that the
user can page between. These tables can also be sorted (server-side).

Deprecation warnings (since 2.1.2)
----------------------------------

Deprecation warnings are now shown when running tests. Reahl's own deprecation warnings
used to use the logging system, but are also now using Python's standard warnings module.

