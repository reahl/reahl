.. Copyright 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
What changed in version 3.2
===========================

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`


Bootstrap
---------

This release extends Reahl with (experimental) `Bootstrap <http://getbootstrap.com>`_ support.

Going forward (Reahl 4.0 onwards) we will base all our Widgets and
styling on `the Bootstrap web frontend library
<http://getbootstrap.com>`_ with the aim of sporting a better look and
better layout tools.

This release is a transitional release: it has Bootstrap based Widgets 
and Layouts added side-by-side to what already exists. However, since 
Bootstrap 4 was still in alpha at the time of this release, this support
is labelled as experimental and it is not enabled by default.

The addition of Bootstrap-based |Widget|\s is the major change
prompting this release. How it works, how its different and how you can
enable it are all :doc:`discussed in the tutorial
<tutorial/bootstrap/index>` and won't be repeated here.


Changes to existing layout tools
--------------------------------

.. |PageColumnLayout| replace:: :class:`~reahl.web.pure.PageColumnLayout`
.. |pure.ColumnLayout| replace:: :class:`reahl.web.pure.ColumnLayout`
.. |grid.ColumnLayout| replace:: :class:`reahl.web.bootstrap.grid.ColumnLayout`
.. |Layout| replace:: :class:`~reahl.web.ui.Layout`
.. |PageLayout| replace:: :class:`~reahl.web.layout.PageLayout`

In the process of having to support Bootstrap, our existing concept of
|PageColumnLayout| has grown too. 

|PageColumnLayout| has too much responsibility. It structures a page
with header, footer etc but it also structures the content area of the
page into columns. In order to do this, |PageColumnLayout|
hard-codes the use of a |pure.ColumnLayout| and we wanted to be able
to use it with a |grid.ColumnLayout| too.

The new :class:`reahl.web.layout.PageLayout` solves this problem by
only taking responsibility for the page itself (header, content,
footer), while delegating the detailed layout of the content area to
any |Layout| you specify. This arrangement makes it possible to use
|PageLayout| with either a |pure.ColumnLayout| or the new
|grid.ColumnLayout| in addition to other possibilities.

Updated dependencies
--------------------

Some thirdparty JavaScript libraries were updated:

  - jQuery from 1.8.1 to 1.11.2 (with jquery-migrate 1.2.1 added)
  - jquery-blockui to 2.70.0

The versions of some external dependencies were updated:

  - Babel from 1.3 to 2.1
  - docutils max version 1.12 to < 1.13
  - selenium max version from < 2.43 to < 3


Development web server
----------------------

The development web server (invoked with ``reahl serve``) now has the
ability to watch for file changes in multiple directories, and restart
itself when a change is detected. 

See:

.. code:: bash

   reahl serve -h


Holder
------

The :mod:`reahl.web.holder.holder` module was added to be able to use
`holder.js <http://imsky.github.io/holder/>`_ to generate images on
the fly in a client browser.


Miscellaneous 
-------------


Bookmark
~~~~~~~~

   .. |Bookmark| replace:: :class:`~reahl.web.fw.Bookmark`

   For |Bookmark|, a `locale` argument was added to force the created
   |Bookmark| to be in a specific locale, possibly different fro mthe
   current one.

Widget
~~~~~~

   .. |HTMLElement| replace:: :class:`~reahl.web.ui.HTMLElement`

   Many |Widget|\s inconsistently could receive a `css_id` kwarg upon
   construction. This is now deprecated. Instead only simple |Widget|\s
   that are subclasses from |HTMLElement| now support this interface.

HTMLElement
~~~~~~~~~~~

   .. |enable_refresh| replace:: :meth:`~reahl.web.ui.HTMLElement.enable_refresh`
   .. |query_fields| replace:: :meth:`~reahl.web.fw.Widget.query_fields`

   Previously, an |HTMLElement| could be set up so that it is refreshed
   via ajax if any of its |query_fields| changed. This was done by
   calling |enable_refresh|. These ideas were refined a little:
   |enable_refresh| can now be given a list of the |query_fields| so that
   the |HTMLElement| will only be refreshed if one of the |query_fields|
   in that list changes. Others are ignored.

Label
~~~~~

   .. |Label| replace:: :class:`~reahl.web.ui.Label`
   .. |Input| replace:: :class:`~reahl.web.ui.Input`

   The constructor of |Label| now takes an additional optional keyword
   argument: `for_input` to indicate which |Input| it labels.


Menu
~~~~

   .. |Menu| replace:: :class:`~reahl.web.ui.Menu`

   The way one creates a |Menu| has been changed. Instead of creating
   a |Menu| from certain sources, it should now be created empty and
   then populated using a set of new methods.

   For example, a |Menu| could previously be created to contain items
   for a given list of |Bookmark|\s by using the class method
   :meth:`~reahl.web.ui.Menu.from_bookmarks`\. A |Menu| could also be
   created for all supported locales with
   :meth:`~reahl.web.ui.Menu.from_languages`.

   These methods have been deprecated in favour of a new interface
   by which you first create an empty |Menu| and then populate it using
   one of:

    - :meth:`~reahl.web.ui.Menu.with_bookmarks`
    - :meth:`~reahl.web.ui.Menu.with_a_list`
    - :meth:`~reahl.web.ui.Menu.with_languages`

   Several methods also let you add items individually from similar 
   sources:

    - :meth:`~reahl.web.ui.Menu.add_bookmark`
    - :meth:`~reahl.web.ui.Menu.add_a`
    - :meth:`~reahl.web.ui.Menu.add_submenu`



