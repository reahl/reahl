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

In this example you will create a docker image for your example **app** with all its runtime dependencies
installed along with the required config using docker-compose on your local machine to simulate a production environment.

The **web** server (Nginx) and **database** (PostgreSQL) are run in separate containers.

The example assumes you need a PostgreSQL database, however :ref:`it can be changed to be MySQL fairly easily <mysql>`.

Follow the instructions for your chosen platform to `install docker <https://docs.docker.com/get-docker/>`_, and also
`docker-compose <https://docs.docker.com/compose/install/>`_.


Create docker images
--------------------

In the checked out example directory, build the required images.

.. note::
   docker-compose will reference the provided docker-compose.yml file.

.. code-block:: bash

    docker-compose build

Verify that the required images built successfully:

.. code-block:: bash

    docker images | grep hellodockernginx

Expect output similar to::

    hellodockernginx_web       latest              e41c79d7ca1a        8 seconds ago       153MB
    hellodockernginx           latest              a351ff871b20        15 seconds ago      270MB


Understanding docker-compose.yaml file
--------------------------------------

The `docker-compose.yaml` file in this example configures 3 services:

database
  This runs a PostgreSQL server, in a container named postgresql, with super user and password as specified in
  the given environment variables.

app
  The hellodockernginx image runs your app in a *uwsgi* server. Your **app**'s config
  points to the **database** service using the default ports.  See `prod/etc/reahl.config.py`:

  .. literalinclude:: ../../reahl/doc/examples/howtos/hellodockernginx/prod/etc/reahl.config.py

  Since this example uses services defined for docker-compose, this configuration can hard-code
  the service name `database`.

  The uwsi config ensures the hellodockernginxwsgi module is run by uwsgi:

  .. literalinclude:: ../../reahl/doc/examples/howtos/hellodockernginx/prod/uwsgi/app.ini

  The hellodockernginxwsgi module is part of your application and hard-codes where the Reahl configuration
  is read from:

  .. literalinclude:: ../../reahl/doc/examples/howtos/hellodockernginx/hellodockernginxwsgi.py

  Locations in the built image to take note of:

    - App is installed in a venv
        /app/venv
    - App's Reahl config directory
        /etc/app-reahl
    - App static file location
        /app/www
    - wsgi config
        /etc/app-wsgi.ini

   This image is built using `prod/Dockerfile` which works in two stages `base` and `build`:
    - base
      In this stage, development dependencies are installed, and a wheel is built for your app.
    - build
      In this stage, a venv is created, and your built wheel is installed along with its static files.

web
  The web service runs *nginx* in a container named hellodockernginx_web. Nginx is configured in `prod/nginx/app.conf`
  to reverse-proxy to your app using the `uwsgi_pass` directive. Note that since this is using services defined for
  docker-compose, this configuration can hard-code the service name `app`:

  .. literalinclude:: ../../reahl/doc/examples/howtos/hellodockernginx/prod/nginx/app.conf

  In order to be able to copy this config into the built image, this service also builds its container from
  `prod/nginx/Dockerfile`:

  .. literalinclude:: ../../reahl/doc/examples/howtos/hellodockernginx/prod/nginx/Dockerfile

  .. note::
     This configuration uses the insecure `snakeoil` certificates shipped in the ssl-cert package. You will
     install your own, mounting the actual certificates via a volume external to the image itself.

  Locations in the built image to take note of:

    - nginx config
        /etc/nginx/conf.d/default.conf



Test the image locally using docker-compose
-------------------------------------------

Spin up containers
~~~~~~~~~~~~~~~~~~

Before deploying the images in your production environment, you can test them locally.
Spin up containers for the built images and connect to your app.

.. code-block:: bash

    docker-compose up -d

Expect::

    Creating network "hellodockernginx_default" with the default driver
    Creating hellodockernginx_database_1 ... done
    Creating hellodockernginx_app_1      ... done
    Creating hellodockernginx_web_1      ... done

List the running containers:

.. code-block:: bash

    docker container list

Expect output::

    CONTAINER ID        IMAGE                  COMMAND                  CREATED             STATUS              PORTS                                         NAMES
    ca0dd108aa59        hellodockernginx_web   "/docker-entrypoint.…"   2 hours ago         Up 2 hours          0.0.0.0:8080->80/tcp, 0.0.0.0:8443->443/tcp   hellodockernginx_web_1
    1e91b70b24c7        hellodockernginx       "uwsgi --ini /etc/ap…"   2 hours ago         Up 2 hours          8080/tcp                                      hellodockernginx_app_1
    26c5e89f5fee        postgres:12.3          "docker-entrypoint.s…"   2 hours ago         Up 2 hours          5432/tcp                                      hellodockernginx_database_1


Create and initialise the database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prepare the database for your app by executing:

.. literalinclude:: ../../reahl/doc/examples/howtos/hellodockernginx/scripts/setup_database.sh


Check the database:

.. code-block:: bash

   docker-compose exec -T app /app/venv/bin/reahl sizedb /etc/app-reahl

Expect output like::

   Database size: 8177 kB


Inspect running app container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To inspect the **app** container, step into it with:

.. code-block:: bash

    docker exec -ti hellodockernginx_app_1 bash -l

View the logs for the **app** container:

.. code-block:: bash

    docker logs hellodockernginx_app_1



Test your app being served by nginx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Open a browser tab to `localhost:8080 <http://localhost:8080/>`_ and expect to see **Hello World!**

Or test it from a command line:

.. code-block:: bash

   python3 -c "from urllib.request import urlopen; import re; print(re.search(r'<p>.*?</p>', urlopen('http://localhost:8080').read().decode('utf-8')).group(0))"

Similarly, expect:

```<p>Hello World!<p>```


.. _mysql:

Changes for a MySQL database
----------------------------

Modify these files that have been annotated with references to MySQL:

    - setup.cfg
        Replace the dependency on "reahl-postgresqlsupport" with "reahl-mysqlsupport"
    - prod/etc/reahl.config.d
        Modify the config to contain the MySQL required settings
    - prod/Dockerfile
        Change the ENV variables to cater for MySQL dependencies
    - scrips/setup_database.sh
        Use the commands to connect to MySQL database container
    - docker-compose.yml
        Replace the Postgres database section with the MySQL section

.. note:: run ```docker-compose down``` to stop and discard running containers.

Build and run the docker images again by following similar instructions given above.
