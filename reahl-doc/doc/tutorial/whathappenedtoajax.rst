.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
What ever happened to Ajax?
===========================

.. sidebar:: Examples in this section

   - tutorial.ajax
   - tutorial.pager

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

Ajax is a prominent word in the web development world. You may be
wondering why it has not been mentioned in this tutorial yet.
The thing is, `Ajax is a low level implementation technique
<https://en.wikipedia.org/wiki/Ajax_(programming)>`_, and the whole
vision of Reahl is to try and hide such low level implementation
details. The framework should deal with it for you: Ajax is in there,
with many other techniques, you just do not have to know about it.

Sometimes though, one needs to build your own :class:`~reahl.web.fw.Widget`\ s with some
behaviour that smacks of Ajax. For example, you'd want a part of the
page to change without refreshing the entire page. Is this high-level
framework flexible enough to let you do that?

To say yes does not do the gravity of that question justice. How Reahl
allows a programmer to do this, and the ways in which other classes in
the Reahl framework use such capabilities say a lot about the values
underlying Reahl. Hence, the two examples in this section.

Refreshing Widgets
------------------

It is possible for a programmer to build a :class:`~reahl.web.fw.Widget` which gets refreshed
without reloading the entire page. To show how this works, we have
concocted an example. The example consists of a single page with a
:class:`~reahl.web.ui.Panel` that contains a paragraph with some text. The page contains a
:class:`~reahl.web.ui.Menu` too. When the user clicks on a :class:`~reahl.web.ui.MenuItem`, the contents of the
:class:`~reahl.web.ui.Panel` changes to indicate what was clicked on in the :class:`~reahl.web.ui.Menu`. This
happens without reloading the page.

The test illustrates this idea:

.. literalinclude:: ../../reahl/doc/examples/tutorial/ajax/ajax_dev/ajaxtests.py
   :pyobject: refreshing_widget
   :prepend: @test(RefreshFixture)

Forget about Ajax, though, and learn these concepts: Like  :class:`~reahl.web.fw.View`\ s ,
:class:`~reahl.web.fw.Widget`\ s can have arguments too. A :class:`~reahl.web.fw.Widget` can be
set to be re-rendered when the value of one or more of its arguments on a given page change. 
(Behind the scenes, this happens via Ajax.)

The beauty of this mechanism in Reahl is that it will all still work
for users even when their JavaScript is turned off -- just not via
Ajax. This is really good, because it makes the parts of the
application that work like this crawlable by search engines, and
bookmarkable by browser users.

Just like you can get a :class:`~reahl.web.fw.Bookmark` to a :class:`~reahl.web.fw.View` with specific arguments,
you can also get a :class:`~reahl.web.fw.Bookmark` to a :class:`~reahl.web.fw.Widget` with specific arguments. If a
user clicks on a :class:`~reahl.web.ui.MenuItem` for such an *in-page* :class:`~reahl.web.fw.Bookmark`, the user
stays on the same :class:`~reahl.web.fw.View`, the only thing that changes is the value of
the arguments to the applicable :class:`~reahl.web.fw.Widget`. This is what triggers the
:class:`~reahl.web.fw.Widget` to be re-rendered.

The arguments of a :class:`~reahl.web.fw.Widget` are called query arguments. To declare query
arguments on the :class:`~reahl.web.fw.Widget` you add a method called `query_arguments` to
the :class:`~reahl.web.fw.Widget` class, and decorate it with `@expose`. Inside the
`query_arguments` method, each argument of the :class:`~reahl.web.fw.Widget` is defined using
a :class:`~reahl.component.modelinterface.Field`. In fact, the arguments of a :class:`~reahl.web.fw.Widget` work exactly like the
:class:`~reahl.component.modelinterface.Field`\ s on a model object. Think of the :class:`~reahl.web.fw.Widget` as being the model
object, and its `.fields` as being called its `.query_arguments`. When
the :class:`~reahl.web.fw.Widget` is constructed, an attribute will be set for each query
argument on the :class:`~reahl.web.fw.Widget` instance:

.. literalinclude:: ../../reahl/doc/examples/tutorial/ajax/ajax.py

.. note::

   If a :class:`~reahl.web.fw.Widget` has `query_arguments`, it is required to have a unique
   css_id.  (The framework raises a :class:`~reahl.component.exceptions.ProgrammerError` if this rule is
   violated.)

Paging long lists
-----------------

Frequently in web applications there is a need to present a long list
of items that do not fit onto a single web page. The Reahl way of
dealing with such a requirement is to provide a bunch of classes that
solve the problem together, on a conceptual level. Think of it almost
as a design pattern of sorts:

 .. figure:: pager.png
    :align: center
    :width: 70%

To deal with long lists, the long list is seen as being broken up into
different "pages", each page containing a smaller, manageable list of
items. Breaking a list up into such pages is the responsibility of the
:class:`~reahl.web.pager.PageIndex`. A :class:`~reahl.web.pager.PageMenu` is a :class:`~reahl.web.fw.Widget` which allows the user to choose
which of these pages should be viewed. The :class:`~reahl.web.pager.PagedPanel` presents the
items on the currently selected page to the user. There are two kinds
of :class:`~reahl.web.pager.PageIndex` that a programmer can choose from: :class:`~reahl.web.pager.AnnualPageIndex`
assumes that a date is associated with each item, and puts all items
sharing the same year on a page, ordering pages by
year. :class:`~reahl.web.pager.SequentialPageIndex` just breaks a list of items up into a fixed
number of items per page.

In the example below, a long list of Addresses is divided into pages
using a :class:`~reahl.web.pager.SequentialPageIndex`. For simplicity, the Addresses are not
stored in the database in this example -- `Address.all_addresses()`
simply creates the Addresses instead of finding them from the
database.

AddressList is the :class:`~reahl.web.pager.PagedPanel` in this example. This is the piece the
programmer needs to supply. Note that AddressList inherits a property
`.current_contents` which is a list of all the items on the current
page. In the implementation of `AddressBookPanel.__init__` you will
also see that the :class:`~reahl.web.pager.SequentialPageIndex` is created first, and sent to
both of the other two :class:`~reahl.web.fw.Widget`\ s. It is created with the long list of
Addresses, and told how many items to put per page.

Both the :class:`~reahl.web.pager.PageMenu` and the :class:`~reahl.web.pager.PagedPanel` also need to have unique IDs
specified, as strings. The ID of :class:`~reahl.web.pager.PageMenu` is passed into its
constructor, and AddressList passes its ID to the `super` call in
`AddressList.__init__`. Reahl sometimes need :class:`~reahl.web.fw.Widget`\ s to have such
unique IDs for the underlying implementation to work. :class:`~reahl.web.ui.Form`\ s also need
a unique ID upon construction, for example.


.. literalinclude:: ../../reahl/doc/examples/tutorial/pager/pager.py
