.. Copyright 2014-2023 Reahl Software Services (Pty) Ltd. All rights reserved.


What changed in version 7.0
===========================

Upgrading
---------

To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc


Licensing changes
-----------------

We're excited to announce a significant change in our project's licensing terms.
In the past, some components of Reahl were LGPL licensed and others were AGPL licensed.
In response to your feedback, we are transitioning the remaining AGPL Reahl components to the
GNU Lesser General Public License (LGPL).


Final move to PEP 621
---------------------

Since version 6.0 Reahl projects were defined in a `setup.cfg` file.

In order to stay breast of changes in the Python packaging infrastructure this version
requires a project to be defined in a standard PEP 621 `pyproject.toml` file instead.

See :doc:`component/pyproject.toml.rst`.


Migrating your setup.cfg to pyproject.toml
------------------------------------------

1. Ensure that in `[build-system]` you include in requires at least:
   - setuptools >= 68
   - toml
   - reahl-component-metadata >= 7.0.0
2. As before, use setuptools as build backend::
   build-backend = "setuptools.build_meta"
3. For everything configured in the 'component =' option, add the
   appropriate configuration as per :doc:`component/pyproject.toml.rst`.
4. Similarly, translate the rest of your setup.cfg config to pyproject.toml
   as per `the setuptools documentation <https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html>`_\.
   
   

Removal of deprecated functionality
-----------------------------------

Everything deprecated before this version is removed in version 7.0.

The major such deprecations worth mentioning are:
- The use of ExposedNames instead of the old @exposed.
- The use of ExecutionContext as context manager.
- Implementing ExecutionContext by means of Contextvars only (previously this could be configured).

 
Bug fixes
---------
 * Fixes to documentation (#403).
 * Fixed incorrect packaging of examples (#406).
 * Fixed breaking migration (#407).


Updated dependencies
--------------------

Some dependencies on thirdparty python packages have been loosened to include a higher max version:




- Babel  between 2.1 and 2.12
- wrapt between 1.11.0 and 1.15
- Pygments between 2.13 and 2.16
- tzlocal between 2.0 and 5.0
- plotly between 5.1.0 and 5.16
- docutils between 0.14 and 0.20
- alembic between 0.9.6 and 1.12
- beautifulsoup4 between 4.6 and 4.12
- watchdog between 0.8.3 and 3.0


Some javascript dependencies were updated to newer versions:

- Jquery to 3.7.1
- js-cookie to 3.0.5
- plotlyjs to 2.26.0



   

 

  
  
