.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Input| replace:: :class:`~reahl.web.ui.Input`
.. |get_concurrency_hash_strings| replace:: :meth:`~reahl.web.fw.Widget.get_concurrency_hash_strings`



Production deployment on nginx
==============================

.. sidebar:: Examples in this section

   - howtos.hellonginx

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Preparation
-----------

Check out the example on your development machine.

In the checked-out `setup.cfg`, make sure you include all the necessary dependencies. Besides things like
`reahl-web-declarative`, also provide a dependency for Reahl's support of the DB you use, eg `reahl-sqlitesupport`
for SQLite.

Still on your development machine, build your project (as is done in :ref:`PythonAnywhere tutorial example <build>`).
Copy the resultant whl file from ./dist in your dev environment to the production machine in a new directory /tmp/dist.


Installation
------------

.. note:: The package names here are taken from an Ubuntu distribution, they may be different on others.

Ensure you have python3, nginx, ssl-cert, uwsgi and uwsgi-plugin-python3 installed on the prod machine. You also need
to install your database, or, if your database runs on a different host, install the client libraries to access it.
These are:

+----------+-----------------------------------------+
| DB       | Libraries required                      |
+==========+=========================================+
| MYSQL    | default-libmysqlclient-dev mysql-client |
+----------+-----------------------------------------+
| POSTGRES | postgresql-client                       |
+----------+-----------------------------------------+
| SQLITE   | sqlite3 libsqlite3-0                    |
+----------+-----------------------------------------+


On the production machine, create a venv as root and install your application:

.. code-block:: bash

    sudo -i
    mkdir -p /usr/local/hellonginx
    python3 -m venv /usr/local/hellonginx/venv/
    source /usr/local/hellonginx/venv/bin/activate
    python3 -m pip install wheel
    python3 -m pip install --find-links /tmp/dist hellonginx      # Note /tmp/dist is where you copied the whl of your app earlier

Create a config directory for hellonginx:

.. code-block:: bash

   sudo mkdir -p /etc/reahl.d/hellonginx

Copy the contents of prod/etc on the example to /etc/reahl.d/hellonginx on the prod machine.

Create a directory (as root) for the database:

.. code-block:: bash

   sudo mkdir /var/local/hellonginx
   sudo chown www-data.www-data /var/local/hellonginx


Test your installation
~~~~~~~~~~~~~~~~~~~~~~

Become the www-data user and check what's installed in the venv:

.. code-block:: bash

    sudo -u www-data bash -l
    source /usr/local/hellonginx/venv/bin/activate
    python -m pip freeze | grep hellonginx
    python -c "from hellonginxwsgi import application"

If the last command completes with no errors, your app is configured correctly and you can exit out of the www-data
shell.


Create the database
-------------------

Create the database as www-data:

.. code-block:: bash

    sudo -u www-data bash -l
    source /usr/local/hellonginx/venv/bin/activate
    reahl createdbuser /etc/reahl.d/hellonginx
    reahl createdb /etc/reahl.d/hellonginx
    reahl createdbtables /etc/reahl.d/hellonginx

Test your database connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Still in the www-data shell, test again:

.. code-block:: bash

   python -c "from hellonginxwsgi import application; application.start()"

Serve your application using uwsgi appserver
--------------------------------------------

To configure uwsgi, put the contents of prod/uwsgi of the example into /etc/uwsgi/apps-available on the prod machine
and create a link as per the instructions in /etc/uwsgi/apps-available/README:

.. code-block:: bash

   ln -s /etc/uwsgi/apps-available/hellonginx.ini /etc/uwsgi/apps-enabled


Test your uwsgi config
~~~~~~~~~~~~~~~~~~~~~~

Run uwsgi on your installed app:

.. code-block:: bash

   sudo -u www-data uwsgi /etc/uwsgi/apps-enabled/hellonginx.ini  -s tcp:///localhost:8000

That command should start with output ending in::

    *** uWSGI is running in multiple interpreter mode ***
    spawned uWSGI worker 1 (and the only) (pid: 1340, cores: 2)
    WSGI app 0 (mountpoint='') ready in 1 seconds on interpreter 0x560c36c852c0 pid: 1340 (default app)

If you got this far, uwsgi is working correctly.
Terminate the previous command with <CTRL>C and then reload the uwsgi config:

.. code-block:: bash

   sudo systemctl reload uwsgi

Configure nginx to serve hellonginx from uwsgi
----------------------------------------------

To configure nginx, put the contents of prod/nginx of the example into /etc/nginx/sites-available on the prod machine.
Then, create a link from sites-enabled and reload nginx config:

.. code-block:: bash

   sudo ln -s /etc/nginx/sites-available/hellonginx /etc/nginx/sites-enabled/
   sudo systemctl reload nginx

Test your app being served by nginx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Your hellonginx app is configured to be served on the DNS name 'hellonginx'.
Fool your prod machine into thinking that name points to itself:

.. code-block:: bash

   sudo bash -c "echo '127.0.1.1 hellonginx' >> /etc/hosts"

Then test by running the following:

.. code-block:: bash

   python3 -c "from urllib.request import urlopen; import re; print(re.search(r'<p>.*?</p>', urlopen('http://hellonginx').read().decode('utf-8')).group(0))"

If you see the output:

```<p>Hello World!<p>```

...then all is up and running. Congratulations.



