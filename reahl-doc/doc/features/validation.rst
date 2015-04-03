.. Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Validating user input
=====================

.. sidebar:: Behind the scenes

   The JavaScript bits of this functionality is implemented using
   `JQuery <http://www.jquery.org>`_ and the `JQuery validation plugin
   <http://docs.jquery.com/Plugins/Validation>`_.

Reahl does validation of user input differently. You declare what
Fields of an object can be input by a user. When creating an Input
Widget, you link it to such a Field. The same Field can be reused by
different Inputs on different screens. (There's more to Fields than
this, but this is the basic idea.)

What you get is validations done in JavaScript on the browser, but
*the same* validations are also performed server-side if the user
switched off JavaScript or when a malicious attempt is done to try and
circumvent your validations.

Our example only has a single Input, with its EmailField:

   .. figure:: ../_build/screenshots/validation1.png
      :alt: Screenshot showing a single input.

If you type an invalid email address and hit tab, the typed input is
checked and a specific error message is shown:

   .. figure:: ../_build/screenshots/validation2.png
      :alt: Screenshot showing a single input with invalid input, coloured red, with an accompanying error message.


The error message changes while the user types to indicate a different
ValidationConstraint is now failing:

   .. figure:: ../_build/screenshots/validation3.png
      :alt: Screenshot showing a single input with invalid input, coloured red with a different accompanying error message.


When the input is changed to a valid value, the message disappears:

   .. figure:: ../_build/screenshots/validation4.png
      :alt: Screenshot showing a single input with valid input.


Below is the *complete* source code for this example, followed by an explanation:

.. literalinclude:: ../../reahl/doc/examples/features/validation/validation.py

This application models the concept of a `Comment`, which is meant to
represent a comment which can be left by a user. The idea is that
users can leave comments, but have to "sign" each comment using their
email address.

Comment is said to @expose certain Fields which are used to receive
input from a user. In this case, a Comment has an email_address
attribute, exposed via an EmailField.

In the code for the CommentForm (the very last line) a TextInput
Widget is connected to the email_address field of a particular
Comment.  This EmailField is responsible for validating user input. 

