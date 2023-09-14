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



What changed in version 7.0
===========================

Upgrading
---------

To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc


Final move to PEP 621
---------------------

Since version 6.0 Reahl projects are defined in a `setup.cfg` file.

In order to stay breast of changes in the Python packaging infrastructure this version
requires a project to be defined in a standard PEP 621 `pyproject.toml` file.

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

TODO

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
   

   

 

  
  
