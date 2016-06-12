.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
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


Configuration and DANGEROUS defaults
------------------------------------

Some configuration settings in Reahl are defaulted. This means that you can easily
run a development server without having to create lots of configuration files because
these default settings will be used instead.

Defaults are thus chosen to work in a development environment. Some of these defaults
do not make sense in a production environment. For this reason, when a Reahl server
starts up, it warns about such "Dangerous defaults"--values that are defaulted for
a development environment. The idea is that in a production system, you are expected
to set these explicitly, and *not* rely on the defaulted value.

In Reahl 3.2 when you run a system in production it will fail to start up if any such
dangerous default value is not set explicitly. Previously it would start, but with a 
warning.

Furthermore, some important configuration settings that previously were not defaulted
are now defaulted:

===================== ======================== ===================
 Setting               Config file              Dangerous default
===================== ======================== ===================
 reahlsystem.debug     reahl.config.py          True
 mail.smtp_port        mailutil.config.py       8025
===================== ======================== ===================

If you are running a production system, you will have to explicitly set these after
upgrading before your system will start again.


Elixir
------

The Reahl 3.1 series allowed use of the `reahl-web-elixirimpl` egg which was distributed 
with Reahl 2.x to ease transition from the 2 to 3 series. In Reahl 3.2 this usage of some
older 2.x version eggs is no longer supported.

Changes to existing layout tools
--------------------------------

.. |PageColumnLayout| replace:: :class:`~reahl.web.pure.PageColumnLayout`
.. |pure.ColumnLayout| replace:: :class:`reahl.web.pure.ColumnLayout`
.. |grid.ColumnLayout| replace:: :class:`reahl.web.bootstrap.grid.ColumnLayout`
.. |Layout| replace:: :class:`~reahl.web.fw.Layout`
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
footer). You can optionally also set up a |PageLayout| with a separate
|Layout| for each of it parts (header, document, content,
footer). Detailed layout of each part is thus decoupled from the
|PageLayout| itself and delegated to whatever |Layout| you specify for
that part.

This arrangement makes it possible to use |PageLayout| with either a
|pure.ColumnLayout| or the new |grid.ColumnLayout| in addition to
other possibilities.

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


Dealing with front-end libraries
--------------------------------

Reahl is written in Python, but it has a lot of JavaScript and CSS
code under the covers. Reahl also makes use of other "front-end
libraries" (projects that live in the JavaScript/CSS world).

The :mod:`reahl.web.libraries` module was added for dealing with such
front-end libraries. The same mechanism is now also used internally by
Reahl to ship its own JavaScript and CSS. 

If you develop your own Widgets that include CSS of JavaScript code,
you should now use this mechanism to distribute such front-end
code as your own front-end library.


Miscellaneous 
-------------


Bookmark
~~~~~~~~

.. |Bookmark| replace:: :class:`~reahl.web.fw.Bookmark`

For |Bookmark|, a `locale` argument was added to force the created
|Bookmark| to be in a specific locale, possibly different from the
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
the |HTMLElement| will only be refreshed if the changing `query_field` 
is included in the list sent to |enable_refresh|. Others are ignored.

Label
~~~~~

.. |Label| replace:: :class:`~reahl.web.ui.Label`
.. |Input| replace:: :class:`~reahl.web.ui.Input`

The constructor of |Label| now takes an additional optional keyword
argument: `for_input` to indicate which |Input| it labels.


FieldSet
~~~~~~~~

.. |FieldSet| replace:: :class:`~reahl.web.ui.FieldSet`

A |FieldSet| could be constructed with the keyword argument `label_text`
in which case a :class:`~reahl.web.ui.Label` would be added at the 
start of the |FieldSet|. This is an incorrect usage of |Label|
according to the HTML specification, hence this usage is now deprecated.

Instead, a `legend_text` keyword argument was added. If `legend_text` is
given, a :class:`~reahl.web.ui.Legend` will be added to the |FieldSet|
with the given text.


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

Table
~~~~~

.. |Table| replace:: :class:`~reahl.web.ui.Table`

A |Table| could previously be created pre-populated with a set of
defined columns and a bunch of rows generated from given data by
using :meth:`~reahl.web.ui.Table.from_columns`.

This method has now been deprecated. The same effect can now be 
achieved by calling :meth:`~reahl.web.ui.Table.with_data` on an
already created |Table|\.
   
This was done to allow one to use a |Layout| on the |Table|\, which
would not be possible before. (A |Layout| has to be attached
to its |Table| before data is added to the |Table| so that the 
added rows adhere to the |Layout|.)


Tofu
----

.. |Fixture| replace:: :class:`~reahl.tofu.Fixture`

One of the defining features of a |Fixture| is that it can have
methods for creating new objects for use in the test. All the
arguments of these methods are keyword arguments with default values
so that you can easily create a new object with default setup or
choose to create a instance that only customises values important to
the test.

For example:

.. code:: python

   def new_person(self, name='Jane', surname='Doe):
       return Person(name, surname)

Such a method can be called in different ways:

.. code:: python

   jane = fixture.new_person()
   john = fixture.new_person(name=John)

If you access an attribute on a |Fixture| with the `new_` prefix
chopped off, the corresponding `new_` method is called without
arguments to create and instance to be returned.  This instance is
then stored so that subsequent calls keep returning that same
"singleton" instance:

.. code:: python

   assert fixture.person is fixture.person

In the past, singleton instances created like this were never torn
down. In most cases it is not necessary to tear them down because the
entire |Fixture| is thrown away after a test. We also abort the
database between each of our tests, so that database-persisted
instances are also cleaned up.

Sometimes (albeit rarely) it is useful to be able to tear down some of
these singleton instances explicitly when the |Fixture| itself is
being torn down. In order to do this, you can now have a corresponding
method prefixed with `del_` which will be called at |Fixture| tear
down time:

.. code:: python

   def del_person(self, person): # do stuff to clean up after person

The `del_` methods are called when tearing down the |Fixture| before
any other tear down mechanisms are invoked, and in reverse order of
creation of each singleton instance.




