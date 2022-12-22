.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Migration| replace:: :class:`~reahl.component.migration.Migration`
.. |ExecutionContext| replace:: :class:`~reahl.component.context.ExecutionContext`
.. |Configuration| replace:: :class:`~reahl.component.config.Configuration`
.. |StoredConfiguration| replace:: :class:`~reahl.component.config.StoredConfiguration`
.. |configure| replace:: :meth:`~reahl.component.config.StoredConfiguration.configure`
.. |AccessRestricted| replace:: :class:`~reahl.component.exceptions.AccessRestricted`
.. |Action| replace:: :class:`~reahl.component.modelinterface.Action`
.. |add_validation_constraint| replace:: :meth:`~reahl.component.modelinterface.Field.add_validation_constraint`
.. |as_input| replace:: :meth:`~reahl.component.modelinterface.Field.as_input`
.. |Event| replace:: :class:`~reahl.component.modelinterface.Event`
.. |ExposedNames| replace:: :class:`~reahl.component.modelinterface.ExposedNames`
.. |secured| replace:: :class:`~reahl.component.modelinterface.secured`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |FieldIndex| replace:: :class:`~reahl.component.modelinterface.FieldIndex`
.. |fire| replace:: :meth:`~reahl.component.modelinterface.Event.fire`
.. |from_input| replace:: :meth:`~reahl.component.modelinterface.Field.from_input`
.. |parse_input| replace:: :meth:`~reahl.component.modelinterface.Field.parse_input`
.. |readable| replace:: :meth:`~reahl.component.modelinterface.Action.readable`
.. |writable| replace:: :meth:`~reahl.component.modelinterface.Action.writable`
.. |SqlAlchemyControl| replace:: :class:`~reahl.sqlalchemysupport.sqlalchemysupport.SqlAlchemyControl`
.. |unparse_input| replace:: :meth:`~reahl.component.modelinterface.Field.unparse_input`
.. |validate_input| replace:: :meth:`~reahl.component.modelinterface.ValidationConstraint.validate_input`
.. |validate_parsed_value| replace:: :meth:`~reahl.component.modelinterface.ValidationConstraint.validate_parsed_value`
.. |ValidationConstraint| replace:: :class:`~reahl.component.modelinterface.ValidationConstraint`

.. _toml format: https://toml.io/en/
.. _table: https://toml.io/en/v1.0.0#table

                                    
Component framework (reahl-component)
=====================================

The Reahl component framework extends setuptools distribution packages to package and distribute more than just code.

.. seealso::

   :doc:`The API documentation <index>`.

Why this?
---------

Pip and PyPI do a good job of enabling the distribution of Python code. The projects ensure that when you install a
package you get all its correct dependencies as well.

When your code contains classes mapped by an ORM (such as SqlAlchemy) to tables in a database, things become more
complicated:

The selection of packages used together in the same database cannot be foreseen by individual package authors.

- How do you create a database schema sufficient for all the database-aware packages you have decided to use together
  in your project?
- What happens if a new version of a package requires a different database schema to a previous version?
- How do you migrate the schema of an existing database to the new schema? This, in the context of there being several
  packages mixed into a single database - with possible foreign key constraints forming dependencies between packages on
  the database level.

The Reahl component framework is an attempt to build such distributable packages that are database-aware. It solves
all the surprisingly difficult accompanying problems. It calls such packages "components".

Components are not only database-aware. Similar problems are solved for components that include:

- its own configuration, which will be read from a separate file.
- its own natural language translations to support multiple languages (i18n).
- annotations of the data and features of its domain objects which can be used by, for example,
  a web framework, to manipulate such objects.
- housekeeping code that needs to be invoked regularly.

.. note::

   In the text below, links are provided to more detail for some topics. These links refer to the Reahl web framework
   tutorial which discusses these topics in more detail --- albeit in the context of the Reahl web framework. Note that
   `reahl-component` functionality is independent of the Reahl web framework.

.. _define_component:
   
Defining a component
--------------------

.. seealso::

  :ref:`The 'hello' component <create-component>`
     How to create a basic component using a `setup.cfg` file.

  :doc:`setup.cfg`
     Reference documentation for a `setup.cfg` file.

A Reahl component is just a setuptools package with extra metadata. To make your project a component,
add a `component =` key to the `[options]` section of your `setup.cfg`. The contents of this key is
explained a bit more in the next section.

In order to help setuptools grok the `component =` option you also need to have a `pyproject.toml` file
which lists `setuptools`, `toml`, and `reahl-component-metadata` as build dependencies.

