.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |UserInterface| ..replace:: :class:`~reahl.web.fw.UserInterface`
.. |UrlBoundView| ..replace :class:`~reahl.web.fw.UrlBoundView`
   
Moving between Views
====================

.. sidebar:: Examples in this section

   - tutorial.pageflow1
   - tutorial.pageflow2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

The user interface of the address book application can be
split up into two :class:`~reahl.web.fw.View`\ s : one that
lists all the addresses, and another on which you can add a new
address.

.. figure:: addressbooksplit.png
   :align: center
   :alt: A diagram showing two Views, and how one can move between them.

   The address book application with two |UrlBoundView|\s.


Bookmarks and Navs
------------------

A |Bookmark| marks a particular |UrlBoundView|.  A |Nav| is a menu
created from a list of |Bookmark|\s. It is a means for the user to
move around in the application.

The simplest way to have all pages look similar is to create a common
page from which you inherit all other pages in the application.

.. literalinclude:: ../../reahl/doc/examples/tutorial/pageflow1/pageflow1.py
   :pyobject: AddressBookPage

.. literalinclude:: ../../reahl/doc/examples/tutorial/pageflow1/pageflow1.py
   :pyobject: HomePage

.. literalinclude:: ../../reahl/doc/examples/tutorial/pageflow1/pageflow1.py
   :pyobject: AddPage


Notice how the bookmarks are collected in `AddressBookUI.assemble`,
and passed to |WidgetFactory| of each page. The |WidgetFactory|
arguments match those of the `__init__` method of each page.

.. literalinclude:: ../../reahl/doc/examples/tutorial/pageflow1/pageflow1.py
   :pyobject: AddressBookUI

AddressBookForm is unchanged in this example. AddressBookPanel though
contains a list of AddressBoxes, but no AddressBookForm---which is on
the other |UrlBoundView|.

.. literalinclude:: ../../reahl/doc/examples/tutorial/pageflow1/pageflow1.py
   :pyobject: AddressBookPanel


---------------------------------------------------------


Transitions
-----------

:class:`~reahl.web.fw.Bookmark`\ s form the cornerstone of any navigation which is under the
control of the user. Navigation that happens under the control of the
application has to be programmed explicitly.

The schematic diagram at the beginning of this example is a good way
to visualise the different  :class:`~reahl.web.fw.View`\ s  in the application and how the user
will be *transitioned* between the different  :class:`~reahl.web.fw.View`\ s  in response to user
actions. One of the aims with Reahl is to have code that clearly maps to such a
schematic representation of the application. This is the purpose of
the `.assemble()` method of a :class:`~reahl.web.fw.UserInterface`. In this method, the programmer
first defines each :class:`~reahl.web.fw.View` of the :class:`~reahl.web.fw.UserInterface`, and then defines each possible
:class:`~reahl.web.fw.Transition` between  :class:`~reahl.web.fw.View`\ s . In this example, there is only one :class:`~reahl.web.fw.Transition`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/pageflow2bootstrap/pageflow2bootstrap.py
   :pyobject: AddressBookUI

In previous examples an :class:`~reahl.web.fw.EventHandler` was defined before a :class:`~reahl.web.ui.Button` is
placed that needed to trigger an :class:`~reahl.component.modelinterface.Event`. That plan works well for
simple examples -- where a user stays on the same page after an
:class:`~reahl.component.modelinterface.Event`. Where users are moved around by the application, it makes more
sense to show such navigation more explicitly. :class:`~reahl.web.fw.Transition`\ s are special
:class:`~reahl.web.fw.EventHandler`\ s used for this purpose.

Drawing a diagram of how a user can self-nagivate to pages is not very
useful though, because users can jump to many different  :class:`~reahl.web.fw.View`\ s  via
:class:`~reahl.web.fw.Bookmark`\ s on :class:`~reahl.web.ui.Menu`\ s (or even the bookmarks of the browser
itself). Hence usually we would draw the schematic without its :class:`~reahl.web.ui.Menu`,
and only include arrows for :class:`~reahl.web.fw.Transition`\ s between  :class:`~reahl.web.fw.View`\ s . This is the
picture which the code of `.assemble()` tries to make explicit.

Normally, in order to define a transition, one needs to specify the
:class:`~reahl.component.modelinterface.Event` which will trigger it. In our example that :class:`~reahl.component.modelinterface.Event` is not
available, since there is no instance of Address available in the
`.assemble()` method of the :class:`~reahl.web.fw.UserInterface` to ask for its `.events.save`.
For that reason, `.events.save` can also be called on the Address
class itself. The call to `.define_transition` (and its ilk) does
not need the actual event -- it just needs to know how to identify the
:class:`~reahl.component.modelinterface.Event` which serves as its trigger. The `.events` attribute, when
accessed on a class yields this information, but it can only do so for
events that were named explicitly in the call to the `@exposed` decorator.
(This limitation is neccessitated by what is possible in the
underlying implementation of the mechanism.)

The modified final code for our current example is shown below. Note
the following changes as per the explanation above:

 - the call to `.define_event_handler` was removed
 - a new call to `.define_transition` was added (accessing
   `Address.events.save`); and
 - the `@exposed` decorator was changed to explicitly include the
   names of the :class:`~reahl.component.modelinterface.Event`\ s it will define when called

.. literalinclude:: ../../reahl/doc/examples/tutorial/pageflow2bootstrap/pageflow2bootstrap.py


Guards
------

:class:`~reahl.web.fw.Transition`\ s between  :class:`~reahl.web.fw.View`\ s  define the "page flow" of a web application.
Such "page flow" is not always simple. Sometimes it is desirable to have
more than one :class:`~reahl.web.fw.Transition` for a particular :class:`~reahl.component.modelinterface.Event`, but have the system choose 
at runtime which one should be followed.

In order to allow such an arrangement, a :class:`~reahl.web.fw.Transition` can be accompanied
by a guard. A guard is an :class:`~reahl.component.modelinterface.Action` which wraps a method that
returns True or False.  Usually, the framework just picks the
first :class:`~reahl.web.fw.Transition` it can find when needed and follows it. Augmenting
:class:`~reahl.web.fw.Transition`\ s with guards changes this scheme.

When a :class:`~reahl.web.fw.Transition` is found that can be followed, the guard of the
:class:`~reahl.web.fw.Transition` is first executed. That :class:`~reahl.web.fw.Transition` is the only followed if
its guard returns True. If a guard returns False, the search is
continued non-deterministically for the next suitable :class:`~reahl.web.fw.Transition` (with
True guard).

In order to specify a guard for a :class:`~reahl.web.fw.Transition`, pass an :class:`~reahl.component.modelinterface.Action` to the
'guard' keyword argument of `.define_transition()`. (See :doc:`../features/pageflow` for an example.)





