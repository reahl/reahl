.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Models with makeup
==================

.. sidebar:: Examples in this section

   - tutorial.modeltests1
   - tutorial.modeltests2
   - tutorial.modeltests3

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

After having seen `the basic Reahl concepts <../buildingblocks.rst>`_
you must be itching to see a running user interface. The first
application implements a kind of address book: it has a single page
showing a list of names of people and their associated email
addresses. It also has a spot where you can add a new email address.

   .. figure:: ../_build/screenshots/addressbook2.png
      :align: center
      :width: 80%
      :alt: Screenshot showing a list of addresses, followed by inputs
	    for a name and email address, and a button to add the
	    address from the details in these inputs.

      A screenshot of our first application.


This application, simple as it may seem, is not only about showing
stuff on the web. The application spans a number of development concerns:

 - It has a design, and an object oriented one at that.
 - It persists objects from its design into a relational database, and thus must 
   do some form of object relational mapping.
 - It displays stuff on the screen.
 - It validates that input received from a user is legal; and
 - It executes actions on the server in response to user actions.

In this tutorial, this application will be built up, bit by bit from
the bottom to the top. These are the steps we will work through:

 #. Show what we mean by a model (an OO design), and how we test models.
 #. Change the model so that it can be persisted in a database (and how such trickier models are tested).
 #. Augment the model with information that will help us to generate a user interface for it.
 #. Do some housekeeping to ensure that Reahl creates and maintains the underlying database for our model.
 #. Design a basic user interface, as different Widgets.
 #. Add Inputs to allow user interaction via the user interface.


Models
------

In an object oriented program, the problem domain for which the
program is written is modelled using classes and objects.

Such a model forms the basis of the application, and Reahl requires a
programmer to augment models with code that is in turn used when
creating an actual user interface. This makes a discussion of Reahl
models necessary before we can go on.

Here is a simple model for an address book application:

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests1.py
   :pyobject: Address

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests1.py
   :pyobject: AddressBook


Exercising a model
------------------

.. sidebar:: Behind the scenes

   `Nosetests <https://nose.readthedocs.org/en/latest/>`_ is a project
   that makes writing and running tests a bit easier. Reahl provides
   some extensions to nosetests as well -- but that is a topic for
   another day.

   Be sure to check out Nosetests, as it is used throughout examples
   and Reahl code.

Whenever you write code that forms part of a model, it is useful to be
able to execute that code. The same is true for the examples presented
in this chapter.

The sensible way to execute code is to write some tests for that code.
Hence *each example here is a test* -- and to keep things simple we
include the toy model and its test together in a single file each time.

To put the simple model presented above through its paces, you can
put it together with a test in a file as follows, say test.py:

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests1.py

You can execute this example by running:

.. code-block:: bash

   nosetests test.py

Sometimes it is useful to include a line somewhere in that test which
will invoke the Python debugger so that you can play around with the
running code:

.. code-block:: python

   import pdb; pdb.set_trace()

...but then be sure to invoke nosetests with its `-s` commandline
option:

.. code-block:: bash

   nosetests -s test.py

   


Models that persist
-------------------

The model above is a bit naïve.

Sure, you can create Addresses and save them to an AddressBook, but
all of this is done in memory.  A real world application rarely works
like this. Usually at least some of the objects would need to be saved
to a database to avoid losing them. This is especially true for web
applications, :doc:`given their nature <buildingblocks>`.

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
create an Address in memory, but we will decide later on whether the
newly created Address should be saved to the database or not.


Of course, the assignment of `elixir.Field` instances to
`email_address` and `name` is how one instructs Elixir to persist
these data items to the database for a particular Address
instance (but you already knew that).

Exercising such database code involves just one more cinch:

Reahl manages a few things related to the database behind the scenes.
For example, it takes care of creating and committing database
transactions at the appropriate times.

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


Reahl models use makeup
-----------------------

If you were to write user interface code on top of this model, the
point of such user interface code would be to allow a user to
manipulate and interact with the model.

A Reahl programmer explicitly states which actions could be invoked on
the model from a user interface, and what can be input into or output
from the model. Having done this, writing the actual user interface
itself becomes much easier.

In our example, you may want to input or output certain data items
that are part of Address: the `name` and `email_address` attributes of
an Address. You may also want to invoke the :class:`~reahl.component.modelinterface.Action` of saving a new
Address to the database.

Here is the model again, with the additional information added:

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests3.py
   :lines: 4-6

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests3.py
   :pyobject: Address

.. sidebar:: Fields vs Fields

   One thing that may be confusing is that Elixir Fields are added to
   Address, but Reahl :class:`~reahl.component.modelinterface.Field`\ s are added as well.

   You have to keep in mind that Elixir has the job of persisting data
   in a database.  The Elixir Field for `email_address` specifies that
   the `email_address` attribute of an Address object will be saved to
   a database column that can deal with unicode text.

   The Reahl :class:`~reahl.component.modelinterface.Field` added for `email_address` is not concerned with
   persistence at all. It specifies several bits of useful
   metainformation about the `email_address` attribute of an Address
   object -- information that can be used to govern interaction with
   users.

   Reahl :class:`~reahl.component.modelinterface.Field`\ s could happily describe an attribute which does not get
   persisted at all. Similarly, an Elixir :class:`~reahl.component.modelinterface.Field` could happily
   describe an attribute that is not `exposed` to a user interface.


