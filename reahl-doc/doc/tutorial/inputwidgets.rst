.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Getting input from a user
=========================

.. sidebar:: Examples in this section

   - tutorial.addressbook2
   - tutorial.modeltests3

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

User input is a tricky thing. Users always provide input as strings,
but programs work in terms of objects such as integers, boolean
values, dates, etc. Part of dealing with user input thus means
translating (or marshalling) such a string to the actual Python object
it represents. That's not all though -- user input also need to be
validated, and appropriate error messages given to guide a user as to
what the program considers valid input.

These are considerable tasks for a framework to deal with.

User input in Reahl
-------------------

In order to get input from a user, Reahl uses special
:class:`~reahl.web.fw.Widget`\ s, called
:class:`~reahl.web.ui.Input`\ s. The responsibility of an
:class:`~reahl.web.ui.Input` is to show a user the value of some item
in your program, and allow the user to change that value. There are
different kinds of :class:`~reahl.web.ui.Input`\ s representing
different ways of dealing with the visual and behavioural aspects of
this task.

Another player, the :class:`~reahl.component.modelinterface.Field`, has
the job of checking whether a string sent by a user is valid, to turn
that string into Python object, and to finally set such a Python
object as the value of an attribute of one of your model objects

One thing about :class:`~reahl.web.ui.Input`\ s: they differ from
other :class:`~reahl.web.fw.Widget`\ s in that they have to live as
children of a :class:`~reahl.web.ui.Form`.

Here is a what we need in the address book application:

   .. figure:: inputs.png
      :align: center
      :width: 80%
      :alt: A diagram showing a TextInput linking to an EmailField, in turn linking the email_address attribute of an Address object

      A TextInput linked to the email_address attribute of an Address, via an EmailField



Reahl models use makeup
-----------------------

The first step towards allowing a user to input anything, is to
augment the model with :class:`~reahl.component.modelinterface.Field`\
s that represent each attribute accessible from the user interface of
the application. In our example, the `name` and `email_address` attributes of
an Address are exposed to the user.

To augment our Address class with :class:`~reahl.component.modelinterface.Field`\ s, create a special method `fields()` on the class, and annotate it with the `@exposed` decorator. Such a method should take one argument: `fields` on which you can set each :class:`~reahl.component.modelinterface.Field` needed. Take care though -- each :class:`~reahl.component.modelinterface.Field` you create will eventually manipulate an attribute of the same name on instances of your class:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook2/addressbook2.py
   :prepend: class Address(elixir.Entity):
   :start-after: class Address(elixir.Entity):
   :end-before: def save(self):

The `@exposed` decorator turns your `fields()` method into a property
named `fields` on instances of this class. The property is special
only in that it is initialised by the method you provide.

The `.fields` attribute of an Address instance now contains a
:class:`~reahl.component.modelinterface.Field` for each corresponding
attribute on that Address which can be accessed via a user
interface. We will need it in a moment when we start creating
:class:`~reahl.web.ui.Input`\ s.

.. note:: Fields vs Fields

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



Fields provide information about attributes
-------------------------------------------

.. sidebar:: For the curious

   If you want a deeper understanding of the concept of a
   :class:`~reahl.component.modelinterface.Field`, check out the
   `tutorial.modeltests3` example. It shows how
   :class:`~reahl.component.modelinterface.Field`\ s are used
   internally by the framework.

The extra information provided by :class:`~reahl.component.modelinterface.Field`\ s is useful in other
contexts. Take the `label` that is specified everywhere, for
example. This is what a user may call the :class:`~reahl.component.modelinterface.Field` in natural
language -- quite a useful bit of information when you want to create a
user interface referring to the :class:`~reahl.component.modelinterface.Field`.

The `required=True` keyword argument can be passed to a :class:`~reahl.component.modelinterface.Field` to say
that this information normally has to be provided as part of input.
(What good is an Address with only a `name`, or only an
`email_address`?)

Notice also that `email_address` is an :class:`~reahl.component.modelinterface.EmailField`. A valid email
address has a specific form.  The string 'john' is not a valid email
address, but 'johndoe@world.org' is. Because `email_address` was
specified as an :class:`~reahl.component.modelinterface.EmailField`, user input to `email_address` can now be
validated automatically to make sure only valid input ever makes it into the model.

Adding the actual Widgets
-------------------------

.. sidebar:: No magic allowed here

   If you were wondering how a LabelledBlockInput figures out which 
   label to display next to its TextInput... remember all of that
   information is available on each Field. 

   Fields can contain much
   more information than this -- leveraged by the framework to do
   much more for you. You will discover these bits later on throughout
   the tutorial.

You should have gathered by now that we are going to have to add a
:class:`~reahl.web.ui.Form` so that we can also add
:class:`~reahl.web.ui.TextInput`\ s for each of the
:class:`~reahl.component.modelinterface.Field`\ s we are
exposing. That's not the entire story though: we want it to look nice
too -- with a label next to each :class:`~reahl.web.ui.TextInput`, and
successive labels and :class:`~reahl.web.ui.TextInput`\ s neatly
aligned underneath each other. It would also be visually pleasing if
we add a heading to this section of our page.

Two elements come to our aid in this regard: An
:class:`~reahl.web.ui.InputGroup` is a :class:`~reahl.web.fw.Widget`
that groups such a section together, and give the section a heading.
A :class:`~reahl.web.ui.LabelledBlockInput` is a
:class:`~reahl.web.fw.Widget` that wraps around another
:class:`~reahl.web.ui.Input` (such as a
:class:`~reahl.web.ui.TextInput`), and provides it with a
label. Successive :class:`~reahl.web.ui.LabelledBlockInput`\ s will
arrange themselves neatly below each other.

What's needed thus, is to create a :class:`~reahl.web.ui.Form`,
containing an :class:`~reahl.web.ui.InputGroup`, to which is added two
:class:`~reahl.web.ui.LabelledBlockInput`\ s, each wrapped around a
:class:`~reahl.web.ui.TextInput` that is linked to the appropriate
:class:`~reahl.component.modelinterface.Field`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook2/addressbook2.py
   :prepend: class AddressBookPanel(Panel):
   :start-after: class AddressBookPanel(Panel):
   :end-before: self.define_event_handler(new_address.events.save)

Let's finish the example in :doc:`the next section <buttonwidgets>`.


