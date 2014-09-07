.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Persistence
===========

.. sidebar:: Behind the scenes (or, not so much *behind* this time)

   Persistence is done directly using `SqlAlchemy
   <http://www.sqlalchemy.org/>`_. If you are not
   familiar with this tool, please refer to its
   documentation.


This example implements another application which allows a user to leave
Comments.  Everything happens on one page though:

The home page first comes up with only a (somewhat prettied up) form
asking the user to leave a comment:

   .. figure:: ../_build/screenshots/persistence1.png
      :align: center
      :alt: A screenshot of a form with input for a user's email.

When the user clicks on submit, the new comment is persisted in
the database. When the page is refreshed, the form is still rendered,
but a list of all the comments in the database is shown below it:

   .. figure:: ../_build/screenshots/persistence2.png
      :align: center
      :alt: A screenshot of a form with input for a user's email, and also a list of previously entered email addresses.


The example uses a CommentPostPanel widget as the container of
everything shown on the home page. Its contents are: one CommentForm
widget (used to post a new Comment), and several CommentBox
widgets -- one for each posted Comment.

Notice that Reahl provides versions of SqlAlchemy's `Session`, `Base` and
`metadata` objects for use with Reahl applications. 


.. literalinclude:: ../../reahl/doc/examples/features/persistence/persistence.py
