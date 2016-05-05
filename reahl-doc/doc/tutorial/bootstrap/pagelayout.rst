.. Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.


Layout of pages
===============

.. sidebar:: Examples in this section

   - tutorial.bootstrapgrids

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


The :mod:`reahl.web.bootstrap.grid` module provides tools with which
you can control the basic layout of a page. Layout is responsive,
meaning that it adapts depending on the size of the device used to
view the page.

Grid basics
-----------

The basic tools for laying out a page are
:class:`reahl.web.bootstrap.grid.Container`,
:class:`reahl.web.bootstrap.grid.ColumnLayout` and
:class:`reahl.web.bootstrap.grid.ResponsiveSize`.

A :class:`reahl.web.bootstrap.grid.Container` sets up a
:class:`~reahl.web.ui.HTMLElement` for pleasing display should it hold
contents. (It gets padding, for example.)

A :class:`~reahl.web.bootstrap.grid.ColumnLayout` is used to turn an
:class:`~reahl.web.ui.HTMLElement` such as a
:class:`~reahl.web.bootstrap.ui.Div` into one row of a grid with a
number of columns inside that one row. 

Bootstrap requires that all Widgets laid out with a
:class:`~reahl.web.bootstrap.grid.ColumnLayout` be nested somewhere
(no matter how deeply) in another which is laid out by a
:class:`reahl.web.bootstrap.grid.Container`.

When adding a column, you need to specify the size of that
column. This is done using a
:class:`~reahl.web.bootstrap.grid.ResponsiveSize`. A
:class:`~reahl.web.bootstrap.grid.ResponsiveSize` lets you specify how
wide the column should be on each possible size of user device. User
device sizes (called device classes) can be one of:

 - xs (extra small)
 - sm (small)
 - md (medium)
 - lg (large)
 - xl (extra large)


In the code below, 12 columns of 1/12th the page width
are added to a :class:`~reahl.web.bootstrap.ui.Div`. Each column is a 
:class:`~reahl.web.bootstrap.ui.Div` itself and all have the same
text in them:

.. literalinclude:: ../../../reahl/doc/examples/tutorial/bootstrapgrids/bootstrapgrids.py
   :pyobject: GridBasicsPage.add_twelve

A :class:`~reahl.web.bootstrap.grid.ColumnLayout` can also be constructed with a list of tuples stating what columns it should have and what each one should be called. In this case, it will add all the specified columns (each a
:class:`~reahl.web.bootstrap.ui.Div` itself) to the :class:`~reahl.web.bootstrap.ui.Div` you apply it to and make these available as a dictionary. An example is shown here:


.. literalinclude:: ../../../reahl/doc/examples/tutorial/bootstrapgrids/bootstrapgrids.py
   :pyobject: GridBasicsPage.add_two

In order to really appreciate the power of
:class:`~reahl.web.bootstrap.grid.ResponsiveSize`, you will 
have to fire up the example and play around with it. The example here
includes different Views -- this View is the first called "Grid basics".

TODO: we need at least on screenshot here - of the large window.

See how the layout changes if you change the size of the window. On
displays that are medium sized or larger (with your browser
maximised), you will see two rows: one with 12 equal sized columns,
and another with two columns that are not equally sized.

As soon as you make the browser window smaller than "md" size, things
change, however: All the columns now stack on top of one another and
fill the whole width of the screen to make them more usable on the
smaller sized screen.

With :class:`~reahl.web.bootstrap.grid.ResponsiveSize`, you can set
up different breakpoints where the layout should adapt and specify
specific widths depending on device class.


Laying out a whole page
-----------------------

It is often useful to layout an entire page with a header area at the
top, a footer at the bottom, and a content area inbetween. The content
area is also often divided into different columns.

You can layout a page in this fasion by using
:class:`reahl.web.bootstrap.grid.PageLayout` in conjunction with a suitable
:class:`reahl.web.bootstrap.grid.ColumnLayout` to be used for its
content area.

The "Page layout" view in our example shows how this works:

.. literalinclude:: ../../../reahl/doc/examples/tutorial/bootstrapgrids/bootstrapgrids.py
   :pyobject: PageLayoutPage


Notice how the same responsive properties hold for such pages too -- go ahead and make your browser window smaller on this example.

You can nest the usage of a
:class:`reahl.web.bootstrap.grid.ColumnLayout` inside others (like
the columns on this page), thereby creating complex grid structures
that resize on all levels.


