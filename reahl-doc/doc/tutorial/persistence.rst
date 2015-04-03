.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.

A persistent model
==================

.. sidebar:: Examples in this section

   - tutorial.modeltests2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>



The model from :doc:`the previous chapter <models>` is a bit naive.

Sure, you can create Addresses and save them to an AddressBook, but
all of this is done in memory.  A real world application rarely works
like this. Usually at least some of the objects would need to be saved
to a database to avoid losing them. This is especially true for web
applications.

Persisting a model using SqlAlchemy
-----------------------------------

The problem of mapping Object Oriented models to relational databases
is a considerable headache, but necessary if you want to work in
an Object Oriented programming language like Python!
Reahl does not implement persistence mechanisms by itself. That's a
tough nut to crack. Besides there are cool tools for persisting
objects in Python. Reahl merely provides some glue so these tools can
be used easily. `SqlAlchemy <http://www.sqlalchemy.org/>`_ 
deals with this persistence problem. 

Let's shift to a more real world model for an address book application
that uses SqlAlchemy for persistence. If Address instances can be
persisted in a database, an AddressBook is not needed anymore. An
AddressBook was merely the thing that held on to our Addresses and the
database does the job just as well, if not better.

That leaves a model consisting of a single class:

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests2.py
   :lines: 5-7

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests2.py
   :pyobject: Address

This shows mostly SqlAlchemy stuff, with a little Reahl help. Notice
that Session, Base and metadata are imported from a Reahl
package. These are provided for working with SqlAlchemy in a Reahl
program.

A discussion of SqlAlchemy is outside the scope of this tutorial, but here
are some pointers to readers unfamiliar with SqlAlchemy:

In order to map Address to a relational database table, we use SqlALchemy's
Declarative extension:

  * __tablename__ states which relational table Address instances go into
  * The assignment of `Column` instances to
    `email_address` and `name` states that those attributes of Address
    are to be inserted in similarly named columns on the relational database
    that are defined as per the Columns stated.
  * The id `Column` provides a unique identifier for each Address instance 
    (and is also its primary key in the database)
  * To actually persist an Address instance to the database, 
    `Session.add()` is called.

If you are not familiar with SqlAlchemy, please refer to its
documentation: no short introduction can ever do it justice.

Exercising a persistent model
-----------------------------

Exercising such database code involves a cinch: Reahl manages a few
things related to the database behind the scenes.  For example, it
takes care of creating and committing database transactions at the
appropriate times.

Usually this is done behind the scenes, out of the view (and concern)
of the programmer. In a test, though, a lot of the Reahl framework is
bypassed, so you have to do its job explicitly.  Luckily that is
easy -- database code just needs to be executed within an
:class:`~reahl.component.context.ExecutionContext`. This can be done as shown in the complete example
below:

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests2.py


.. note::

   Have you noticed how the first few lines of the `test_model()`
   connects to the database, ensuring that its schema is created for
   the test run? That is all standard SqlAlchemy without any
   Reahl influence.

   In a complete Reahl program, none of this database housekeeping is
   visible in code -- Reahl provides tools that deal with it.


