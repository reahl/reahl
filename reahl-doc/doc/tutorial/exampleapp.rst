.. Copyright 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
A first application
===================

We are going to write a simple address book application. It has:

- a single page showing a list of email addresses; and
- a way to add a new email address on the same page.

   .. figure:: addressuischematic.png
      :align: center
      :width: 40%
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
 #. :doc:`Create custom Widgets to display a list of Addresses. <addresslist>`
 #. :doc:`Persist Address objects in the database. <addresslistdb>`

Older:
 #. :doc:`First we build a silly model (an OO design) to show what is meant by that, and how we test models. <models>`
 #. :doc:`Next, the model is changed (with tests) so that it can be persisted in a database. <persistence>`
 #. :doc:`Then, a component is created for the app, and persisted classes registered with that component so that Reahl has the info it needs to create and maintain the underlying database schema for you. <housingmodels>`
 #. :doc:`Some user interface fundamentals are explained next by building a simple first part of the user interface of our application using Widgets. <uibasics>`
 #. :doc:`Then it is time to add Input widgets (for adding a new address) to the user interface. To do that, the model is also augmented with meta information used by the user interface. <inputwidgets>`
 #. :doc:`Lastly, a "Save" Button is added to actually trigger the work server-side of adding this new address to the database. <buttonwidgets>`



