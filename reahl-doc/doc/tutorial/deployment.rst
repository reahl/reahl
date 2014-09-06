.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Deploying a production site
===========================

.. sidebar:: Examples in this section

   - tutorial.helloapache
   - tutorial.hellonginx

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

Many things influence the details of how one deploys a web application
to a production site. Some people have root access to the machine on
which the site will run, some only have ssh access to a user
account. Different people use different web servers. Different
environments also run on different operating platforms and versions of
those platforms. The list goes on...

The high level details are the same though. In short, here's what you
need to do to deploy an application:

- Package your application and distribute it to the machine where it
  is to be installed.
- Create a virtualenv for your application, and install your
  application and all its dependencies into that virtualenv.
- Provide configuration for which explicit settings are *needed* in
  production (these settings are defaulted for convenience, but their
  defaults only make sense in development).
- Set up (or migrate) the database for the application.
- Provide your application as a WSGI app to the web server.
- Configure your web server to serve the WSGI app -- both a version via
  http and one served via https.

The rest of this section elaborates on these points by walking you
through an example. The example is the simple "hello world"
application developed in :doc:`gettingstarted`, but with a few files
included for use in a production environment. The example is done in
terms of an `Apache 2.2.x web server <http://httpd.apache.org>`_,
using `mod_wsgi <https://code.google.com/p/modwsgi/>`_.


Packaging and distributing your application
-------------------------------------------

Since any Reahl project is also a Python Egg, packaging it is a matter
of building and distributing the egg. Your `.reahlproject` file
specifies all the formats you want the egg to be packaged in, and for
each such format, a list of repositories to which you'd like to
distribute it.

This example has the following in its `.reahlproject` file:

.. literalinclude:: ../../reahl/doc/examples/tutorial/helloapache/.reahlproject
   :language: xml
   :start-after: <!-- packaging -->
   :end-before: </project>

The `<distpackage type="sdist">` tag represents a package to be built
as a Python Egg source distribution. In this example, no repositories
are defined for distributing the package. Repositories would be
defined inside the `<distpackage>` tag, by listing a `<packageindex>` 
for each repository to which this package should be distributed.

.. sidebar:: debs and apt archives

   The Reahl infrastructure supports building `.deb` packages as well,
   and the uploading of these to an Apt repository. These features are
   experimental at this stage, and not well tested or documented!

A `<packageindex>` represents a PyPi-style repository. It expects a
single attribute `repository="some value"` which has exactly the same
meaning as the ``--repository`` command line argument to the
normal ``setup.py upload`` command which is normally used to upload
eggs to `PyPi <https://pypi.python.org>`_.

By default, though, all packages are put in a "local repository" when
built. This local repository is just a special directory in which all
eggs will be dumped. For our example we'll just copy the egg from
there to the target production machine.

The `reahl` script that is used during development creates a directory
for all housekeeping tasks. Normally it would create this
directory as `.reahlworkspace` in your home directory. The local
repository for eggs would then be `~/.reahlworkspace/dist-egg`.

To build your egg, issue the following command from within the
directory containing your component::

  reahl build

After issuing that, look for the tar file of your built egg in
`~/.reahlworkspace/dist-egg`. It will be named helloapache-0.0.tar.gz.


What's to be installed
----------------------

Besides your application itself (in an egg), any Reahl application will
also need the following:

- A virtualenv in which the egg and its dependencies will be installed
- A script that creates and starts your application as a WSGI app
- The configuration directory for your application, set up for a
  production environment.
- A location for static files served by the web server.

Before we can go into the details of these, it is necessary to decide
where all these files will go on the production file system. Of
course, this is up to you, and may depend on the type of access you
have to the production machine. For the purposes of this example, root
access is assumed, making the following file locations possible::

 ├── etc
 │   ├── apache
 │   │   └── sites-available
 │   │       ├── default           <-- An Apache site for http
 │   │       └── default-ssl       <-- An Apache site for https
 │   └── reahl.d                   <-- A directory where all Reahl config directories will go
 │       └── helloapache           <-- The config directory for our example site
 │           ├── reahl.config.py
 │           ├── web.config.py
 │           └── systemaccountmodel.config.py
 ├── usr
 │   └── local
 │       └── helloapache           <-- The helloapache program itself
 │           ├── helloapache.wsgi  <-- The wsgi script
 │           └── virtualenv        <-- The virtualenv for helloapache
 └── var
     └── local
         └── helloapache           <-- Data used by the helloapache program
             ├── www               <-- The "DocumentRoot" for static files for this website
             └── helloapache.db    <-- The sqlite database (if you use sqlite)



virtualenv
----------

Production environments can also be run in an isolated environment
provided by virtualenv. Doing this has some advantages:

- If you host many applications, each one in its own virtualenv, you
  will not impact other applications when upgrading one.
- You're not tied to the versions of Python packages shipped by your
  distribution.

There is also a disadvantage though: since Python packages are
installed into the virtualenv using pip, they are installed from
source. That means they have to be built -- a process which relies on
the presence of some non-Python packages. These non-Python packages
would need to be installed on the production system.

