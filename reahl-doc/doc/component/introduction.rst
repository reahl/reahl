.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.

Component framework - packaging and distributing more than just code
====================================================================

The Reahl component framework extends setuptools distribution packages to package and distribute more than just code.

Why this?
---------

Pip and PyPI do a good job of enabling the distribution of Python code. The projects ensure that when you install a
package you get all its correct dependencies as well.

When your code contains classes mapped by an ORM (such as SqlAlchemy) to tables in a database, things become more
complicated:

The selection of packages used together in the same database cannot be foreseen by individual package authors.
How do you create a database schema sufficient for all the packages you have decided to use together in your project?

What happens if a new version of a package requires a different database schema to a previous version? How
do you migrate the schema of an existing database to the new schema? This, in the context of there being several
packages mixed into a single database - with possible foreign key constraints forming dependencies between packages on
the database level.

The Reahl component framework is an attempt to build such distributable packages that are database-aware. It solves
all the surprisingly difficult accompanying problems. It calls such packages "components".

Components are not only database-aware. Similar problems are solved for components that include:

- its own configuration, which will be read from a separate file.
- its own natural language translations to support multiple languages (i18n).
- annotations of the data and features of its domain objects which can be used by, for example,
  a web framework, to manipulate such objects.

.. note:: API docs
   Please see :doc:`for the complete API <index>`.

.. note::
   In the text below, links are provided to more detail for some topics. These links refer to the Reahl web framework
   tutorial which discusses these topics in more detail - albeit in the context of the Reahl web framework. Note that
   `reahl-component` functionality is independent of the Reahl web framework.

Defining a component
--------------------

.. seealso::

  :ref:`<create-component>`
     How to create a basic component using a `.reahlproject` file.

  `<../devtools/xmlref>`
     Reference documentation for a .reahlproject file.

A Reahl component is just a setuptools package with extra metadata.

The Reahl component infrastructure will recognise any package with an
`entrypoint <https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points>`_ named 'Egg', advertised
in the group 'reahl.eggs' which points to the :class:`reahl.component.eggs.ReahlEgg` class as a Reahl component.

One can create such a package using a setup.py, but due to all the extra metadata which is encoded into what setuptools
supports, it is easier to use a .reahlproject file instead. To use a .reahlproject file, you need to install `reahl-dev`
in your development environment where you will build packages.  With `reahl-dev` installed, the `reahl` commandline tool is
extended with extra commands, some of which are:

- reahl setup <usual arguments to setup.py>
  This invokes the normal functionality provided by setup.py, but uses the your .reahlproject file as a source.
- reahl build
  This builds distribution packages as defined in your `.reahlproject` file.
- reahl shell [-g]
  This runs a shell command for one or more projects, each with a `.reahlproject` file. The `-g` option
  generates a setup.py for the duration of the shell command's execution. Hence, to run a shell command
  which expects a setup.py (such as tox), you would run, for example::
    reahl shell -g tox
  And to just generate a setup.py, you copy the generated file elsewhere::
    reahl shell -g cp setup.py setup.generated.py

Basics of .reahlproject
-----------------------

.. seealso::

  `<../devtools/xmlref>`
     Reference documentation for a .reahlproject file.

The `.reahlproject` file is XML, and contains a :ref:`\<project type="egg"\> <xml_project>` tag at its root.

In the <project> tag, there should be a :ref:`\<metadata\> <xml_metadata>` tag which specifies the name of
your project and its version.

There should also be one or more :ref:`\<version\> <xml_version>` entries for each minor version of your project,
including one that matches the major.minor part of the version specified in the metadata tag.

List all the dependencies of a particular version by adding a :ref:`\<deps purpose="run"\> <xml_deps>` inside the
appropriate <version> tag, and a :ref:`\<thirdpartyegg\> <xml_thirdpartyegg>` tag for each dependency.

Each time you change `.reahlproject`, be sure to regenerate the egg metadata:

.. code-block:: bash
   reahl develop -N

Reahl commandline
-----------------

The Reahl commandline is installed when you install `reahl-component` and is invoked with the command `reahl`. The set
of commands it offers depends on other Reahl components you install.

