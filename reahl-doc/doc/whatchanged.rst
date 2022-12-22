.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.


.. |with_returned_argument| replace:: :meth:`~reahl.component.modelinterface.Event.with_returned_argument`
.. |Event| replace:: :class:`~reahl.component.modelinterface.Event`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |Form| replace:: :class:`~reahl.web.ui.Form`
.. |ExposedNames| replace:: :class:`~reahl.component.modelinterface.ExposedNames`
.. |exposed| replace:: :meth:`~reahl.component.modelinterface.exposed`
.. |ExecutionContext| replace:: :class:`~reahl.component.context.ExecutionContext`
.. |get_context| replace:: :meth:`~reahl.component.context.ExecutionContext.get_context`
.. |install| replace:: :meth:`~reahl.component.context.ExecutionContext.install`
.. |UrlBoundView| replace:: :class:`~reahl.web.fw.UrlBoundView`
.. |ButtonInput| replace:: :class:`~reahl.web.ui.ButtonInput`
.. |TextInput| replace:: :class:`~reahl.web.ui.TextInput`
.. |HTMLWidget| replace:: :class:`~reahl.web.ui.HTMLWidget`
.. |SelectInput| replace:: :class:`~reahl.web.ui.SelectInput`
.. |PasswordInput| replace:: :class:`~reahl.web.ui.PasswordInput`
.. |PrimitiveInput| replace:: :class:`~reahl.web.ui.PrimitiveInput`
.. |Action| replace:: :class:`~reahl.component.modelinterface.Action`
.. |Choice| replace:: :class:`~reahl.component.modelinterface.Choice`
.. |ChoiceField| replace:: :class:`~reahl.component.modelinterface.ChoiceField`
.. |NavbarLayout.add| replace:: :meth:`~reahl.web.bootstrap.navbar.NavbarLayout.add`
.. |InlineFormLayout.add_input| replace:: :meth:`~reahl.web.bootstrap.forms.InlineFormLayout.add_input`
.. |set_refresh_widgets| replace:: :meth:`~reahl.web.ui.PrimitiveInput.set_refresh_widgets`
.. |set_refresh_widget| replace:: :meth:`~reahl.web.ui.PrimitiveInput.set_refresh_widget`



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
work under the covers. This release focused on improving
performance---an aspect which previously took a back seat.

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

Several enhancements were added to ease a number of corner cases:

Dynamic |Event| argument values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:doc:`As explained in the tutorial example
<tutorial/parameterised>`, when transitioning to an |UrlBoundView|
which is parameterised, values are supplied to the |Event| to match the
arguments expected by the destination |UrlBoundview|.

Sometimes this value is not yet known at the time the |Event| is used
to render a |ButtonInput|, but becomes known as a result of executing
the |Action| of the |Event|.

In order to handle this scenario, you can now use the return value of the
|Action| as a parameter value, together with |with_returned_argument|.

:doc:`See more in the added howto. <howto/eventresult>`

Automatic display of default as placeholder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When creating a |TextInput|, you can now set `placeholder=True`
(instead of a string).

If the underlying |Field| does not have a value, and is not required,
submitting the |Form| results in setting that |Field| to its specified
`default`. With `placeholder=True`, that default is now displayed as a
placeholder to show the user what will be submitted.

If the |Field| is required, though, the user is forced to enter a
value, and hence a default does not make sense. In this case, the
label of the |Field| is displayed as placeholder.


Delaying the list of choices of a |ChoiceField|
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some cases (such as when one |PrimitiveInput| refreshes a |SelectInput| and
expects the different choices after a refresh, the list of |Choice|\s
of the |SelectInput| cannot be statically pinned down at the time the
|ChoiceField| is created. In this case you can now pass a no-arg
callable for `grouped_choices`. This callable is then called only
later on to compute the list of |Choice|\s.


UI enhancements
^^^^^^^^^^^^^^^

* The `left_aligned` keyword argument was added to |NavbarLayout.add|.
* On |InlineFormLayout.add_input| the 'space_before' and 'space_after'
  keyword arguments were added.
* The 'placeholder' keyword argument was added |PasswordInput|.
* A 'size' keyword argument was added to |SelectInput|.
* An |PrimitiveInput| can now refresh more than one |HTMLWidget| at a
  time. To facilitate this, |set_refresh_widgets| was added and
  |set_refresh_widget| was deprecated (and will be removed in a
  future version).


Other enhancements
^^^^^^^^^^^^^^^^^^

sqlalchemysupport
  A new config file `sqlalchemy.config.py` can now be created and
  supports a single setting: `sqlalchemy.engine_create_args`. This is
  a dictionary of keyword arguments passed to `SqlAlchemy's
  create_engine method
  <https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine>`_.
  
test dependencies
  Test dependencies declared on Fixtures are now taken into account
  when running tests. This means their config is read and injections
  are done correctly when testing.

 
Bug fixes
---------
 * Listing and checking out of examples did not work correctly (#354).
 * Fixed incorrect handling of timeouts (#383).
 * Changed DateField to correctly use dayfirst based on the current locale. The default is now an empty string instead of the current date. (#194)
 * Fixed in-memory tables that were not created on the fly when using sqlite (#366).



Updated dependencies
--------------------

Some dependencies on thirdparty python packages have been loosened to include a higher max version:

- babel  between 2.1 and 2.11
- Pillow between 2.5 and 3.9
- alembic between 0.9.6 and 1.8
- beautifulsoup4 between 4.6 and 4.11
- docutils between 0.14 and 0.19
- lxml between 4.2 and 4.9
- plotly between 5.1.0 and 5.11
- prompt_toolkit between 2.0.10 and 3.0
- selenium between 2.42 and 4.7
- tzlocal between 2.0 and 4.2
- watchdog between 0.8.3 and 2.2
- wrapt between 1.11.0 and 1.14
- setuptools should now be 51.0.0 or higher

The dependency on plotly has been upped to version 5.11.0.

The dependency on pip has been upped to minimum version 21.1 in order to work correctly for projects using pyproject.toml.

Some javascript dependencies were updated to newer versions:

- Jquery to 3.6.1
- Jquery-ui to 1.13.2
- jquery-validate to 1.19.5
- js-cookie to 3.0.1
- bootstrap to 4.6.2
- underscore to 1.13.6
- plotlyjs to 2.16.4
   

   

 

  
  