A lot is going on here, and you need to understand it.

The improved version of our Address now sports some new attributes: a
`.fields` and `.events` attribute.

The `.fields` attribute contains all the data elements on an
Address which can be accessed via a user interface. (These are the
things that can be input or output.)

Similarly, `.events` contains all the :class:`~reahl.component.modelinterface.Event`\ s a user could
trigger from the user interface, and specifies which :class:`~reahl.component.modelinterface.Action` (if any)
will be executed upon receipt of each such an :class:`~reahl.component.modelinterface.Event`.

The extra information provided by :class:`~reahl.component.modelinterface.Event`\ s and :class:`~reahl.component.modelinterface.Field`\ s is useful in other
contexts. Take the `label` that is specified everywhere, for
example. This is what a user may call the :class:`~reahl.component.modelinterface.Field` (or :class:`~reahl.component.modelinterface.Event`) in natural
language -- quite a useful bit of information when you want to create a
user interface referring to the :class:`~reahl.component.modelinterface.Field` or :class:`~reahl.component.modelinterface.Event`.

The `required=True` keyword argument can be passed to a :class:`~reahl.component.modelinterface.Field` to say
that this information normally has to be provided as part of input.
(What good is an Address with only a `name`, or only an
`email_address`?)

Notice also that `email_address` is an :class:`~reahl.component.modelinterface.EmailField`. A valid email
address has a specific form.  The string 'john' is not a valid email
address, but 'johndoe@world.org' is. Because `email_address` was
specified as an :class:`~reahl.component.modelinterface.EmailField`, user input to `email_address` can now be
validated to make sure only valid input ever makes it into the model.

The following test contains some code that sheds light on how the
Reahl framework could use these attributes internally to obtain more
information about a :class:`~reahl.component.modelinterface.Field`, or, for example validate user input
to a :class:`~reahl.component.modelinterface.Field`.

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests3.py
   :lines: 2,7

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests3.py
   :pyobject: test_reahl_additions

.. note:: 

   This test includes the use of `expected()`. This is just a way to
   state that the code block it applies to is expected to raise an
   exception of the given type.

   Of course, expecting `NoException` is a special case and just a
   convenient way to explicitly state that no exceptions are expected.

   The `expected()` function is part of `reahl.tofu`, a package which
   provides some extra testing tools -- some as extensions to Nosetests.


Why models and makeup belong together
-------------------------------------

Augmenting a model like this is something new and unfamiliar. What's
worse is that adding this stuff is extra work and the usefulness of it
is not obvious at this point.

The extra information provided about your model in this way is
information which the Reahl user interface machinery needs to be able
to do its work. (:doc:`Validation <../features/validation>` is one of
the tasks Reahl performs using this info.)

Think about it for a moment, though: the knowledge about what
constitutes a valid `email_address` for an Address naturally belongs
with Address, doesn't it? It would not make sense to write that
knowledge on a :class:`~reahl.web.ui.Form` somewhere on a screen: The email_address of an
Address could potentially be used on many different :class:`~reahl.web.ui.Form`\ s in many
different places and you'd have to duplicate that knowledge in all of
those places. Think about the possibilities as well: one could write a
graphical user interface alongside a web based one for the exact same
model. Such a graphical interface would need the exact same
information provided here, and can re-use it for free.


Persistent models require special care
--------------------------------------

There's one more thing to know about models (those that are persisted):

A model should live in a Reahl component -- like any other code. The Reahl
component infrastructure needs to be made aware of the classes that
can be persisted in each component. This is necessary because the command 
line tools perform certain tasks that need this information as input. 
These tasks include creating the database schema or creating or dropping
tables, for example.

The example presented here is just a simple file. This is not representative
of the model code you'd find in an actual project. In an actual project,
your code would always be part of a component, as :doc:`discussed previously 
<gettingstarted>`. To make the Reahl infrastructure aware of the persisted 
classes in a component, just add a list of `<class>` tags inside a 
single `<persisted>` section in the `.reahlproject` file of the 
component in which the code lives.

The example in the :doc:`next section <uibasics>` illustrates this. It is 
a complete Reahl application inside its own component, and it uses a 
similar Address class to the one shown here. In its component (as with 
all components) there is a `.reahlproject` file, containing the following
`<persisted>` section:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook2/.reahlproject
   :language: xml
   :start-after: <persisted>
   :end-before:  </persisted>
   :prepend: <persisted>
   :append: </persisted>


For each class, a `locator` is specified. The part of the `locator`
after the ':' is the Python class you want to list, and the part
before the ':' is the Python module where it is to be found.

Whenever you change a `.reahlproject` file though, be sure to run (for
that project):

.. code-block:: bash

   reahl setup -- develop -N

Your Python Egg's meta information is regenerated from the
`.reahlproject` file when setup is run like this.

Remember that after adding a new persisted class, you need to create
the necessary database schema for it:

.. code-block:: bash

   reahl-control createdbtables etc

