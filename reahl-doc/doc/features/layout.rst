.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Layout example
==============

.. sidebar:: Behind the scenes
   
   Reahl Widgets and Layouts are based on
   `the Bootstrap frontend framework <http://getbootstrap.com>`_.

A Widget can use a predefined (but configurable) Layout to change what
it looks like. Different Layouts could be used with the same Widget on
different apps or different contexts.

Some special widgets are also provided to help position elements on a
page. The example presented here shows some layout examples.

We provide some styling for a basic look which you can use while
programming while web designers can create your perfect look in
parallel for each applicable Widget.

The source code given below results in the following visual layout:

   .. figure:: ../_build/screenshots/layout.png
      :align: center
      :width: 100%
      :alt: Screenshot of a page with header, footer, two columns and a few other layout features demonstrated.

In this example, the page used is not specified per View, but a single
`page` is used for the entire UserInterface. Each View (there's only
one here) just specifies some contents for the named Slots provided by
that page. (See :doc:`../tutorial/slots` for an explanation.)

PageLayout is used in this example to change the HTMLPage of the
application to have a header and footer with a content area inbetween
the two, that is itself split into columns using ColumnLayout. A
Slot is inserted in the header, footer and each column.

The `row` variable is a Panel split into columns using another ColumnLayout.

Widgets like the LabelledBlockInput can be used to do the internal
layout of elements of a form. A LabelledBlockInput wraps around any
simple input and provides it with a label. It also positions all the
relevant constituent elements neatly --- including possible validation
error messages.

.. literalinclude:: ../../reahl/doc/examples/features/layout/layout.py
