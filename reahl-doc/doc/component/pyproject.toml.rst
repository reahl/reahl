.. Copyright 2022, 2023 Reahl Software Services (Pty) Ltd. All rights reserved.

.. _entry point object reference: https://packaging.python.org/en/latest/specifications/entry-points/#data-model
.. _table: https://toml.io/en/v1.0.0#table
.. _toml format: https://toml.io/en/
.. |Migration| replace:: :class:`~reahl.component.migration.Migration`
.. |Configuration| replace:: :class:`~reahl.component.config.Configuration`
.. |DatabaseControl| replace:: :class:`~reahl.component.dbutils.DatabaseControl`
.. |Command| replace:: :class:`~reahl.component.shelltools.Command`



Configuring your component via pyproject.toml
=============================================


Some features of a component are configured using a `pyproject.toml` file.


The component table
-------------------

To indicate that a project is a component, add a `[tool.reahl-component]` table to pyproject.toml.

The simplest component requires the table, but no contents:

.. code-block:: ini

   [tool.reahl-component]

.. note::
   Remember to include `setuptools` and `reahl-component-metadata >= 7.0` as a requires entry in your `[build-system]` table.


.. _pyproject_persisted:

persisted
^^^^^^^^^

List any classes that own a part of a database schema in the "persisted" key of the `[tool.reahl-component]`. Each item in this
array is a string, in the format of an `entry point object reference`_\:

.. code-block:: ini

   [tool.reahl-component]
   persisted = [
       "my.one.package:PersistedClass1",
       "my.other.package:PersistedClass2"
       ]


.. _pyproject_versions:
     
versions
^^^^^^^^

[tool.reahl-component.versions."6.1"]

Add a `[tool.reahl-component.versions."major.minor"]` `table`_ for each minor version that has been released of your package:

The current version (1.3 in the example below) is not included in this list **except** if it needs :ref:`migrations <pyproject_migrations>`.

.. code-block:: ini

   [project]
   version = "1.3.4"
   
   [tool.reahl-component.versions."1.2"]
   
   [tool.reahl-component.versions."1.0"]



.. _pyproject_dependencies:


dependencies
""""""""""""

Each version may have a 'dependencies' array, which lists all other components it requires. For the current
version, this information is automatically read from the usual `dependencies` key in standard '[project]' table, which is why the current
version need not be listed.

.. code-block:: toml

   [project]
   version = "1.3.4"
   dependencies = [
     "reahl-component>=7.0,<7.1"
     ]
     
   [tool.reahl-component.versions."1.2"]
     dependencies = [
       "reahl-component>=1.2,<1.3"
     ]
   
   [tool.reahl-component.versions."1.0"]
     dependencies = [
       "reahl-component>=0.8,<1.9"
     ]


.. note::

   Only requirements that are themselves components should be listed here. Other packages that are not themselves components can be omitted even
   if that version used to depend on them. 
   
   Components should be versioned using semantic versioning, hence these requirements should always be specified
   with a min (included) and max (excluded) version:  acomponent>=3.0,<3.1. A requirement does not have to be tied to one minor
   version though, it can span multiple: acomponent>=3.0,<6.1

   You should not use version 0.0 - it is assumed the database schema is always empty for this version.
   

     
.. _pyproject_migrations:

migrations
""""""""""

Each version may also have a "migrations" array: an array of all the migration classes (each a string formatted as an `entry point object
reference`_) to run in order to bring the previous version of the database schema of your component up to date with the listed version.

.. code-block:: ini

   [project]
   version = "1.3.4"
   dependencies = [
     "reahl-component>=7.0,<7.1"
     ]

   
   [tool.reahl-component.versions."1.2"]
     dependencies = [
       "reahl-component>=1.2,<1.3"
     ]
     migrations = [
       "my.one.package:MigrateC",
       "my.other.package:MigrateB"
     ]
     
   [tool.reahl-component.versions."1.0"]
     dependencies = [
       "reahl-component>=0.8,<1.9"
     ]
     migrations = [
       "my.one.package:MigrateA"
     ]



If the current version of your component has a |Migration|, then it should also be included in the versions listed, but only its migrations
should then be specified, no "dependencies":

.. code-block:: ini
                
   [project]
   version = "1.3.4"
   dependencies = [
     "reahl-component>=7.0,<7.1"
     ]

   
   [tool.reahl-component.versions."1.3"]
     migrations = [
       "my.one.package:MigrateD"
     ]
   [tool.reahl-component.versions."1.2"]
     dependencies = [
       "reahl-component>=1.2,<1.3"
     ]
     migrations = [
       "my.one.package:MigrateC",
       "my.other.package:MigrateB"
     ]
     
   [tool.reahl-component.versions."1.0"]
     dependencies = [
       "reahl-component>=0.8,<1.9"
     ]
     migrations = [
       "my.one.package:MigrateA"
     ]


     
.. _pyproject_configuration:
     
configuration
^^^^^^^^^^^^^

If your project contains its own |Configuration|, specify it as the "configuration" key. Its value is a string using
the `entry point object reference`_ format:

.. code-block:: ini

   [tool.reahl-component]
     configuration = "my.package:MyConfiguration"


.. _pyproject_schedule:


schedule
^^^^^^^^

List each callable object that is to be run periodically as a scheduled job in the "schedule" array. This is an array
of such objects represented as strings, each formatted as an `entry point object reference`_:

.. code-block:: ini
                
   [tool.reahl-component]
     schedule = [
       "my.package:my_function",
       "my.package:MyClass.a_class_method"
     ]


Entry points
------------

Some component functionality is merely configured as normal entry points. This means that they will be picked up
by any component once a component advertising them is installed.


.. _pyproject_translations:

reahl.translations
^^^^^^^^^^^^^^^^^^

To ship translations for your component, add a package where these messages are to be stored inside your component.
Register this package in the "reahl.translations" group and give it the name of your component.

.. code-block:: ini
                
   [project]
     name = "mycomponent"

   
   [project.entry-points."reahl.translations"]
     mycomponent = "mymessages"


.. warning:: Be sure to follow `the setuptools guidelines for including your compiled messages files as package data <https://setuptools.pypa.io/en/latest/userguide/datafiles.html>`_ as well.
             


.. _pyproject_commands:

reahl.component.commands
^^^^^^^^^^^^^^^^^^^^^^^^

To add a command to the `reahl` command line tool, list your |Command|\-derived class in the "reahl.component.commands" entry point group:

.. code-block:: ini
                
   [project.entry-points."reahl.component.commands"]
     MyCommand = "my_package.module:MyCommand"




.. _pyproject_database_controls:

reahl.component.databasecontrols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add additional |DatabaseControl| classes to the "reahl.component.databasecontrols" entry point group:


.. code-block:: ini
                
   [project.entry-points."reahl.component.databasecontrols"]
     MyNewControl = "mypackage.mymodule:MyNewControl"

       
