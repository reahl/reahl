.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |Layout| replace:: :class:`~reahl.web.fw.Layout`
.. |HTML5Page| replace:: :class:`~reahl.web.ui.HTML5Page`
.. |pure.ColumnLayout| replace:: :class:`~reahl.web.pure.ColumnLayout`
.. |PageLayout| replace:: :class:`~reahl.web.layout.PageLayout`
.. |UnitSize| replace:: :class:`~reahl.web.pure.UnitSize`

Layout and styling
==================

.. sidebar:: Behind the scenes

   Reahl uses the `Pure.css framework <http://purecss.io/>`_ to deal
   with layout issues.

Styling is probably not the first thing a programmer wants
to worry about. That is why Reahl comes with some styling you can use
when starting a project -- perhaps to be replaced by a
graphic designer later.

Let us detour to introduce layout and styling ideas because that will
allow us to to make the rest of the examples in the tutorial look just
a little bit better.



Layout
------

A |Layout| is used to change what a |Widget| looks like, what css
classes are attached to it for styling, or even how children |Widget|\
s are added to it -- all for the purpose of influencing look and
layout.

A |Widget| is configured to use a particular |Layout| by calling
:meth:`reahl.web.fw.Widget.use_layout` on the |Widget| after
construction. (You can also call
:meth:`reahl.web.fw.WidgetFactory.use_layout` where you construct only
a :class:`~reahl.web.fw.WidgetFactory` for later use.)  For example,
the :class:`~reahl.web.ui.HorizontalLayout` or
:class:`~reahl.web.ui.VerticalLayout` can be used to make a
:class:`~reahl.web.ui.Menu` appear with its items horizontally next to
each other or stacked vertically.

Some layout concepts are implemented in terms of some frontend
library, others are generally applicable.

The :mod:`~reahl.web.pure` module includes some layouts based on the
`Pure.css framework <http://purecss.io/>`_. The |pure.ColumnLayout|
changes a |Widget| by adding several :class:`~reahl.web.ui.Div`\ s to
it that are arranged as columns next to each other. You can specify
the size of these columns, and in such a way that the size can change,
depending on the size of the device used for viewing. See the
documentation for |pure.ColumnLayout| and |UnitSize| for more details.
(See :doc:`../web/bootstrap` for Layouts and Widgets built using the
Bootstrap library.)

The :mod:`~reahl.web.layout` module houses generically applicable concepts.
|PageLayout| is meant to be used with an
HTML5Page. It changes the page to have a header
and footer with a content area inbetween. If a |pure.ColumnLayout|
(for example) is passed to the |PageLayout| constuctor, 
it will automatically be used as the layout of the content area of the page.


Here is an example of how |PageLayout| and
|pure.ColumnLayout| can be used in conjunction to
create a page with some structure. In the example,
:class:`~reahl.web.ui.HorizontalLayout` is also used to specify how
the :class:`~reahl.web.ui.Menu` is presented.

.. literalinclude:: ../../reahl/doc/examples/tutorial/slots/slots.py
   :pyobject: MyCustomPage



Special Widgets
---------------

There are also some |Widget|\ s with special behaviour that relate to
layout and styling:

:class:`~reahl.web.ui.LabelledBlockInput`
 This |Widget| wraps around an :class:`~reahl.web.ui.Input`, and adds a :class:`~reahl.web.ui.Label`
 to it. The combination of the :class:`~reahl.web.ui.Input` and its :class:`~reahl.web.ui.Label` are then arranged
 in two columns next to each other. Successive :class:`~reahl.web.ui.LabelledBlockInput`\ s
 appear underneath each other, with all the :class:`~reahl.web.ui.Label`\s aligned and all the
 Inputs aligned.

:class:`~reahl.web.ui.LabelledInlineInput`
 A :class:`~reahl.web.ui.LabelledInlineInput` also wraps around an :class:`~reahl.web.ui.Input` and adds a :class:`~reahl.web.ui.Label`. The
 result though is an element that flows with text and can be used as
 part of a paragraph (:class:`~reahl.web.ui.P`\ ), for example.

:class:`~reahl.web.ui.PriorityGroup`
 Sometimes it is useful to visually highlight certain |Widget|\ s to make
 them stand out amongst their peers. This concept is called the
 "priority" of a |Widget|. Normally, you would not specify the priority
 of a |Widget|. But, amongst chosen grouping of |Widget|\ s, you may set one
 |Widget| as having "primary" priority, with the others having
 "secondary" priority. 

 A |Widget| with "secondary" priority will have a CSS class
 `reahl-priority-secondary` attached to it, which is normally styled
 such that it fades a bit into the background (perhaps lighter, or
 slightly greyed out). A |Widget| with "primary" priority will have CSS
 class `reahl-priority-primary` which is normally styled such that it
 stands out visually.

 The :class:`~reahl.web.ui.PriorityGroup` is an object to which you can add |Widget|\ s, stating
 their priority (or lack of it). The :class:`~reahl.web.ui.PriorityGroup` will ensure that
 only one of the |Widget|\ s added to it will ever have primary
 priority. (Many could have no priority set, and many could be
 secondary.)



Styling
-------

Complex |Widget|\ s in Reahl are written such that the |Widget| has an
identifiable HTML element that represents the |Widget|. Identifiable
means that the HTML element has an id or class attribute which can be
used as target of CSS selectors. This allows for CSS to be attached to
each |Widget| (or its contents). For example, the TabbedPanel is in a
`<div class="reahl-tabbedpanel">`. |Widget|\ s that map one-to-one to HTML
tags do not have special classes -- they can be targeted in CSS by just
using the HTML tag name they represent: the :class:`reahl.web.ui.P` |Widget| is just a `<p>`,
for example.

Any |Layout| can add additional CSS classes to a
|Widget| or change how content is added to it.

Given these ways to be able to target a |Widget|
(possibly modified by a apecific |Layout|) via
CSS, you can write normal CSS to provide your own look and feel for
Reahl |Widget|\ s (if you really want to). In the
reference documentation for each |Widget| an
explanation is given of what the HTML for that
|Widget| looks like, for this purpose. (Similar
documentation is provided with |Layout|\ s.)

In order to use your own CSS on a page, you need to add a link to it on
your HTML5Page subclass. For example in the `__init__`
of your class, you can write:

.. code-block:: python

   self.head.add_css(Url('/link/to/my/own.css'))


The minutae of what |Widget|\ s look like is probably not the first thing on a
programmer's mind however. It is useful just to start programming using *some*
look for the |Widget|\ s, and later customise this look to your
liking. For this reason, a stylesheet is provided which includes
styling for all the standard Reahl |Widget|\ s. You can include this style
by adding it to the Head of your HTML5Page:

.. code-block:: python

   self.head.add_css(Url('/styles/basic.css'))

If you are using the HTML5Page as a page, the same effect
can be accomplished by merely passing ``style='basic'`` to its
constructor (as can be seen in almost all of our code examples so
far).