Finally, your package itself needs to require `reahl-component` using `install_requires` as usual.


Basics of the component option
------------------------------

The component option expects to receive data in `toml format`_. For this to work in a `setup.cfg`, the contents
of the component option need to be after a dangling = and indented:

.. code-block:: ini

   [options]
   component =
     # contents come here, but this comment can be omitted


Each time you change `setup.cfg`, be sure to regenerate the component metadata:

.. code-block:: bash

   python -m pip install --no-deps -e .



Reahl command line
------------------

The Reahl command line is installed when you install `reahl-component` and is invoked with the command `reahl`. The set
of commands it offers depends on other Reahl components you install.

To see the available commands, run::

  reahl help-commands

  
Below is a list of which commands some components add:

`reahl-dev`
  Commands to work with components in development. This includes commands like `extractmessages` used in development
  for internationalisation (i18n). 

`reahl-commands`
  Commands for working with the extra functionality provided by Reahl components in production. This includes managing databases, schemas
  and performing migrations as well as dealing with things like internationalisation and configuration.

`reahl-workstation`
  When using :doc:`the Reahl development Docker image <../devmanual/devenv>` install `reahl-workstation` on your
  host machine to provide commands to share terminal access via `Ngrok <https://ngrok.com>`_ or GUI windows with
  `Xpra <https://xpra.org>`_.

`reahl-webdev`
  Helpful commands, such as `serve` (which runs a development webserver) when doing web development using the Reahl web framework (`reahl-web`).

`reahl-doc`
  Commands for working with examples included in the overall Reahl documentation.


   
Persistence
-----------

Persistence basics
~~~~~~~~~~~~~~~~~~

.. seealso::

  :doc:`../tutorial/persistence`
     How to register persisted classes with your component and use the command line to create a database schema.

The `reahl-component` infrastructure is extended by other Reahl components to be able to deal with differing
implementations of ORM or database systems.

To use a particular database, include in your component's dependencies the support package matching the database you
want to use:

- `reahl-postgresqlsupport`
- `reahl-mysqlsupport`
- `reahl-sqlitesupport`

Set the reahlsystem.connection_uri in `reahlsystem.config.py` to an URI matching your database
`as specified by SQLAlchemy <https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls>`_.

List the database support component, `reahl-sqlalchemysupport` and `reahl-component` as dependencies of your component.

List each persisted class of your component in the `setup.cfg`\'s component option, as an element in :ref:`the "persisted" key <setup_cfg_persisted>`.

You can now use the following commands (amongst others) from `reahl-commands` to manage the database::

    reahl createdbuser <config_directory>
    reahl createdb <config_directory>
    reahl createdbtables <config_directory>

Database migration
~~~~~~~~~~~~~~~~~~

.. seealso::

  :doc:`../tutorial/schemaevolution`
     How to write migrations, define new versions of a Reahl component and upgrade a database to the new version.

The author of one component has no knowledge of other components which might inhabit the same database when used
together. However, when component A depends on component B, the author of A will know that B is being used. The classes
of A can be written such that they result in foreign keys to tables created by component B.

This creates a dependency on the database level with some implications:

1. When creating database tables, the tables of component B have to be created before those of A to ensure A's foreign
   key constraints will not be violated.
2. When changing the schema for B, the foreign key constraints of A (to B) first have to be removed before changes are
   made to the schema of B. Then the foreign key constraints of A can be reinstated possibly referring to renamed
   tables or columns in B.

If B's author brings out a new version of B in which tables or column names have changed as in (2) above, version 2 of
B will contain a |Migration| which takes care of changing B's schema from the old version.

If A's author wants to bring out a new version of A that uses B v2, A's author needs to write a |Migration| as part of
A v2 which adjusts the old A v1 foreign key constraints to be compatible with the changes in B v2.

In a real world project, there could be a large number of such components by diverse authors. In order to migrate
the whole database from one version to another, Reahl computes a dependency graph that spans all the versions of all
the components in play. It then runs different parts of each |Migration| in the correct order to ensure all database
level dependencies and constraints are honoured.

Each version of your Reahl component can have its own set of |Migration|\s which are performed when upgrading to that
version from its predecessor. The migration machinery needs access to all |Migration|\s of all versions of all
components to be able to compute a correct dependency tree.

Add a `table`_ for each minor release of your component :ref:`in the 'setup.cfg' component option <setup_cfg_install_requires>`.

For each such version entry, add two entries:

 - :ref:`"install_requires" <setup_cfg_install_requires>`: a list of the requirements that version had; and
 - :ref:`"migrations" <setup_cfg_migrations>`: a list of the migration classes that need to run to bring the previous version's schema up to date to this version.

