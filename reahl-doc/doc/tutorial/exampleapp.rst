.. Copyright 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
A basic application
===================

We are going to write a simple address book application. It has:

- a single page showing a list of email addresses; and
- a way to add a new email address on the same page.

   .. figure:: addressuischematic.png
      :align: center
      :alt: A visual schematic showing what the application home page should contain.

      The home page -- schematically.


This application, simple as it may seem, spans a number of development
concerns that will be explained along the way:

 - It has a design, and an object oriented one at that;
 - It persists objects from its design into a relational database, and thus must 
   do some form of object relational mapping;
 - It displays stuff on the screen;
 - It validates that input received from a user is legal; and
 - It executes actions on the server in response to user actions.

Later on in the tutorial increasingly complicated variations of
this simple application are used to introduce other concepts. 

For now, though, this application will be built up bit by
bit in these steps:

 #. :doc:`Start by making a basic page to learn about layout. <styling>`
 #. :doc:`Create custom Widgets to display a list of Addresses. <uibasics>`
 #. :doc:`Persist Address objects in the database. <persistence>`
 #. :doc:`Let the user add Addresses. <inputwidgets>`




