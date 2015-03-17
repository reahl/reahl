.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Layout example
==============

.. sidebar:: Behind the scenes

   Reahl implements layout-related functionality in terms of the
   `Pure.css framework <http://purecss.io/>`_.

A Widget can use a predefined (but configurable) Layout to change what it looks like.
Some special widgets are also provided to help position elements on a
page. The example presented here shows some layout examples.

The source code given below results in the following visual layout:

   .. figure:: ../_build/screenshots/layout.png
      :align: center
      :width: 100%
      :alt: Screenshot of a page with header, footer, two columns and a few other layout features demonstrated.

The first thing to notice in the code given below is that the page
used is not specified per View, but a single `page` is used for the
entire UserInterface. Each View (there's only one here) just specifies
some contents for the named Slots provided by that page. (See
:doc:`../tutorial/slots` for an explanation.)

The code includes two example Layouts: The HTMLPage used as the main page 
of the application has a header and footer with a content area inbetween the
two, that is itself split into columns. All of this is the work of the
PageColumnLayout, which is set up to have two columns with sizes relative
to their container. Each column created by the PageColumnLayout contains
a Slot with the same name as the column.

Below the form inputs is an example of a Panel that is split into columns
using ColumnLayout. This is a simpler Layout which also makes the columns
it adds to its Widget available via its .columns dictionary for further use.

Widgets like the LabelledBlockInput can be used to do the internal
layout of elements of a form. A LabelledBlockInput wraps around any
simple input and provides it with a label. It also positions all the
relevant constituent elements neatly --- including possible validation
error messages.

.. literalinclude:: ../../reahl/doc/examples/features/layout/layout.py
