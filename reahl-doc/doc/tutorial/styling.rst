.. Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.

Layout and styling
==================

.. sidebar:: Behind the scenes

   Reahl uses the `Pure.css framework <http://purecss.io/>`_ to deal
   with layout issues.

Layout and styling is a thorny issue for programmers. Here is the support
Reahl provides support for dealing with this issue:

Layout
------

A :class:`~reahl.web.fw.Layout` is used to change what a
:class:`~reahl.web.fw.Widget` looks like, how it is styled, or even how
children :class:`~reahl.web.fw.Widget`\ s are added to it -- all for
the purpose of influencing look and layout.
A :class:`~reahl.web.fw.Widget` is configured to use a particular
:class:`~reahl.web.fw.Layout` by calling
:meth:`~reahl.web.fw.Widget.use_layout` on the
:class:`~reahl.web.fw.Widget` after construction. (You can also call
:meth:`~reahl.web.fw.WidgetFactory.use_layout` where you construct only
a :class:`~reahl.web.fw.WidgetFactory` for later use.)
For example, the :class:`~reahl.web.ui.HorizontalLayout` or
:class:`~reahl.web.ui.VerticalLayout` can be used to make a
:class:`~reahl.web.ui.Menu` appear with its items horizontally next to
each other or stacked vertically.

The :mod:`~reahl.web.pure` module includes some layouts based on the
`Pure.css framework <http://purecss.io/>`_. The
:class:`~reahl.web.pure.ColumnLayout` changes a
:class:`~reahl.web.fw.Widget` by adding several
:class:`~reahl.web.ui.Panel`\ s to it that are arranged in columns next
to each other. You can specify the size of these columns, and in such
a way that the size can change, depending on the size of the device
used for viewing. See the documentation for
:class:`~reahl.web.pure.ColumnLayout` and
:class:`~reahl.web.pure.UnitSize` for more details.

:class:`~reahl.web.pure.PageColumnLayout` is meant to be used with an
:class:`~reahl.web.ui.HTML5Page`. It changes the page to have a header
and footer with several columns inbetween.

Here is an example of how these Layouts are used to change a page and
a :class:`~reahl.web.ui.Menu` on that page:

.. literalinclude:: ../../reahl/doc/examples/tutorial/slots/slots.py
   :pyobject: MyCustomPage



Special Widgets
---------------

There are also some :class:`~reahl.web.fw.Widget`\ s with special behaviour that relate to
layout and styling:

:class:`~reahl.web.ui.LabelledBlockInput`
 This :class:`~reahl.web.fw.Widget` wraps around an :class:`~reahl.web.ui.Input`, and adds a Label
 to it. The combination of the :class:`~reahl.web.ui.Input` and its Label are then arranged
 in two columns next to each other. Successive :class:`~reahl.web.ui.LabelledBlockInput`\ s
 appear underneath each other, with all the Labels aligned and all the
 Inputs aligned.

:class:`~reahl.web.ui.LabelledInlineInput`
 A :class:`~reahl.web.ui.LabelledInlineInput` also wraps around an :class:`~reahl.web.ui.Input` and adds a :class:`~reahl.web.ui.Label`. The
 result though is an element that flows with text and can be used as
 part of a paragraph (:class:`~reahl.web.ui.P`\ ), for example.

:class:`~reahl.web.ui.PriorityGroup`
 Sometimes it is useful to visually highlight certain :class:`~reahl.web.fw.Widget`\ s to make
 them stand out amongst their peers. This concept is called the
 "priority" of a :class:`~reahl.web.fw.Widget`. Normally, you would not specify the priority
 of a :class:`~reahl.web.fw.Widget`. But, amongst chosen grouping of :class:`~reahl.web.fw.Widget`\ s, you may set one
 :class:`~reahl.web.fw.Widget` as having "primary" priority, with the others having
 "secondary" priority. 

 A :class:`~reahl.web.fw.Widget` with "secondary" priority will have a CSS class
 `reahl-priority-secondary` attached to it, which is normally styled
 such that it fades a bit into the background (perhaps lighter, or
 slightly greyed out). A :class:`~reahl.web.fw.Widget` with "primary" priority will have CSS
 class `reahl-priority-primary` which is normally styled such that it
 stands out visually.

 The :class:`~reahl.web.ui.PriorityGroup` is an object to which you can add :class:`~reahl.web.fw.Widget`\ s, stating
 their priority (or lack of it). The :class:`~reahl.web.ui.PriorityGroup` will ensure that
 only one of the :class:`~reahl.web.fw.Widget`\ s added to it will ever have primary
 priority. (Many could have no priority set, and many could be
 secondary.)



Styling
-------

Complex :class:`~reahl.web.fw.Widget`\ s in Reahl are written such that the :class:`~reahl.web.fw.Widget` has an
identifiable HTML element that represents the :class:`~reahl.web.fw.Widget`. Identifiable
means that the HTML element has an id or class attribute which can be
used as target of CSS selectors. This allows for CSS to be attached to
each :class:`~reahl.web.fw.Widget` (or its contents). For example, the TabbedPanel is in a
`<div class="reahl-tabbedpanel">`. :class:`~reahl.web.fw.Widget`\ s that map one-to-one to HTML
tags do not have special classes -- they can be targeted in CSS by just
using the HTML tag name they represent: the :class:`reahl.web.ui.P` :class:`~reahl.web.fw.Widget` is just a `<p>`,
for example.

Given these ways to be able to target a :class:`~reahl.web.fw.Widget`
via CSS, you can write normal CSS to provide your own look and feel
for Reahl :class:`~reahl.web.fw.Widget`\ s (if you really want to). In
the reference documentation for each :class:`~reahl.web.fw.Widget` an
explanation is given of what the HTML for that
:class:`~reahl.web.fw.Widget` looks like, for this purpose. (Similar
documentation is provided with :class:`~reahl.web.fw.Layout`\ s.)

In order to use your own CSS on a page, you need to add a link to it on
your :class:`~reahl.web.ui.HTML5Page` subclass. For example in the `__init__`
of your class, you can write:

.. code-block:: python

   self.head.add_css(Url('/link/to/my/own.css'))


The minutae of what :class:`~reahl.web.fw.Widget`\ s look like is probably not the first thing on a
programmer's mind however. It is useful just to start programming using *some*
look for the :class:`~reahl.web.fw.Widget`\ s, and later customise this look to your
liking. For this reason, a stylesheet is provided which includes
styling for all the standard Reahl :class:`~reahl.web.fw.Widget`\ s. You can include this style
by adding it to the Head of your :class:`~reahl.web.ui.HTML5Page`:

.. code-block:: python

   self.head.add_css(Url('/styles/basic.css'))

If you are using the :class:`~reahl.web.ui.HTML5Page` as a page, the same effect
can be accomplished by merely passing ``style='basic'`` to its
constructor (as can be seen in almost all of our code examples so
far).

