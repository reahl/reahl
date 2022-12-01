.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.




What changed in version 6.1
===========================

Upgrading
---------

To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc

   
A new way of exposing Fields and Events
---------------------------------------

Reahl's |Field|\s (or |Event|\s) :doc:`can be defined on a normal
model object <tutorial/inputwidgets>`.

The usual way of defining extra semantics for an attribute of
instances of a particular class is to define the attribute in class
scope in a special way, as is done by SqlAlchemy, Django ORM, etc.

Since a Reahl programmer could use those tools as well for the same
attribute on a given class, the same plan cannot also be implemented
for designating an attribute as being a Reahl |Field|, for example.

Initially, this was accomplished using the |exposed| decorator, but
we felt this is a very unfamiliar way of defining such behaviour.

In this release, the |exposed| decorator is deprecated in favour of
a new plan that is more aligned with how well known frameworks work.

Previously |exposed| was used to define attributes in a instance-side method:

.. code-block:: python

   class Address(Base):

       email_address = Column(UnicodeText) # For persistence using SqlAlchemy
       name          = Column(UnicodeText) # For persistence using SqlAlchemy

       @exposed
       def fields(self, fields):
           fields.name = Field(label='Name', required=True)
           fields.email_address = EmailField(label='Email', required=True)


The new |ExposedNames| is now used to create a namespace where
attributes can be defined just for Reahl:

.. code-block:: python

   class Address(Base):

       email_address = Column(UnicodeText) # For persistence using SqlAlchemy
       name          = Column(UnicodeText) # For persistence using SqlAlchemy

       fields = ExposedNames()
       fields.name = lambda i: Field(label='Name', required=True)
       fields.email_address = lambda i: EmailField(label='Email', required=True)
   

Note in the above that attributes are not just assigned an instance of |Field| though.
Instead assign a callable that will instantiate the necessary |Field| when called.

This is done to allow the use of instance-side data for |Field|\s, for example:

.. code-block:: python

   class Address(Base):

       ...

       fields = ExposedNames()
       fields.date_of_birth = lambda i: EmailField(label=f'Date {i.name} was born', required=True)

Another advantage of this new approach is that, when used for |Event|'s, the defined |Event| names
can be used as-is without an instance to declare transitions:

.. code-block:: python

   class Address(Base):

       events = ExposedNames()
       events.save = lambda i: Event(label='Save', action=Action(i.save))

   ...

   class AddressBookUI(UserInterface):
       def assemble(self):
           home = self.define_view('/', title='Address book', page=AddressBookPage.factory())
           self.define_transition(Address.events.save, home, home)


       
Performance-related changes
---------------------------

Reahl is a very high level web framework and as such does a lot of
work under the covers. This release focused on improving performance---
an aspect which previously took a back seat.

Performance varies depending on what action is performed, the size of
a page and the number of Input Widgets on the page. 

With a default configuration, this work resulted in a performance
increase of roughly 50% given our test used for profiling. Setting
`reahlsystem.runtime_checking_enabled` to False (see below), leads to
a further 50% increase in performance---for a performance gain of 75%
all in all.

While most of this work will not be visible to a programmer, some is:

Performance settings
^^^^^^^^^^^^^^^^^^^^

In order to ensure errors are caught early and stack traces make sense
to a programmer, Reahl performs some runtime checks. These can be
switched off in production for a further performance increase.

To switch runtime checks off, set
`reahlsystem.runtime_checking_enabled = False` in `reahl.config.py`.

Deprecated API of |ExecutionContext|
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The |ExecutionContext| always used to be implemented by traversing the
stack whenever |get_context| is invoked.  In order to make this more
performant, this implementation is being phased out in favour of an
implementation based on contextvars.

Since contextvars are not available in all versions of Python, the
default implementation of |ExecutionContext| is still the old
stack-traversing algorithm. Switch it to the new contextvars
implementation by setting `reahlsystem.use_context_var_for_context =
True` in `reahl.config.py`. (With the next major release, this will be
the default.)

This setting will, however, be ignored with a warning in cases where
your version of Python does not include contextvars (or the optional
contextvars package is not available).

The result of this change though is that the |install| API of
|ExecutionContext| is now deprecated.  Instead of writing:

 .. code-block:: Python

    context = ExecutionContext() context.install() ...
    
You should now write:

 .. code-block:: Python

    with ExecutionContext() as context: ...
    

Translating (i18n) of config settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In previous releases, the names of actual individual config settings
could be translated into different languages.

During profiling, it was discovered that this feature came with
significant performance cost. Because it is also not really used it
was dropped in this release.

We argued that dropping this feature does not impact any code, hence
it was accepted in this (minor) release.



General UI related changes
--------------------------
 * Added Event.with_returned_argument to allow dynamically supplying argument values to an Event (#371). examples/howtos/eventresult/

 * Added left_aligned kwarg to NavbarLayout.add.
 * Added space_before and space_after to InlineFormLayout.add_input.
 * Added placeholder to PasswordInput.
       :keyword placeholder: If given a string, placeholder is displayed in the TextInput if the TextInput
                     is empty in order to provide a hint to the user of what may be entered into the TextInput.
                     If given True instead of a string, the label of the TextInput is used.
 * Added size to SelectInput (#362)
 * Changed placeholder to display the default of the field under certain conditions (#363).
   

Ajax
----
 * Changed ChoiceField to be able to delay fetching the list of Choices (#369).
 * Added set_refresh_widgets to allow refreshing multiple widgets (#375).

   
Reahl-component
 * Made create_args for sqlalchemy configurable (#232).
   
Reahl-dev/webdev
 * Read and configure test dependencies from fixture (#237).
   
Bug fixes
---------
 * Listing examples bug fix (#354).
 * Fixed incorrect handling of timeouts (#383).
 * Changed DateField to correctly use dayfirst based on the current locale (#194). (onthou default when not inputted is now '', not today)
 * Fixed in-memory tables for sqlite (#366).

General
-------
 * Replaced usage of pkg_resources.resource_filename with importlib.resources.files (#390).


Deprecated functionality
------------------------
- field.bind will break in future if already bound
- ExposedNames changes
  

Updated dependencies
--------------------

Some dependencies on thirdparty python packages have been loosened to include a higher max version:
- setuptools should now be 51.0.0 or higher
- babel should now be between 2.1 and 2.11






   

   

 

  
  
