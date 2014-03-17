.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
A tabbed panel example
======================

A common requirement in web applications is a page which contains a
number of tabs between which a user can flip -- each with different
content.

A simple example is illustrated in the figure below:

   .. figure:: ../_build/screenshots/tabbedpanel1.png
      :align: center
      :width: 70%
      
Should a user click on a different tab, different contents are displayed:

   .. figure:: ../_build/screenshots/tabbedpanel2.png
      :align: center
      :width: 70%

Here is the complete Reahl web application which produces the TabbedPanel
in the figure above (notice the MyTabbedPanel class):

.. literalinclude:: ../../reahl/doc/examples/features/tabbedpanel/tabbedpanel.py

Using Reahl, this is written entirely in Python, and in terms of user
interface widgets: You create your own widget class (MyTabbedPanel in
this case), and populate it with Tabs in its ``__init__`` method. Each
Tab is given a *factory* it can use to generate its own contents (in
each case here, just a paragraph with text.

What you get for that is tabs that can be switched via JavaScript,
preventing the entire page to be refreshed when the user switches
tabs. For users who have JavaScript switched off, the tabs still
work, they just result in the page being refreshed. Search engines can
crawl these tabs, and they can be bookmarked by browsers.

All these extra considerations you get without having to break a sweat
-- and you get the better implementation each time we improve it.