To prevent duplication, the version `table`_ matching the current version
should not contain any requirements, since those are already in
the standard `install_requires` of `setup.cfg`.

If the current version does not have any migrations, it need not be
listed at all.
   
.. note::

   A change in dependency or in database schema is seen as at least a minor version change, therefore
   versions listed only specify major.minor version numbers, not an additional patch version.

Each |Migration| is written such that user code does not execute changes directly, but schedules each necessary change to be done
during a specified 'phase' of migration. The final order in which the |Migration| itself and each individual phase of the |Migration| will be executed
is determined by Reahl at runtime taking all components into account.

If you schedule more than one action in a single phase in your |Migration|, these actions will retain their order
relative to one another.

The following useful commands from `reahl-commands` related to migration are available::

    reahl migratedbdb <config_directory>
    reahl diffdb <config_directory>
    reahl listversionhistory <config_directory>
    reahl listdependencies <config_directory>

Execution context
-----------------

Some Reahl code is dependent upon there being an |ExecutionContext| which can be obtained at any point in the code, and
hosts information such as the global configuration or current locale.

In other systems, you may be familiar with using `thread-local storage <https://en.wikipedia.org/wiki/Thread-local_storage>`_
for this purpose. Reahl's |ExecutionContext| is not local to a thread, it is local to a call stack.

To execute code that needs an |ExecutionContext|, use the |ExecutionContext| in a *with statement*.
The |ExecutionContext| is then available to any code inside the *with statement* block.

.. code-block:: python

    class Example:
        def do_something(self):
            self.do_something_else()

        def do_something_else(self):
            print(ExecutionContext.get_context().interface_locale)

    try:
        Example().do_something()   # Breaks, because there's no ExecutionContext
    except:
        pass
        
    with ExecutionContext():
        Example().do_something()       # Prints en_gb by default




Configuration
-------------

When building a system using Reahl components, your system includes other components via its dependencies. These
dependencies can in turn depend on other Reahl components, and so on.

The author of each individual component knows whether their component needs configuration and what config it needs. Your
final system, via dependencies, ends up consisting of a set of components by various authors. How does one configure the
final system, and how does each author specify the configuration of their component without knowledge of this final
composed system?

Configuration basics
~~~~~~~~~~~~~~~~~~~~

.. seealso::

  :doc:`../tutorial/owncomponent`
     How to define and use configuration for your own component.

A Reahl system has a single config directory with a config file for each component in the system.

You specify a unique key for the config of your component, as well as what config settings you need and the
configuration file name to be used for your component:

Inherit a new class from |Configuration|. In the `component` option of your `setup.cfg` register this class by adding
:ref:`a "configuration" entry <setup_cfg_configuration>` for this class.

When defining config settings, you can specify default values for these settings, and also a human readable description
of each setting. You can mark some config settings as "dangerous defaults": such defaults will produce warnings when
reading a configuration if they are not explicitly set in a config file. Defaults are usually chosen for a development
environment, marking a default as dangerous is a way to prevent that default value from reaching a production
environment.

.. note:: Use an ExecutionContext

   Store your |Configuration| on an |ExecutionContext| to make it accessible anywhere in your code:

   .. code-block:: python

      config = StoredConfiguration('/my/directory')
      config.configure()
      with ExecutionContext() as context:
         context.config = config

         ...

         ExecutionContext.get_context().config  # To get it anywhere

In your system, read the config by creating a |StoredConfiguration|, and then calling |configure| on it. Pass
True to `strict_checking` in production environments in order to turn dangerous defaults into errors instead of
warnings.


Dependency injection between components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. seealso::

  :ref:`dependency injection <dependency_injection>`
     How reahl-web-declarative supplies a specific implementation to reahl-web using dependency injection.

Sometimes it is useful to make one component (A) outsource some of its functionality to an as yet unknown component
by requiring classes it can use as config settings. If component B depends on A, it can then automatically provide
the relevant config settings to A.

This is a form of dependency injection which `reahl-component` uses to, for example, allow the use of different ORMs:
`reahl-component` has a config setting `reahlsystem.orm_control` which it uses to do various tasks related to database
management. If your project also depends on `reahl-sqlalchemysupport`, the latter will automatically configure
`reahlsystem.orm_control` to be a |SqlAlchemyControl|.

Commands
~~~~~~~~

The following useful commands from `reahl-commands` related to configuration are available::

    reahl listconfig <config_directory>
    reahl listconfig --values <config_directory>
    reahl listconfig --files <config_directory>
    reahl listconfig --info <config_directory>
    reahl listconfig --missing <config_directory>
    reahl checkconfig <config_directory>


