.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
A tabbed panel example
======================

A common requirement in web applications is a page which contains a
number of tabs between which a user can flip -- each with different
content.

A simple example is illustrated in the figure below:

   .. figure:: ../_build/screenshots/tabbedpanel1.png
      :align: center
      :width: 70%
      :alt: A screenshot of a tabbed panel, open at one tab.
      
Should a user click on a different tab, different contents are displayed:

   .. figure:: ../_build/screenshots/tabbedpanel2.png
      :align: center
      :width: 70%
      :alt: A screenshot of a tabbed panel, open at a different tab.

Here is the complete Reahl web application which produces the TabbedPanel
in the figure above:

.. literalinclude:: ../../reahl/doc/examples/features/tabbedpanel/tabbedpanel.py

Using Reahl, this is written entirely in Python, and in terms of user
interface widgets: You create a page by inheriting from the existing
HTML5Page Widget (which comes with a `.body` already). In the
``__init__`` of that page, you add a TabbedPanel Widget as a child to
the body of this HTML5Page, and populate the TabbedPanel
with Tabs. Each Tab is given a *factory* it can use to generate its
own contents if and when that becomes necessary (in each case here,
the contents is just a paragraph with text, but it could have been any
Widget).

What you get for that is tabs that can be switched via JavaScript,
preventing the entire page to be refreshed when the user switches
tabs. For users who have JavaScript switched off, the tabs still
work, they just result in the page being refreshed. Search engines can
crawl these tabs, and they can be bookmarked by browsers.

All these extra considerations you get without having to break a sweat
-- and you get the better implementation each time we improve it.


