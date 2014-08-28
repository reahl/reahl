.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Tool support
============

Two command line tools are included with Reahl: `reahl-control` and
`reahl`. The `reahl-control` script is available in production
environments as well as in development environments; `reahl` is only
used in development. These tools are extensible -- you could add a
component that includes new commands that would automatically be added
to one of the command line tools.

One example of the use of the command line tools has to do with
configuration settings. Reahl has a system of configuration that
allows the programmer of each individual component to specify just the
configuration needed for that specific component. This means that a
running application (which consists of many components), needs a
configuration directory containing a configuration file for each
component used by the application. Without tool support it would be
cumbersome for a system administrator in this scenario to find out
what config is needed, and in what file each setting goes.

All commands implemented by `reahl-control` operate on an
application, given its configuration directory.

In order to manage configuration, the `listconfig` command can show
which config settings are in use, which are defaulted, in which file
each one should go, what each setting is for, etc.  For example, the
command:

.. code-block:: bash

   reahl-control listconfig -f -i ./reahl/doc/examples/features/widgets/etc 

would respond with a listing of each configuration setting used by the
application configured in ``./reahl/doc/examples/features/widgets/etc`` (the
:doc:`tabbed panel example<tabbedpanel>`). 

For each configuration setting the tool will list which file it whould
be configured in (`-f`), and give information about what the setting is for
(`-i`).  (Note that not all configuration files need to be present in
that directory, most configuration settings have sensible defaults
set.)

.. code-block:: bash

   Listing config for ./reahl/doc/examples/features/widgets/etc/
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

To see what is offered by `reahl-control`, issue::

   reahl-control -h
