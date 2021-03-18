.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.


Production deployment using Docker
==================================

.. sidebar:: Examples in this section

   - howtos.hellodockernginx

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Get started
-----------

Check out the example on your development machine.

You will create a docker image for your example **app** with all its runtime dependencies installed along with the required config.
Two additional images for **web** (nginx) and your **database** (Postgres) will be composed.

The example assumes you need a Postgres database, however it can be changed to be MySQL fairly easily.

Follow the instructions for your chosen platform to `install docker <https://docs.docker.com/get-docker/>`_, and also
`docker-compose <https://docs.docker.com/compose/install/>`_. to make use of what the example provides.


Create docker images
--------------------

In the checked out example directory, build the required images.

.. note:: docker-compose will reference the provided docker-compose.yml file.


.. code:: bash

    docker-compose build

Verify that the required images built successfully:

.. code:: bash

    docker images | grep hellodockernginx

Expect output similar to:

::

    hellodockernginx_web       latest              e41c79d7ca1a        8 seconds ago       153MB
    hellodockernginx           latest              a351ff871b20        15 seconds ago      270MB

The hellodockernginx image contains *uwsgi* that will serve your **app**. Your **app**'s config
will point to the **database** container using the default ports.
Locations in image to take note of:

    - App is installed in a venv
        /app/venv
    - App config
        /etc/app-reahl
    - App static file location
        /app/www
    - wsgi config
        /etc/app-wsgi.ini

hellodockernginx_web will connect *nginx* to to your **app** on port 8080 through the created docker network. It
contains preconfigured SSL certificates.
Locations in image to take note of:

    - nginx config
        /etc/nginx/conf.d/default.conf


.. note:: You should modify the ```prod/nginx/Dockerfile``` to install your own production certificates and update the nginx default.conf.

Although your database image does not need to be built, check that it has been downloaded.

.. code:: bash

    docker images | grep postgres

Expect at least one entry for postgres

::

    postgres:12.3


Spin up containers
------------------


Docker hosting platforms
~~~~~~~~~~~~~~~~~~~~~~~~

There are so many Docker hosting platforms you can choose from. Follow the guides provided by your chosen supplier.

The next section will show you how to spin up containers yourself.

Spin up containers locally
~~~~~~~~~~~~~~~~~~~~~~~~~~

Before deploying the images in your production environment, you can test them locally.
Spin up containers for the built images and connect to your app.

.. code:: bash

    docker-compose up -d

Expect:

::

    Creating network "hellodockernginx_default" with the default driver
    Creating hellodockernginx_database_1 ... done
    Creating hellodockernginx_app_1      ... done
    Creating hellodockernginx_web_1      ... done

List the running containers:

.. code:: bash

    docker container list

::

    CONTAINER ID        IMAGE                  COMMAND                  CREATED             STATUS              PORTS                                         NAMES
    ca0dd108aa59        hellodockernginx_web   "/docker-entrypoint.…"   2 hours ago         Up 2 hours          0.0.0.0:8080->80/tcp, 0.0.0.0:8443->443/tcp   hellodockernginx_web_1
    1e91b70b24c7        hellodockernginx       "uwsgi --ini /etc/ap…"   2 hours ago         Up 2 hours          8080/tcp                                      hellodockernginx_app_1
    26c5e89f5fee        postgres:12.3          "docker-entrypoint.s…"   2 hours ago         Up 2 hours          5432/tcp                                      hellodockernginx_database_1


Prepare the database for your app.

.. code:: bash

    ./scripts/setup_database.sh

Expect

::

    Database setup complete

To inspect the **app** container, you can step into it with this command:

.. code:: bash

    docker exec -ti hellodockernginx_app_1 bash -l

View the output for the **app** container:

.. code:: bash

    docker logs hellodockernginx_app_1



Test your app being served by nginx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open a browser tab to `localhost:8080 <http://localhost:8080/>`_ and expect to see **Hello World!**

Or test it from a commandline:

.. code:: bash

   python3 -c "from urllib.request import urlopen; import re; print(re.search(r'<p>.*?</p>', urlopen('http://localhost:8080').read().decode('utf-8')).group(0))"

Similarly, expect:

```<p>Hello World!<p>```


Changes for a MySQL database
----------------------------

Modify these files that have been annotated with references to MySQL:

    - .reahlproject
        Replace the dependency on "reahl-postgresqlsupport" with "reahl-mysqlsupport"
    - prod/etc/reahl.config.d
        Modify the config to contain the MySQL required settings
    - prod/Dockerfile
        Change the ENV variables to cater for MySQL dependencies
    - scrips/setup_database.sh
        Change the commands to connect to MySQL database container
    - docker-compose.yml
        Replace the Postgres database section with the MySQL section

.. note:: run ```docker-compose down``` to stop and discard running containers.

Build and run the docker images again by following similar instructions given above.