Internationalisation
--------------------

.. seealso::

  :doc:`../tutorial/i18n`
     How to make strings in your application translatable and work with translations in other languages.

If a component needs a user interface in several different human languages, each string that could appear on its
user interface is marked in such a way that tools can collect all such strings in one file. (These translatable
strings are usually referred to as "messages".) For each additional language you need to support, you then provide a
version of this file with translations for each such message to that language.

Reahl-component provides a mechanism for each component to ship the translations of its messages. One component can
also provide extra translations for another component.

Before you can use the Reahl command line commands for working with messages, create an empty python package in which
messages and their translations can be saved. Once created, register this translations package
in `setup.cfg` as :ref:`an entry point in the "reahl.translations" group <setup_cfg_translations>`.


Setting the current locale
~~~~~~~~~~~~~~~~~~~~~~~~~~
Python has its own ways to set and determine what the current locale should be. Reahl code is used in server settings,
however, which means that the locale used is probably different for each user regardless of the server the code is
running on.

For this reason, a different mechanism is used to determine the current locale: supply an object to represent
a 'user session' containing options related to the current user. Add a method called `get_interface_locale` on it which
returns a locale string `formatted according to RFC5646 <https://tools.ietf.org/html/rfc5646>`_.

To make the session available to code, ensure it runs within an |ExecutionContext| on which you have set the session:

.. code-block:: python

    class UserSession:
        def __init__(self, locale):
            self.locale = locale
        def get_interface_locale(self):
            return self.locale

    ExecutionContext() as context:
        context.session = UserSession('en_gb')

.. note::
   If you set the locale to a language for which you have not supplied translations, messages will just be displayed
   using 'en_gb' - the default.

Commands
~~~~~~~~

The following useful commands from `reahl-dev` related to translations are available::

    reahl extractmessages
    reahl addlocale
    reahl mergetranslations
    reahl compiletranslations

.. note::
   Remember to `python -m pip install --no-deps -e .` after having changed `setup.cfg` before using these commands.
    
Describing the interface of your model
--------------------------------------

When a system has a user interface, the values that a user enters require a lot of management:

Marshalling
  Users can only type text, but perhaps a program would rather deal with that text as an instance of a
  specific class, such as a Date or boolean. "Marshalling" in this context refers to changing a given text
  representation into an object instance, and vice versa.

Validation
  User input also needs to be validated to ensure that, for example, the text representation of a date is in an
  expected format to be able to be transformed into a Date object. Alternatively, a numeric input might be expected
  to always constrained between a lower and upper bound.

Access control
  Programs sometimes need to prevent the acceptance of user input in certain situations or only allow it from certain
  users. For example, if an order is already processed, its contents should probably be read only to all users.

In an object oriented program, you might have one object representing something (like a BankAccount), but user input
to the same attribute of that object could be present on many different places in the user interface.

Reahl component's `modelinterface` provides a way for you to describe the above requirements for an attribute of such
an object in one place. Your user interface code can then be written with the knowledge that all these concerns have
been taken care of, and thus will be consistently applied wherever referenced.

Fields and FieldIndexes
~~~~~~~~~~~~~~~~~~~~~~~

.. seealso::

  :ref:`Using Fields <fields_explained>`
     How to expose |Field|\s for an object.

A |Field| describes one attribute of an object. There are different |Field| subclasses for things such as email
addresses, numbers or booleans.

The |ExposedNames| class is used to define all the |Field|\s available for user input on a particular class instance.

.. note::
   ORMs like Django ORM and SQLAlchemy use class attributes to define how database columns
   map to the attributes of an object. Reahl's |ExposedNames| mechanism is purposely different so that it can be used
   together with these tools without getting in their way.

To declare the |Field|\s that are bound to instances of a class,
assign a |ExposedNames| instance to a class attribute, ie,
`fields`. For each |Field| needed, assign a callable to an attributes
on the |ExposedNames|.  The callable will be passed a single argument:
the instance of the class it will be bound to. It should return a
Field instance.

When the class attribute is accessed on an instance of that class,
a |FieldIndex| is returned that allows access to |Field| instances
bound to the given instance.


Accessing an object via its |Field|\s
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given an object with bound |Field|\s declared via an |ExposedNames|:

.. code-block:: python

   class Order:
      fields = ExposedNames()
      fields.processed = lambda i: BooleanField(label='Processed', true_value='yes', false_value='no')

You can access |Field|\s from user interface code using the |from_input| and |as_input| methods:

.. code-block:: python

   with ExecutionContext():
       order = Order()

       order.fields.processed.from_input('yes')
       print(order.processed)                     # prints True
       order.processed = False
       print(order.fields.processed.as_input())   # prints 'no'

Invalid input raises a |ValidationConstraint| to communicate what is wrong:

.. code-block::

   order.fields.processed.from_input('invalid input')  # Raises: reahl.component.modelinterface.AllowedValuesConstraint: Processed should be one of the following: yes|no


Extending |Field|\s and validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Standard |Field| subclasses manage their validation by adding various |ValidationConstraint|\s based on keyword
parameters given upon construction.

Add additional |ValidationConstraint|\s to a |Field| using |add_validation_constraint|.

Build a |Field| to marshal an object of your own by creating your own |Field| subclass, and overriding the |parse_input|
and |unparse_input| methods.

When creating your own |ValidationConstraint|, create a subclass of |ValidationConstraint| and override the
|validate_input| and |validate_parsed_value| methods.


Access rights
~~~~~~~~~~~~~

To control access to a |Field|, pass single-argument callables to `readable` or `writable` when constructing the |Field|.
These callables will be called when the |Field| is read or written using |as_input| and |from_input| respectively, and
the |Field| instance itself is passed as the single argument.

The `readable` callable should return True to indicate that calling |as_input| is allowed. Similarly, `writable` should
return True to indicate that |from_input| may be called.

If `readabale` returns False, |as_input| merely returns the empty string. If `writable` returns False, calling
|from_input| has no effect.


Events and Actions
~~~~~~~~~~~~~~~~~~

An |Event| is a special kind of |Field| that represents an occurrence that can be triggered when a user clicks on a
button, for example.

An |Event| can optionally be linked to an |Action|.

.. code-block:: python

    class X:
       def exclaim(self): print('whoa')

       events = ExposedNames()
       events.boo = lambda i: Event(action=Action(self.exclaim))

To |fire| an |Event|, you first need to receive it as textual input:

.. code-block:: python

    with ExecutionContext():
        boo = X().events.boo
        boo.from_input(boo.as_input())
        boo.fire()

An |Event| can be parameterised, which will cause its action to be sent arguments upon firing. These arguments are
deduced from the input passed to |as_input| above, hence the need for calling |from_input| before |fire|.

This advanced topic is outside of the scope of this introductory material.

Access controlled methods
~~~~~~~~~~~~~~~~~~~~~~~~~

Methods can also be access controlled. Decorate a method with |secured|, passing it callables for `read_check` and
`write_check`. The signatures of these callables should match that of the |secured| method.

Each time a |secured| method is executed, these check callables are first executed to check whether the method is
allowed to be executed. If either of these callables return False, an |AccessRestricted| is raised. The point of
`read_check` is that user interface machinery could in theory use the `read_check` to, for example show a button, but
grey it out (ie., the user is aware of the method's existence but cannot invoke it). A False `write_check` instead
could signal to the user interface machinery to not even show the said button at all.

.. code-block:: python

    class Order:
        state = 'new'
        def is_submitted(self):
            return self.state == 'submitted'

        @secured(write_check=is_submitted)
        def authorise(self):
            ...

   >>> Order().authorise()   # raises reahl.component.exceptions.AccessRestricted because state is 'new'


Scheduled jobs
--------------

.. seealso::

  :doc:`../tutorial/jobs`
     Registering and running regular scheduled jobs.

The internals of a component may require certain housekeeping tasks to be performed regularly. A user of a system with
many such components does not want to have to know about all the jobs needed by all the components used. In order to
facilitate this, Reahl has a mechanism by which a component author can register jobs that the system runs on a regular
basis.

List each callable object that should be run as a scheduled job in :ref:`the "schedule" entry <setup_cfg_schedule>`
of the `component` option of your `setup.cfg`.

Whenever `reahl runjobs` is executed on your system's configuration directory, all the registered scheduled jobs of all
components that are used by your system are executed.

.. note::
   We could have opted to just register all scheduled jobs as entry points. However, a package contributes its entry points
   when it is merely installed. The scheduled jobs **for your application** should only be those jobs that are registered by
   components it depends on.

On a production system, ensure that this command is run regularly (say every 10 minutes) via your system's task
scheduler. It is up to the code in each such registered class method to check whether it should do any work when
invoked or whether it should wait until a future invocation. For example: a job may cleans out sessions from a database,
but only once a day around midnight despite being invoked every 10 minutes.

The only command from `reahl-commands` related to jobs is::

    reahl runjobs <configuration directory>