The process of preparing a virtualenv for production is the same
as that of preparing it for development, as explained in the
:doc:`gettingstarted`. Only, a virtualenv installed in
`/usr/local/helloapache` should be installed as the `root` user.

Installing helloapache in the virtualenv
----------------------------------------

Once the virtualenv has been prepared, and all necessary
non-Python packages are available in the system, you can now go ahead
and install helloapache into the virtualenv (again, do this as root).

You don't have to install Reahl explicitly. The `helloapache` egg
should have the correct dependencies declared -- which means installing
`helloapache` will also install all its dependencies.

We noted earlier that for the sake of this example you can distribute the
application by copying helloapache-0.0.tar.gz to the production
box. We're not going to flood PyPi with `helloapache` projects!

Assuming you put `helloapache-0.0.tar.gz` in /tmp, simply install it by
issuing (as root)::

  pip install /tmp/helloapache-0.0.tar.gz


The wsgi script
---------------

Reahl is meant to be served via a web server that can serve WSGI
applications. `Apache <http://httpd.apache.org>`_ can do this using
its `mod_wsgi <https://code.google.com/p/modwsgi/>`_. This module
requires one to supply a Python script which makes a WSGI application
available in its name space as the variable ``application``. Of
course, this script is also responsible for initialising said WSGI
application.

Here is the script for our planned setup for this example (you would
probably write a very similar script when deploying to a different
server):

.. literalinclude:: ../../reahl/doc/examples/tutorial/helloapache/prod/helloapache.wsgi
   :language: python

The strangest thing done by the script relates to the fact that your
application lives in a virtualenv. The first paragraph in the script
switches the current Python interpreter to the virtualenv (and, by
implication all applications and libraries installed there). Only
after having done that, can you import :class:`~reahl.web.fw.ReahlWSGIApplication` and create
an instance of it from the configuration directory for your
application. Lastly, `.start()` the application.


Production config
-----------------

According to the plan laid out above, the configuration directory is
created inside `/etc/reahl.d`. This is just convenient if you run
multiple web applications on the same machine. What is important to
take not of is the configuration settings that are needed for a
production machine.  Here they are, in the files where they belong for
our example application and our chosen setup planned above:

reahl.config.py
~~~~~~~~~~~~~~~

.. literalinclude:: ../../reahl/doc/examples/tutorial/helloapache/prod/etc/reahl.config.py

web.config.py
~~~~~~~~~~~~~

.. literalinclude:: ../../reahl/doc/examples/tutorial/helloapache/prod/etc/web.config.py

systemaccountmodel.config.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../reahl/doc/examples/tutorial/helloapache/prod/etc/systemaccountmodel.config.py


Create the database
-------------------

If you are using SQLite, the database will be saved in a file that is
directly accessed from the running application process. Since this
process is running as the `www-data` user, that file must be created
such that it is readable and writable by the `www-data` user.

The easiest way to ensure that happens is to run the database creation
commands as the `www-data` user. Remember though to also activate the
virtualenv!

Here's how you can create the database, making sure you've activated the
correct virtualenv, as the correct user:

.. code-block:: bash

   sudo su - www-data
   source /usr/local/helloapache/virtualenv/bin/activate
   reahl-control createdbuser /etc/reahl.d/helloapache 
   reahl-control createdb /etc/reahl.d/helloapache 
   reahl-control createdbtables /etc/reahl.d/helloapache 

Of course, all of this assumes you are installing a new
application. If you are just upgrading your application to a new
version, you will want to retain the existing database, but migrate it
to the new schema with:

.. code-block:: bash

   sudo su - www-data
   source /usr/local/helloapache/virtualenv/bin/activate
   reahl-control migratedb /etc/reahl.d/helloapache 


Apache config
-------------

To keep things simple, we have merely simplified the apache
configuration that is installed by default on an Ubuntu machine. You
may want to do things a bit differently. For example, to run your
application on a NamedVirtualHost. Note though, that each application
would need its own IP address when using HTTPS.

You need to set up two "websites" in Apache: one for HTTP requests,
and another for HTTPS requests. Here are the apache configuration
files for each of these:

The HTTP site
~~~~~~~~~~~~~

.. literalinclude:: ../../reahl/doc/examples/tutorial/helloapache/prod/apache/default
   :language: xml

The WSGIScriptAlias ensures that the entire site will be handled by
the WSGI application set up by the script prepared for that
purpose. The ErrorLog and CustomLog could probably also have been left
at their defaults, but it is nice to have the logs of each site
separately, so we configured them as a matter of habit.


The HTTPS site
~~~~~~~~~~~~~~

.. literalinclude:: ../../reahl/doc/examples/tutorial/helloapache/prod/apache/default-ssl
   :language: xml

The HTTPS site is configured exactly the same, except that it needs to
be told to use SSL. For the example, we're just using the self-signed
certificates already installed on an Ubuntu machine.


Let it run!
-----------

You're finally ready to start it all up. As `root`, first enable both
sites in Apache, then start Apache itself::

  sudo a2enmod default  
  sudo a2enmod default-ssl
  sudo /etc/init.d/apache start

