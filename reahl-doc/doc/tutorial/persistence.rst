.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.

A persistent model
==================

.. sidebar:: Examples in this section

   - tutorial.modeltests2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>



The model from :doc:`the previous chapter <models>` is a bit naïve.

Sure, you can create Addresses and save them to an AddressBook, but
all of this is done in memory.  A real world application rarely works
like this. Usually at least some of the objects would need to be saved
to a database to avoid losing them. This is especially true for web
applications.

Persisting a model using Elixir
-------------------------------

Reahl does not implement persistence mechanisms by itself. That's a
tough nut to crack. Besides there are cool tools for persisting
objects in Python. Reahl merely provides some glue so these tools can
be used easily. `SqlAlchemy <http://www.sqlalchemy.org/>`_ and its
companion project, `Elixir <http://elixir.ematia.de/trac/wiki>`_ work
in unison to deal with this persistence problem. If you are not
familiar with these tools, please refer to their respective
documentation.

Let's shift to a more real world model for an address book
application. If Address instances can be persisted in a database, 
an AddressBook is not needed anymore. An AddressBook was merely the
thing that held on to our Addresses and the database does the job
just as well, if not better.

That leaves a model consisting of a single class:

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests2.py
   :lines: 3-4

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests2.py
   :pyobject: Address

This shows mostly Elixir/SqlAlchemy stuff (which you should be
familiar with from reading up on those projects), with a little Reahl
help. Notice that Session and metadata are imported from a Reahl
package. These are provided for working with Elixir/SqlAlchemy in a
Reahl program.

Elixir needs to be told to use the Session and metadata provided by
Reahl, and that's what the `using_options()` call is for.

The call to `using_mapper_options()` is needed because by default any
Elixir Entity is immediately saved to the database upon creation and
that's not really what we want in this example. We want to be able to
create an Address in memory, but will only save it to the database
later on if the user decides to click on the "Save" button.

Of course, the assignment of `elixir.Field` instances to
`email_address` and `name` is how one instructs Elixir to persist
these data items to the database for a particular Address
instance (but you already knew that).

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
   the test run? That is all standard Elixir/SqlAlchemy without any
   Reahl influence.

   In a complete Reahl program, none of this database housekeeping is
   visible in code -- Reahl provides tools that deal with it.


