.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
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
each :class:`~reahl.web.fw.View` inherit all the common elements.

In a large :class:`~reahl.web.fw.UserInterface` it becomes cumbersome
to do what we've done with AddressBookPage. :doc:`Later on you will
also learn how to incorporate other pre-existing<loggingin>`
:class:`~reahl.web.fw.UserInterface`\ s as part of your own
:class:`~reahl.web.fw.UserInterface`. Obviously if the look and layout
of the pages of a :class:`~reahl.web.fw.UserInterface` are hard-coded
like we've done with :doc:`our example <connectingviews>`, you would
not be able to incorporate it onto your web application, which has its
own look and layout!


Slots and Views without pages
-----------------------------

For all these reasons, there's another way to deal with many pages that look similar: 
You can attach a page to the entire :class:`~reahl.web.fw.UserInterface` instead of to each individual
:class:`~reahl.web.fw.View` inside it. Then you only need to specify as part of each :class:`~reahl.web.fw.View`  
what it would add to the page.

To make this possible, there is a special Widget, :class:`~reahl.web.ui.Slot`. On its own, a :class:`~reahl.web.ui.Slot`
does not render anything at all on the page it is a part of. It represents an empty area, the contents of which is meant to
be supplied by a :class:`~reahl.web.fw.View`. The :class:`~reahl.web.fw.View` then "plugs" only the bit of content 
specific to it into the supplied :class:`~reahl.web.ui.Slot`, on the fly.

There can be more than one :class:`~reahl.web.ui.Slot` on a page, and each one of then is referred to individually by name.

.. figure:: views.png
   :align: center
   :width: 90%

   A page with two different views.



See it in action
----------------


Below is the source code for an application that demonstrates these
ideas.

The application has two  :class:`~reahl.web.fw.View`\ s . Its page (a CustomPage) contains
an :class:`~reahl.web.ui.HMenu` (a horisontal menu) which allows one to navigate between the
two  :class:`~reahl.web.fw.View`\ s  of the application.

The home page looks as follows:

   .. figure:: ../_build/screenshots/slots1.png
      :align: center

Notice the two bits of text.  Each paragraph was plugged into a
separate :class:`~reahl.web.ui.Slot` of the page.

In "Page 2", the same page is displayed, but with different
text in those :class:`~reahl.web.ui.Slot`\ s:

   .. figure:: ../_build/screenshots/slots2.png
      :align: center


.. literalinclude:: ../../reahl/doc/examples/tutorial/slots/slots.py

A :class:`~reahl.web.ui.TwoColumnPage` is a handy :class:`~reahl.web.fw.Widget`, since it contains a sensible page
with all sorts of sub-parts to which one can attach extra :class:`~reahl.web.fw.Widget`\ s.  Of
interest here are its `.header` element (a :class:`~reahl.web.ui.Panel` positioned well for
holding things like menu bars), and two of its predefined :class:`~reahl.web.ui.Slot`\ s:
"main" and "secondary". These two slots represent the two columns of
the :class:`~reahl.web.ui.TwoColumnPage` :class:`~reahl.web.fw.Widget`: "main" is to the right, and fairly large,
whereas "secondary" sits to the left of it, and is narrower.

In this example, a CustomPage is derived from :class:`~reahl.web.ui.TwoColumnPage`. That way
the CustomPage inherits all the abovementioned niceties from
:class:`~reahl.web.ui.TwoColumnPage`. To ba a useful page for this application,
CustomPage only needs to add an :class:`~reahl.web.ui.HMenu` to the `.header` of the
:class:`~reahl.web.ui.TwoColumnPage` on which it is based.