The commands in `reahl-commands` and `reahl-dev` pertain to the functionality of `reahl-component` as explained here.
Below is a more complete list of which commands other components add:

`reahl-dev`
  Commands to work with components defined by .reahlproject files instead of setup.py files. This includes
  the commands used in development for internationalisation (i18n).

`reahl-commands`
  Commands for working with the extra functionality provided by Reahl components. This includes managing databases,
  schemas and performing migrations as well as dealing with things like internationalisation and configuration.

`reahl-workstation`
  When using `the Reahl development Docker image <../devmanual/devenv.rst>` `reahl-workstation` is installed on the
  host machine to provide commands to help share GUI windows of terminal access via `Ngrok <https://ngrok.com>`_ or
  `Xpra <https://xpra.org>`_.

`reahl-webdev`
  Helpful commands when using web development using the Reahl web framework (`reahl-web`).

`reahl-doc`
  Commands for working with examples included in the overall Reahl documentation.


Persistence
-----------

Persistence basics
~~~~~~~~~~~~~~~~~~

The `reahl-component` infrastructure is extended by other Reahl components to be able to deal with differing
implementations of ORM or database systems.

To use a particular database, use the support package matching the database you want to use:

- `reahl-postgresqlsupport`
- `reahl-mysqlsupport`
- `reahl-sqlitesupport`

You also should use `reahl-sqlalchemysupport` which provides support for `SQLAlchemy <https://www.sqlalchemy.org/>`_
which is the only supported ORM.

Your component should list the required packages as well as `reahl-component` as its dependencies.

The <project> tag can also contain a single :ref:`\<persisted\> <xml_persisted>` tag. List each persisted class in
your component using a :ref:`\<class\> <xml_class>` tag inside the <persisted> tag.

.. seealso::

  `<../tutorial/persistence>`
     How to register persisted classes with your component and use the commandline to create a database schema.

You can now use the following commands (amongst others) from `reahl-commands` to manage the database::

    reahl createdbuser <config_directory>
    reahl createdb <config_directory>
    reahl createdbtables <config_directory>

Database migration
~~~~~~~~~~~~~~~~~~

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

.. seealso::

  `<../tutorial/schemaevolution>`
     How to write migrations, define new versions of a Reahl component and upgrade a database to the new version.

In order to facilitate this functionality, each version of a Reahl component can have its own set of |Migration|\s
which are performed when upgrading to that version from its predecessor. For this reason your
:ref:`\<project\> <xml_project>` tag contains one or more :ref:`\<version\> <xml_version>` tags. Since your project's
dependencies can differ between versions, :ref:`\<deps purpose="run"\> <xml_deps>` are specified inside each
:ref:`\<version\> <xml_version>` tag. The list of :ref:`\<version\> <xml_version>` tags in your project never changes -
it is only added to.

A change in dependency or in database schema is seen as at least a minor version change, therefore
:ref:`\<version\> <xml_version>` tags only specify major.minor version numbers, not an additional patch version.

Each |Migration| is written such that user code only schedules each necessary change in a so-called 'phase'. The final
order in which the |Migration| itself and each individual phase of the |Migration| will be executed is determined by Reahl
at runtime taking all components into account.

If you schedule more than one action in a single phase in your |Migration|, these actions will retain their order
relative to one another.

The following useful commands from `reahl-commands` related to migration are available::

    reahl migratedbdb <config_directory>
    reahl diffdb <config_directory>
    reahl listversionhistory <config_directory>
    reahl listdependencies <config_directory>

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

  `<../tutorial/owncomponent>`
     How to define and use configuration for your own component.

A Reahl system has a single config directory. Each Reahl component can have its own configuration file in that directory,
in which its own configuration settings which are set. A component author specifies a unique key for the config of a
component, as well as what config settings it needs and the configuration file name to be used. This is done by
inheriting a new class from |Configuration|. In your `.reahlproject` register this class using a
:ref:`\<configuration\> <xml_configuration>` tag inside your :ref:`\<project\> <xml_project>`.

When defining config settings, you can specify default values for these settings, and also a human readable description
of each setting. Some defaults can also be marked as "dangerous defaults": such defaults will produce warnings when
reading a configuration if they are not explicitly set in a config file. Defaults are usually chosen for a development
environment, marking a default as dangerous is a way to prevent that default from reaching a production
environment.

