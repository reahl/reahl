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
