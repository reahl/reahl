.. Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Reacting to user events
=======================

In Reahl, each screen the user can see is called a View. The user is
transitioned from one View to another depending on which Event a
user action triggers.

You program how the user is transitioned between different Views
depending on which Events are fired, and you can make such transitions
conditional using Guards.

The example here has three Views. If the user `submits` a comment on
the home View, and *did* enter some text for the comment, the next
View shown is '/thanks'. If the user *did not* enter any text, '/none'
is shown instead:

   .. figure:: pageflow.png
      :align: center
      :width: 80%
      :alt: A graph showing each View as a node, with arrows showing how the user would transition between the views.

Events are defined on an object (just like Fields are). Each Button is
linked to the Event it will fire when clicked. Each Event is in turn optionally
linked to an Action.

Defining the entire design depicted visually above is preferably done
in one place: the `assemble` method of your UserInterface. Here each
View is defined, as well as the Transitions between the Views.


.. literalinclude:: ../../reahl/doc/examples/features/pageflow/pageflow.py

.. note::

   This example does not set a different page for each View. That would have
   required us to create a page class for each View. We rather use :doc:`a different
   technique using Slots and a page defined for the entire UserInterface <../tutorial/slots>`
   that saves some typing.


