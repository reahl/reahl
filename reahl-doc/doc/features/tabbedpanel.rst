.. Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Widgets let you work on a conceptual level
==========================================

You need a lot of stuff to make something work on a web page: some
dynamically generated HTML, some JavaScript, some CSS and some URLs
on a server that provide other resources, such as embedded images or
web services that validate input.

We can write all these bits for you, and deliver them packaged in a
Python class that is easy to use. A tabbed panel is a simple example
of this:

   .. figure:: ../_build/screenshots/tabbedpanel1.png
      :align: center
      :width: 70%
      :alt: A screenshot of a tabbed panel, open at one tab.
      
Should a user click on a different tab, different contents are displayed:

   .. figure:: ../_build/screenshots/tabbedpanel2.png
      :align: center
      :width: 70%
      :alt: A screenshot of a tabbed panel, open at a different tab.

With Reahl, you can create a TabbedPanel object, add Tab objects to it
and specify what each Tab should be filled with once opened. 

For that, you get a working tabbed panel with its JavaScript that
takes care to keep the browser's back button working. You also get
server-side functionality that make the panel work even when
JavaScript is disabled (useful for search engine indexing amongst
other things). When we improve TabbedPanel, you get those improvements
without changes to your code.

Here is the *complete* Reahl web application which produces the TabbedPanel
in the figure above:

.. literalinclude:: ../../reahl/doc/examples/features/tabbedpanel/tabbedpanel.py



