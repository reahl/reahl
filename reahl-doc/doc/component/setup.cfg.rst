.. Copyright 2022 Reahl Software Services (Pty) Ltd. All rights reserved.

.. _entry point object reference: https://packaging.python.org/en/latest/specifications/entry-points/#data-model
.. _table: https://toml.io/en/v1.0.0#table
.. _toml format: https://toml.io/en/
.. |Migration| replace:: :class:`~reahl.component.migration.Migration`
.. |Configuration| replace:: :class:`~reahl.component.config.Configuration`
.. |DatabaseControl| replace:: :class:`~reahl.component.dbutils.DatabaseControl`
.. |Command| replace:: :class:`~reahl.component.shelltools.Command`



Configuring your component via setup.cfg
========================================


Some features of a component are configured using standard
configuration in setup.cfg, others are added in the 'component' option
of setup.cfg.


The component option
--------------------

To indicate that a package is a component, add a component option to setup.cfg. The
contents of that option is indented text in `toml format`_\.
The simplest component just needs an empty setting:

.. code-block:: ini
                
   [options]
   component =

.. note::
   Remember to include `setuptools` and `reahl-component-metadata` as build dependencies in your pyproject.toml
   in order for this to work.

.. warning::
   The `toml format`_ used here looks superficially like ini file format which is used by the rest of this file, but it is not the same!

.. _setup_cfg_persisted:

persisted
^^^^^^^^^

List any classes that own a part of a database schema in the "persisted" list. Each item in this
list is a string, in the format of an `entry point object reference`_\:

.. code-block:: ini
                
   [options]
   component =
     persisted = [
       "my.one.package:PersistedClass1",
       "my.other.package:PersistedClass2"
     ]


.. _setup_cfg_versions:
     
versions
^^^^^^^^

Add a `[versions."major.minor"]` `table`_ for each minor version that has been released of your package:

The current version (1.3 in the example below) is not included in this list **except** if it needs :ref:`migrations <setup_cfg_migrations>`.

.. code-block:: ini

   [metadata]
   
   version = 1.3.4
   
   [options]
   
   component =
     [versions."1.2"]
     [versions."1.0"]


.. _setup_cfg_install_requires:

install_requires
""""""""""""""""

Each version may have an "install_requires" list, which lists all other components it requires. For the current
version, this information is automatically read from the usual `install_requires` option, which is why the current
version need not be listed.

.. code-block:: ini

   [metadata]

   version = 1.3.4

   
   [options]
   
   install_requires =
     reahl-component>=6.0,<6.1
     
   component =
     [versions."1.2"]
     install_requires = [
       "reahl-component>=1.2,<1.3"
     ]
     
     [versions."1.0"]
     install_requires = [
       "reahl-component>=0.8,<1.9"
     ]


.. note::

   Only requirements that are themselves components should be listed here. Other packages that are not themselves components can be omitted even
   if that version used to depend on them. 
   
   Components should be versioned using semantic versioning, hence these requirements should always be specified
   with a min (included) and max (excluded) version:  acomponent>=3.0,<3.1. A requirement does not have to be tied to one minor
   version though, it can span multiple: acomponent>=3.0,<6.1

   You should not use version 0.0 - it is assumed the database schema is always empty for this version.
   

     
.. _setup_cfg_migrations:

migrations
""""""""""

Each version may also have a "migrations" list: a list of all the migration classes (each a string formatted as an `entry point object
reference`_) to run in order to bring the previous version of the database schema of your component up to date with the listed version.

.. code-block:: ini

   [metadata]

   version = 1.3.4

   
   [options]
   
   install_requires =
     reahl-component>=6.0,<6.1
     
   component =
     [versions."1.2"]
     install_requires = [
       "reahl-component>=1.2,<1.3"
     ]
     migrations = [
       "my.one.package:MigrateC",
       "my.other.package:MigrateB"
     ]
     
     [versions."1.0"]
     install_requires = [
       "reahl-component>=0.8,<1.9"
     ]
     
     migrations = [
       "my.one.package:MigrateA"
     ]



If the current version of your component has a |Migration|, then it should also be included in the versions listed, but only its migrations
should then be specified, no "install_requires":

.. code-block:: ini
                
   [metadata]

   version = 1.3.4

   
   [options]
   
   install_requires =
     reahl-component>=6.0,<6.1
     
   component =
     [versions."1.3"]
     migrations = [
       "my.one.package:MigrateD"
     ]
     
     [versions."1.2"]
     install_requires = [
       "reahl-component>=1.2,<1.3"
     ]
     migrations = [
       "my.one.package:MigrateC",
       "my.other.package:MigrateB"
     ]
     
     [versions."1.0"]
     install_requires = [
       "reahl-component>=0.8,<1.9"
     ]
     
     migrations = [
       "my.one.package:MigrateA"
     ]


     
.. _setup_cfg_configuration:
     
configuration
^^^^^^^^^^^^^

If your project contains its own |Configuration|, specify it as the "configuration" key. Its value is a string using
the `entry point object reference`_ format:

.. code-block:: ini
                
   [options]
   component =
     configuration = "my.package:MyConfiguration"


.. _setup_cfg_schedule:


schedule
^^^^^^^^

List each callable object that is to be run periodically as a scheduled job in the "schedule" list. This is a list
of such objects represented as strings, each formatted as an `entry point object reference`_:

.. code-block:: ini
                
   [options]
   component =
     schedule = [
       "my.package:my_function",
       "my.package:MyClass.a_class_method"
     ]


Entry points
------------

Some component functionality is merely configured as normal entry points. This means that they will be picked up
by any component once a component advertising them is installed.


.. _setup_cfg_translations:

reahl.translations
^^^^^^^^^^^^^^^^^^

To ship translations for your component, add a package where these messages are to be stored inside your component.
Register this package in the "reahl.translations" group and give it the name of your component.

Be sure to also add an entry for including the compiled messages as package data.

.. code-block:: ini
                
   [options]
   
   name = mycomponent

   
   [options.entry_points]
     reahl.translations = 
       mycomponent = mymessages


   [options.package_data]
     * = 
       */LC_MESSAGES/*.mo


.. _setup_cfg_commands:

reahl.component.commands
^^^^^^^^^^^^^^^^^^^^^^^^

To add a command to the `reahl` command line tool, list your |Command|\-derived class in the "reahl.component.commands" entry point group:

.. code-block:: ini
                
   [options.entry_points]
     reahl.component.commands = 
       MyCommand = my_package.module:MyCommand




.. _setup_cfg_database_controls:

reahl.component.databasecontrols
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add additional |DatabaseControl| classes to the "reahl.component.databasecontrols" entry point group:


.. code-block:: ini
                
   [options.entry_points]
     reahl.component.databasecontrols = 
       MyNewControl = mypackage.mymodule:MyNewControl

       
