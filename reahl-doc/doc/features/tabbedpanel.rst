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

Implementing such a tabbed panel is non-trivial. Perhaps you want to
let its tabs be switched via JavaScript to prevent the entire page
from being reloaded when switching to a different tab. At the same
time though you'll want users who browse without JavaScript to also be
able to navigate to different tabs. What about making sure that search
engines can crawl to different tabs and index them, or allowing a user
(or a search engine) to bookmark a specific tab. Have a look at `this
article
<http://alistapart.com/article/aria-and-progressive-enhancement#section6>`_
which is one of many you'd have to read to build a nice tabbed panel.

**The programmer who is building an application for an end-user does
not want to have to think about these issues.**

It is much more useful to have a reusable TabbedPanel widget available
for use, to which you can add Tabs, each with its own heading and
contents -- all of which you can describe in Python, and only
Python. The implementation details are irrelevant (assuming they're
done well).