In your system, read the config by creating a |StoredConfiguration|, and then calling |configure| on it. Pass
True to |strict_checking| in production environments in order to turn dangerous defaults into errors instead of
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

If a component needs a user interface in several different human languages, each string that could appear on its
user interface is marked in such a way that tools can collect all such strings in one file. (These translatable
strings are usually referred to as "messages".) For each additional language you need to support, you then provide a
version of this file with translations for each such message to that language.

Reahl-component provides a mechanism for each component to ship the translations of its messages. One component can
also provide extra translations for another component.

Before you can use the Reahl commandline commands for working with messages, create an empty python package in which
messages and their translations can be saved. Once created, register this translations package
in `.reahlproject` using a :ref:`\<translations\> <xml_translations>` tag inside your :ref:`\<project\> <xml_project>`.

.. seealso::

  `<../tutorial/i18n>`
     How to make strings in your application translatable and work with translations in other languages.

The following useful commands from `reahl-dev` related to translations are available::

    reahl extractmessages
    reahl addlocale
    reahl mergetranslations
    reahl compiletranslations


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
an object on one place. Your user interface code can then be written with the knowledge that all these concerns have
been taken care of, and thus will be consistently applied wherever referenced.

Fields and FieldIndexes
~~~~~~~~~~~~~~~~~~~~~~~

A |Field| describes one attribute of an object. There are different |Field| subclasses for things such as email
addresses, numbers or booleans.

The |exposed| decorator is used to define all the |Field|\s available for user input on a particular class instance.

.. note::
   ORMs like Django ORM and SQLAlchemy famously use class attributes to define how database columns
   map to the attributes of an object. Reahl's |exposed| mechanism is purposely different so that it can be used
   together with these tools without getting in their way.

A method decorated with |exposed| is always passed a single argument, and is accessible as a property on the instance.
The argument passed is a |FieldIndex|. Describe the attributes of your object by assigning an instance of |Field| to
an attribute of |FieldIndex| using the same name as the attribute on the object.

.. seealso::

  :ref:`Using Fields <fields_explained>`
     How to use |exposed| to expose |Fields| for an object.


Accessing an object via is |exposed| |Field|\s
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given an object with exposed |Field|\s:

.. code-block:: python

   class Order:
      @exposed
      def fields(self, fields):
          fields.processed = BooleanField(label='Processed', true_value='yes', false_value='no')

You can access it from user interface code using the |from_input| and |as_input| methods:

.. code-block:: python

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
parameters given upon construction. You can add additional |ValidationConstraint|\s to a |Field| using
|add_validation_constraint|.

To build a |Field| to marshal an object of your own, create your own |Field| subclass, and override the |parse_input|
and |unparse_input| methods.

When creating your own |ValidationConstraint|, create a subclass of |ValidationConstraint| and override the
|validate_input| and |validate_parsed_input| methods.


Access rights
~~~~~~~~~~~~~

To control access to a |Field|, pass single-argument callables to |readable| or |writable| when constructing the |Field|.
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

       @exposed
       def events(self, events):
           events.boo = Event(action=Action(self.exclaim))

To |fire| an |Event|, you first need to receive it as textual input:

.. code-block:: python

    boo = X().events.boo
    boo.from_input(e.as_input())
    boo.fire()

An |Event| can be parameterised, which will cause its action to be sent arguments upon firing. These arguments are
deduced from the input passed to |as_input| above, hence the need for calling |from_input| before |fire|.

This advanced topic is outside of the scope of this introductory material.

Access controlled methods
~~~~~~~~~~~~~~~~~~~~~~~~~

Methods can also be access controlled. Decorate a method with |secured|, passing it callables for |read_check| and
|write_check|. The signatures of these callables should match that of the |secured| method.

Each time a |secured| method is executed, these check callables are first executed to check whether the method is
allowed to be executed. If either of these callables return False, an |AccessRestricted| is raised. The point of
|read_check| is that user interface machinery could in theory use the |read_check| to, for example show a button, but
grey it out (ie., the user is aware of the method's existence but cannot invoke it). A False |write_check| instead
could signal to the user interface machinery to not even show the said button at all.






scheduled jobs?