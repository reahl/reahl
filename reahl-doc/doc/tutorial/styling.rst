.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.

Styling your application
========================

.. sidebar:: Behind the scenes

   Reahl uses the `YUI 2 Grids CSS framework
   <http://developer.yahoo.com/yui/grids/>`_ to deal with layout
   issues.

Styling and layout is a thorny issue for programmers. Reahl provides
some support for dealing with this issue -- but we can probably do a
whole lot more. Here is what we've got currently.

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

Given these ways to be able to target a :class:`~reahl.web.fw.Widget` via CSS, you can write
normal CSS to provide your own look and feel for Reahl :class:`~reahl.web.fw.Widget`\ s (if you
really want to). In the reference documentation for each :class:`~reahl.web.fw.Widget`, an explanation is
given of what the HTML for that :class:`~reahl.web.fw.Widget` looks like, for this purpose.

However, what :class:`~reahl.web.fw.Widget`\ s look like is probably not the first thing on a
programmer's mind. It is useful just to start programming using *some*
look for the :class:`~reahl.web.fw.Widget`\ s, and later customise this look to your
liking. For this reason, a stylesheet is provided which includes
styling for all the standard Reahl :class:`~reahl.web.fw.Widget`\ s. You can include this style
by adding it to the Head of your :class:`~reahl.web.ui.HTML5Page`:

.. code-block:: python

   self.head.add_css(Url('/styles/basic.css'))

If you are using the :class:`~reahl.web.ui.TwoColumnPage` as a page, the same effect
can be accomplished by merely passing ``style='basic'`` to its
constructor (as can be seen in almost all of our code examples so
far).

Layout
------

Positioning of elements on a page can be quite tricky, given how the
implementors of different browsers bend the specifications to their
will. To deal with this issue in a browser-agnostic way, Reahl uses
the `YUI 2 Grids CSS framework
<http://developer.yahoo.com/yui/grids/>`_.

An :class:`~reahl.web.ui.HTML5Page` is a very basic :class:`~reahl.web.fw.Widget` that represents an HTML page which
looks empty, but does include links to the necessary JavaScript and
CSS files that the framework depends on. One of the things included in
such an empty-looking :class:`~reahl.web.ui.HTML5Page` is the `YUI 2 Grids CSS framework
<http://developer.yahoo.com/yui/grids/>`_. All :class:`~reahl.web.fw.Widget`\ s used as a main
window in an application should be instances of :class:`~reahl.web.ui.HTML5Page` or one of
its subclasses.

The YUI 2 Grids CSS framework does the following things:

- It resets all fonts to look the same on all browsers
- It resets all margins, padding, of elements etc to 0 (to ensure
  these settings are the same on all browsers)
- It includes CSS that makes positioning things in a layout grid
  using YuiGrid and YuiUnit container :class:`~reahl.web.fw.Widget`\ s.

To develop your own page, you need to understand how YUI 2
Grids CSS works. Then use basic Reahl :class:`~reahl.web.fw.Widget`\ s to build your
own :class:`~reahl.web.ui.HTML5Page`\ -derived page that will provide the structure
you need. The :class:`~reahl.web.ui.TwoColumnPage` :class:`~reahl.web.fw.Widget` is an example of how one can do
this.

A :class:`~reahl.web.ui.TwoColumnPage` is a basic page which contains a header area, footer
area and two columns: a smaller one to the left and a larger one to
the right of the page. The header area spans the top of the two
columns, and the footer spans the area below the two columns. All the
user of a :class:`~reahl.web.ui.TwoColumnPage` needs to know is what :class:`~reahl.web.ui.Slot`\ s the :class:`~reahl.web.ui.TwoColumnPage`
provides, or what elements it has to which you could add more
children.

The :class:`~reahl.web.ui.TwoColumnPage` also can be created with a keyword argument 'style'
which, if used, indicates which predefined style to use for standard
Reahl :class:`~reahl.web.fw.Widget`\ s.

As an example of how you could build your own, here is the
implementation of :class:`~reahl.web.ui.TwoColumnPage`, that shows how Yui elements are used
to construct a page layout:

.. literalinclude:: ../../../reahl-web/reahl/web/ui.py
   :pyobject: TwoColumnPage


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
 part of a paragraph (:class:`reahl.web.ui.P`\ ), for example.

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

