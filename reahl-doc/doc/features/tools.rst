.. Copyright 2013, 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Tool support
============

The `reahl` commandline script contains several useful commands.

For example, to give information about the applicable config settings
of all components used. To see which file each setting originates from
(`-f`) and a description of what the setting does (`-i`), execute the
following in your project:

.. code-block:: bash

   reahl listconfig -f -i ./etc

For :doc:`tabbed panel example<tabbedpanel>`, it gives:

.. code-block:: bash

   Listing config for ./etc/
   reahlsystem.connection_uri         	    reahl.config.py	The database connection URI
   reahlsystem.databasecontrols       	    reahl.config.py	All available DatabaseControl classes
   reahlsystem.debug                  	    reahl.config.py	Enables more verbose logging
   reahlsystem.orm_control            	    reahl.config.py	The ORM control object to be used
   reahlsystem.root_egg               	    reahl.config.py	The egg of the project
   reahlsystem.serialise_parallel_requests  reahl.config.py	Whether concurrent requests to the web application should be forcibly serialised
   web.default_http_port              	    web.config.py	The http port used when an encrypted connection is not required
   web.default_http_scheme            	    web.config.py	The http scheme used when an encrypted connection is not required
   web.encrypted_http_port            	    web.config.py	The http port used for encrypted connections.
   
   (rest of output not shown here)

The commands supported differ depending on what components you have
installed. To see what is available do::

   reahl help-commands


