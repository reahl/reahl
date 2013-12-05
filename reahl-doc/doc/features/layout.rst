.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Layout example
==============

.. sidebar:: Behind the scenes

   Reahl implements all layout-related functionality in terms of the
   `YUI grids css framework <http://developer.yahoo.com/yui/grids/>`_.

Several special widgets are provided to help position elements on a
page. The example presented here shows some of these widgets in action.

The source code given below results in the following visual layout:

   .. figure:: ../_build/screenshots/layout.png
      :align: center
      :width: 100%

The first thing to notice in the code given below is the notion of a
widget used as the `main window` of your application.  The main window
is the widget which will appear on all pages of your application ---
but with slightly different contents depending on the particular URL
visited.

Although you can roll your own, Reahl includes, for example, a
TwoColumnPage which takes care of the basic layout of pages. In this
example text is inserted to show the different areas which can be
populated when using a TwoColumnPage.

Widgets like the LabelledBlockInput can be used to do the internal
layout of elements of a form. A LabelledBlockInput wraps around any
simple input and provides it with a label. It also positions all the
relevant constituent elements neatly --- including possible validation
error messages.

Lastly, for users familiar with `YUI-style layout grids
<http://developer.yahoo.com/yui/grids/>`_, widgets are provided
representing these lower-level layout tools.


.. literalinclude:: ../../reahl/doc/examples/features/layout/layout.py
