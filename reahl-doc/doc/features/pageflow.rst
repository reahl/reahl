.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Reacting to user events
=======================

Any web application needs to control what gets executed in response to
a user action, and also how the user is transitioned between the
different pages of an application. The application presented here
illustrates the basics of how this is done in Reahl.

There are three pages in the example application presented here. If
the user `submits` a comment on the home page, and *did* enter some
text for the comment, the next page shown is '/thanks'. If the user
*did not* enter any text, '/none' is shown instead.

A visual representation shows this succinctly:

   .. figure:: pageflow.png
      :align: center
      :width: 80%
      :alt: A graph showing each View as a node, with arrows showing how the user would transition between the views.

Remember :doc:`how user input is controlled by means of Fields
<validation>`? The Actions a user can trigger are similarly controlled
by means of Events.

Note in the code below how a Comment @exposes a `submit` Event, which
will result in the execution of the `submit` method of the Comment
when triggered. The execution of the `submit` method renders the
following output on the console:


.. literalinclude:: ../_build/screenshots/pageflow2.txt


To enable a user to actually trigger this Event, a Button is linked to
the Event.

Defining the entire design depicted visually above is done in one
place: the `assemble` method. Here each View is defined, as well as a
number of Transitions between Views.


.. literalinclude:: ../../reahl/doc/examples/features/pageflow/pageflow.py


