.. Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |ColumnLayout| replace:: :class:`~reahl.web.bootstrap.grid.ColumnLayout`
.. |Div| replace:: :class:`~reahl.web.bootstrap.ui.Div`
.. |HTMLElement| replace:: :class:`~reahl.web.ui.HTMLElement`
.. |HTML5Page| replace:: :class:`~reahl.web.bootstrap.ui.HTML5Page`
.. |ResponsiveSize| replace:: :class:`~reahl.web.bootstrap.grid.ResponsiveSize`
.. |Container| replace:: :class:`~reahl.web.bootstrap.grid.Container`
.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |PageLayout| replace:: :class:`~reahl.web.bootstrap.grid.PageLayout`

Layout of pages
===============

.. sidebar:: Examples in this section

   - tutorial.bootstrapgrids

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Containers
----------

A |Container| manages how the contents of an |HTMLElement| fills its
width. The contents can be confined to a fixed width (with margins),
or the contents can be fluid and expand to fill the whole width.

.. figure:: container-fixed.png
  :align: center
  :alt: A site with fixed container showing how the contents are centered on the viewport.

.. figure:: container-fluid.png
  :align: center
  :alt: A site with fluid container showing how the contents stretch to fill the viewport.

Different areas of a site may be laid out using different
|Container|\s. For example, you might want your pages to have a
header and footer that both stretch the entire viewport width, but
with a content area inbetween that has a fixed width and is centered.

Bootstrap requires that all Widgets laid out with a |ColumnLayout| be
nested somewhere (no matter how deeply) in another which is laid out
by a |Container|.


Responsive grids
----------------

A responsive layout is one that arranges its contents differently,
depending on the size of the device it is being displayed on.

A |ColumnLayout| turns an |HTMLElement| such as a |Div| into one row
of an invisible grid. You can add |Widget|\s into each of its columns.
A |ResponsiveSize| states how wide a column should be for all the
different sizes of device. Sizes are stated in 1/12ths of the parent's
width. If the total width of all the columns in your row is more than
12/12ths, the row flows over and forms a grid.


In the code below, 12 columns of 1/12th the page width are added to a
|Div|. Each column is a |Div| itself and all have the same text in
them. Note that the |ResponsiveSize| is only set up with a size for medium
devices. This means that the columns will be 1/12th of the page on
medium (or larger) devices. On devices smaller than medium, each column
will expand to the full width with all the columns stacked on top of
one another. (On small devices it is better to have to scroll down
further to see content than to have to scroll right).

.. literalinclude:: ../../../reahl/doc/examples/tutorial/bootstrapgrids/bootstrapgrids.py
   :pyobject: GridBasicsPage.add_twelve

A |ColumnLayout| can also be constructed with a list of tuples stating
what columns it should have and what each one should be called. In
this case, it will add all the specified columns (each a |Div| itself)
to the |Div| you apply it to and make these available as a
dictionary. An example is shown here:


.. literalinclude:: ../../../reahl/doc/examples/tutorial/bootstrapgrids/bootstrapgrids.py
   :pyobject: GridBasicsPage.add_two

In order to really appreciate the power of |ResponsiveSize|, you will
have to fire up the example and play around with it. The example here
includes different Views -- this View is the first called "Grid
basics".

Here is a screenshot of what the page looks like:

.. figure:: ../../_build/screenshots/bootstrapgrids.png
  :align: center
  :width: 70%
  :alt: A screenshot of the page.

See how the layout changes if you change the size of the window when
running the example yourself. On displays that are medium sized or
larger (with your browser maximised), you will see two rows: one with
12 equal sized columns, and another with two columns that are not
equally sized.

As soon as you make the browser window smaller than "md" size, things
change: All the columns now stack on top of one another and
fill the whole width of the screen to make them more usable on the
smaller sized screen.



Laying out a whole page
-----------------------

It is often useful to layout an entire page with a header area at the
top, a footer at the bottom, and a content area in between. The content
area is also often divided into different columns.

You can layout a page in this fashion by using |PageLayout| in
conjunction with a suitable |ColumnLayout| to be used for its content
area. 

The "Page layout" view in our example shows how this works:

.. literalinclude:: ../../../reahl/doc/examples/tutorial/bootstrapgrids/bootstrapgrids.py
   :pyobject: PageLayoutPage


Notice how the same responsive properties hold for such pages too --
go ahead and make your browser window smaller on this example.

You can nest the usage of a |ColumnLayout| inside others (like the
columns on this page), thereby creating complex grid structures that
resize on all levels.


