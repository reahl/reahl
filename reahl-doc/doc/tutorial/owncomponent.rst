.. Copyright 2013, 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.


.. |Migration| replace:: :class:`~reahl.component.migration.Migration`
.. |Configuration| replace:: :class:`~reahl.component.config.Configuration`
.. |ConfigSetting| replace:: :class:`~reahl.component.config.ConfigSetting`
.. |ExecutionContext| replace:: :class:`~reahl.component.context.ExecutionContext`


Defining custom configuration
=============================

.. sidebar:: Examples in this section

   - tutorial.componentconfigbootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

Any code you write using Reahl :ref:`is packaged as a component even your
web application itself <create-component>`.

Each Reahl component used by an application can have its own
configuration file located in a common configuration directory.

The `tutorial.componentconfigbootstrap` example shows how to make a
component read configuration from such a file. The example uses its
own config setting (`componentconfig.showheader`) to control whether
AddressBookPanel has a heading or not.

The |Configuration| for the system is available anywhere in your code
as :attr:`~reahl.component.context.ExecutionContext.config` of the
current |ExecutionContext|:

.. literalinclude:: ../../reahl/doc/examples/tutorial/componentconfigbootstrap/componentconfigbootstrap.py
   :pyobject: AddressBookPanel

AddressConfig (which inherits from |Configuration|) defines the
available configuration settings and associated information. Declare
each config setting by assigning an instance of |ConfigSetting| to a
class attribute of AddressConfig with the name you want:

.. literalinclude:: ../../reahl/doc/examples/tutorial/componentconfigbootstrap/componentconfigbootstrap.py
   :pyobject: AddressConfig

.. note::

   It is good practice to always provide a default value for a
   setting. If all your settings have sensible defaults, your application
   can be started up and run without any config file present at
   all--something a new user will appreciate. Similarly, the description
   is used to enable useful output when you run, for example:

   .. code-block:: bash

      reahl listconfig -i etc/

In the `setup.cfg` file, AddressConfig is added :ref:`as the "configuration" of the component <setup_cfg_configuration>`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/componentconfigbootstrap/setup.cfg
   :start-after:   component = 
   :end-before:    persisted = 
   :prepend:       component = 

Config files contain Python code. In `componentconfig.config.py` (the
:attr:`~reahl.component.config.Configuration.filename`) an
instance of AddressConfig is available as `componentconfig` (the
:attr:`~reahl.component.config.Configuration.config_key`):

.. literalinclude:: ../../reahl/doc/examples/tutorial/componentconfigbootstrap/etc/componentconfig.config.py



