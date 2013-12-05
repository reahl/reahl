.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Validating user input
=====================

.. sidebar:: Behind the scenes

   The JavaScript bits of this functionality is implemented using
   `JQuery <http://www.jquery.org>`_ and the `JQuery validation plugin
   <http://docs.jquery.com/Plugins/Validation>`_.

The code in this section is the complete listing of a Reahl web
application which demonstrates the validation of a single item that
can be input by a user.

The application will render a sole text input on its home page:

   .. figure:: ../_build/screenshots/validation1.png


The user is expected to type a valid email address into the
input. When the user types something into the input and hits tab (for
example), the typed input is checked and a useful error message is
shown:

   .. figure:: ../_build/screenshots/validation2.png


The error message changes while the user types. For example, if
the user deletes the invalid email address, the message changes:

   .. figure:: ../_build/screenshots/validation3.png


When the input is changed to a valid value, the message disappears:

   .. figure:: ../_build/screenshots/validation4.png


The validation shown above is done in a user's browser using
JavaScript. Doing validation using JavaScript is desirable because it
gives immediate feedback to the user. There is a problem with doing
validation in JavaScript, however: a user could disable JavaScript and
bypass such validation.

Reahl guards against this scenario by re-checking the same validation
rules on the server side when the user clicks on a button. If the
validation fails, the same page is shown again with exactly the same
error messages, format and styling shown above for the JavaScript
version.

Here is a listing of the code, followed by an explanation:

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

