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

There are common user interface elements present on all the different
URLs of a web application. :doc:`Our previous example <connectingviews>` is the first one with more
than one page. We dealt with the commonality between its pages by
having a common class (AddressBookPage) from which the page used by 
each |View| inherit all the common elements.

In a large |UserInterface| it becomes cumbersome to do what we've done
with AddressBookPage. Moreover, what we did also hard-codes the main
layout (and usually, look) used for your application in the code of
the |UserInterface|. As you will learn later on, :doc:`it is also
possible to re-use other pre-existing<loggingin>` |UserInterface|\s as
part of your web application.

If you intend for a |UserInterface| to be re-usable in different web
applications, each with its own look and main layout, you cannot
hard-code what the final web page will look like.


Slots and Views without pages
-----------------------------

For all these reasons, there's another way to deal with many pages that look similar: 
You can attach a page to the entire |UserInterface| instead of to each individual
|View| inside it. Then you only need to specify as part of each |View|  
what that |View| adds to the page.

To make this possible, there is a special Widget, |Slot|. On its own, a |Slot|
does not render anything at all on the page it is a part of. It represents an empty area, the contents of which is meant to
be supplied by a |View|. The |View| then "plugs" only the bit of content 
specific to it into the supplied |Slot|, on the fly.

There can be more than one |Slot| on a page, and each one of then is referred to individually by name.

.. figure:: views.png
   :align: center
   :width: 90%

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



