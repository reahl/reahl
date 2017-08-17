.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |UserInterface| replace:: :class:`~reahl.web.fw.UserInterface` 
.. |View| replace:: :class:`~reahl.web.fw.View`
.. |Slot| replace:: :class:`~reahl.web.ui.Slot`

Make light work of similar-looking pages
========================================

.. sidebar:: Examples in this section

   - tutorial.slots

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

Slots and Views without pages
-----------------------------

In :doc:`the previous example <connectingviews>` all the pages of an
application are made to look similar by deriving each page from a
common superclass.

An |UrlBoundView| can plug different contents into the same page
provided that that page contains placeholders, called |Slot|\s. Each
|Slot| on a page is referred to by name.

.. figure:: views.png
   :align: center

   A page with two different views.



See it in action
----------------


Below is the source code for an application that demonstrates these
ideas.

The application has two  |View|\ s . Its page (a CustomPage) contains
an :class:`~reahl.web.ui.HMenu` (a horizontal menu) which allows one to navigate between the
two  |View|\ s  of the application.

The home page looks as follows:

   .. figure:: ../_build/screenshots/slots1.png
      :align: center

Notice the two bits of text.  Each paragraph was plugged into a
separate |Slot| of the page.

In "Page 2", the same page is displayed, but with different
text in those |Slot|\ s:

   .. figure:: ../_build/screenshots/slots2.png
      :align: center


.. literalinclude:: ../../reahl/doc/examples/tutorial/slots/slots.py

In the example, the :class:`~reahl.web.layout.PageLayout` is used
to give our plain :class:`~reahl.web.ui.HTML5Page` a `.header` (which
we can use to put a menu bar) and contents area. The contents are in turn
laid out using a :class:`~reahl.web.grid.bootstrap.ColumnLayout`. The column
named "main" is to the right, and fairly large, whereas "secondary"
sits to the left of it, and is narrower.

The :class:`~reahl.web.grid.bootstrap.ColumnLayout` also adds |Slot|\ s
in each column so that we can use the columns without having to hard-code their 
contents. The  :class:`~reahl.web.layout.PageLayout` does the same for the header 
and footer areas.

In this example, a CustomPage is derived from
:class:`~reahl.web.ui.HTML5Page`. That way the
:class:`~reahl.web.layout.PageLayout` can be applied to our
CustomPage, and a suitably laid out :class:`~reahl.web.ui.Menu` can be
added to the `.header` of all CustomPage instances.



