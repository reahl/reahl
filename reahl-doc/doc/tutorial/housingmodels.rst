.. Copyright 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.

Models live in components
=========================

.. sidebar:: Examples in this section

   - tutorial.addressbook1

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Create a component
------------------

Up to now, the example presented was just a simple file containing
application code and a test. This is not representative of the 
code you'd find in an actual project. In an actual project, your code
would always be part of a component, as :doc:`discussed previously
<gettingstarted-develop>`. 

It is time to create a component for our project, and put the code for
our model in there. We'll skip testing further :doc:`until a bit later
<testing>`, so just go ahead and create a project :doc:`as before
<gettingstarted-develop>`, with our new model code in a file called
`addressbook1.py`.

Register the models that live there
-----------------------------------

A model should live in a Reahl component -- like any other code. The Reahl
component infrastructure needs to be made aware of the classes that
can be persisted in each component. This is necessary because the command 
line tools perform certain tasks that need this information as input. 
These tasks include creating the database schema or creating or dropping
tables, for example.

To make the Reahl infrastructure aware of the
persisted classes in a component, you must add a list of `<class>` tags
inside a single `<persisted>` section in the `.reahlproject` file of
the component in which the code lives:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/.reahlproject
   :language: xml
   :start-after: <persisted>
   :end-before:  </persisted>
   :prepend: <persisted>
   :append: </persisted>


For each class, a `locator` is specified. The part of the `locator`
after the ':' is the Python class you want to list, and the part
before the ':' is the Python module where that class is to be found.

Housekeeping and your database schema
-------------------------------------

Whenever you change a `.reahlproject` file though, be sure to run (for
that project):

.. code-block:: bash

   reahl setup -- develop -N

Your Python Egg's meta information is regenerated from the
`.reahlproject` file when setup is run like this.

Of course, at this point your database schema needs to be updated to include tables for this new class. Thus, you need to run:

.. code-block:: bash

   reahl-control createdbtables etc

.. note::

   The `createdbtables` command will only succeed if you have not run it before. In this case you can always
   undo your previous run before you re-create the tables, by running:

   .. code-block:: bash

      reahl-control dropdbtables etc

