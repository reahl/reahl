.. Copyright 2017 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Development environment setup
=============================

We use a bunch of tools while developing Reahl itself. Some are just
useful, some enable remote pair programming, and others make sure our
tests consistently run the same way.

To ensure things always work, and always work consistently, we employ
`Docker <https://www.docker.com>`_\. The `Reahl dev Docker image
<https://hub.docker.com/r/iwanvosloo/reahl-dev>`_ has all of these development tools
pre-installed and configured as well as a clean venv with Reahl itself.

If you just want to develop on your own project (even if it does not
use Reahl), you can still use the same tools as we do.


The Reahl dev Docker image
--------------------------

To use the Reahl dev Docker image, `install Docker and docker-compose
<https://docs.docker.com/get-docker/>`_, then put the following 
docker-compose.yaml file in your development directory:

.. literalinclude:: ../../../docker-compose.yaml


Inside the Docker dev image
---------------------------

Inside the Docker container, we have:

- Projects installed that Reahl depends on;
- A Python3 virtualenv prepared for Reahl development;
- A version of Firefox for tests;
- A matching version of Geckodriver to enable Selenium tests;
- Various ways to access the GUI on the Docker container; and
- Configuration for pip to allow local installation of what is built (useful for tox tests).

Using the container
-------------------

Run the container:

.. code-block:: bash

   touch ~/.bash_history_docker
   touch ~/.ssh/authorized_keys_docker 
   docker-compose up -d
   docker exec -u developer -ti reahl bash -l

.. note:: 

   The first time you do this might take a while, since the image needs to be 
   downloaded and prepared.

Run an example inside the container:

.. code-block:: bash

   cd ~/reahl
   reahl example tutorial.hello
   cd hello
   reahl setup develop -N
   reahl createdbuser etc
   reahl createdb etc
   reahl createdbtables etc
   reahl serve etc

On your own machine, navigate to the example at: `http://localhost:8000 <http://localhost:8000>`_


Ssh to the dev container
------------------------

Ssh-ing into the container is needed for pair programming or to see the GUI of the browser that 
runs selenium tests.

To be able to ssh, put your public ssh key on your host machine into ~/.ssh/authorized_keys_docker:

.. code-block:: bash

   cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys_docker

Test your ssh connection to the container:

.. code-block:: bash

   DOCKER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' reahl)
   ssh developer@$DOCKER_IP -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null



Browsers and seeing stuff
-------------------------

The webserver ports of the Docker dev container are forwarded to your local
machine. To surf to your app, start your app inside the container and point 
your usual browser to http://localhost:8000.

When tests are run inside the container, you may want to see the browser 
used for testing.

We use `an Xpra display server <https://xpra.org/>`_ for the Docker dev
container. It allows headless operation and sharing of GUI windows for pair
programming.

When you run a login shell inside the container an xpra display server is 
automatically started on :100.

If you are working alone, you can bypass the headless server by forwarding 
your local X display server by adding a `-X` to the ssh command:

.. code-block:: bash

   DOCKER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' reahl)
   ssh -X developer@$DOCKER_IP -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null




Editing code
------------

There's no IDE installed inside the Docker dev container. 

Edit the source code outside the container in your development directory - the changes 
will be visible inside the container.

For more advanced use, such as running and debugging code in an IDE, use an IDE that is able
to connect to a docker container or a ssh host. Your IDE also needs to be able to work with 
Python code *inside a specific virtualenv* on the remote host.

To find the IP address of the running container do::

  docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' reahl

To know which virtualenv to connect to, run::

  docker container exec -u developer reahl bash -l -c 'echo $VIRTUAL_ENV'

The virtualenv is the last line output, something like: /home/developer/.venvs/python3.10
   
Pair programming
----------------

We often pair program remotely. Doing this requires a bit more
know-how. Here's how we do it:

Lets assume John and Jane want to work together, and decide to do so
on Jane's computer.  In order to do this, Jane needs to expose her
Docker dev container on the Internet and allow John to log into it. From
there on, John can share various things with Jane via an ssh
connection to Jane's Docker dev container.

From a security point of view, Jane never puts her real workstation at
risk of tampering by John.

Install reahl-workstation on your development machine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The reahl-workstation component of Reahl is meant to be installed
separately on your own development workstation. It contains the
`reahl` command line and a few commands that are useful for pair
programming.

If you are on ubuntu install it like this:

.. code-block:: bash

   sudo apt-get install python-pip
   sudo pip install reahl-workstation

(The rest of this text assumes that you have reahl-workstation installed.)


Use ngrok to make a local Docker dev container accessible to remote co-workers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We use `ngrok <https://ngrok.com/>`_ to make a local Docker dev container
accessible on the Internet to all the tools we use.

Jane must have an account at ngrok, and share her Docker dev container.

In order to setup ngrok, download it--our scripts expect its executable
to be in your PATH. Follow the instructions on the ngrok website to
create an account and save your credentials locally.

To share a locally running Docker dev container (assuming ngrok is all set
up), Jane can then run `reahl ngrok start -D`. This command will provide 
output in the form of a DNS name and port number that the remote party can use
to access. Make a note of these for use later on.
   
Let the remote user connect securely
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We do not allow login via password for security reasons
[#passlogin]_. For John to be able to log in, his ssh public key needs
to be installed into Jane's Docker dev container. To do this, John should
send his public key to Jane. John's public key is in
`~/.ssh/id_rsa.pub` on his computer.

To enable John to log in, Jane edits the `~/.ssh/authorized_keys_docker` 
file on her host and append the contents of John's public key to whatever's 
in that file already.

Now John will be allowed in. John also needs to make sure when
connecting that he is connecting to the correct machine and not some
impostor. When Jane logs into her Docker dev container,
the various fingerprints belonging to the Docker dev container are printed
out. Jane should send this to John.

John can now ssh as the user called `developer` to the host and port
reported to Jane when she started ngrok. John will be presented with
one of the fingerprints of the machine he is connecting to. This
fingerprint should match one of the ones Jane sent earlier. If it
matches, John can say 'yes' to ssh, which will now remember the
fingerprint was OK, and not ask again.

Sharing a terminal with screen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gnu screen is a program used to share a terminal between two
people. It is configured for this use on the Docker dev container.

One user starts a screen session by doing (on the Docker dev container):

.. code-block:: bash

   screen

The other connects to the same screen session by doing (on the Docker dev container):

.. code-block:: bash

   screen -x

Now both can see and type on the same terminal.

Sharing a browser with xpra
~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is useful for both users to also see the same browser window also,
for example, when debugging JavaScript issues using in-browser tools.

If Jane logs into the Docker dev container,an xpra display server is started 
in the Docker dev container and all GUI programs will be displayed there.

In order to see that GUI, both Jane and John need to connect to it. It
is often very useful NOT to connect to it, because its not very
interesting to see the tests execute. In some circumstances (such
as debugging) you *do* however want to see what is going on.

Jane and John need to have xpra and `reahl-workstation` installed on
their own machines for this to work.

Jane connects by running (on her own machine): `reahl xpra attach -D`

John connects via ngrok using the machine name and port number
provided earlier, for example:

.. code-block:: bash

   reahl xpra attach -s developer@0.tcp.eu.ngrok.io -p 19837


Editing code together
~~~~~~~~~~~~~~~~~~~~~

There are a couple of IDEs and tools that allow collaborative editing. We
know of these:

 - `Floobits <https://floobits.com/>`_
 - `Vscode with its liveshare extension <https://marketplace.visualstudio.com/items?itemName=MS-vsliveshare.vsliveshare>`_
 - `Eclipse with saros plugin <https://www.saros-project.org/documentation/installation.html#via-eclipse-marketplace>`_
 - `Gobby <https://gobby.github.io/>`_

   
.. [#passlogin] Once you expose a Docker dev container to the Internet,
   malicious parties will discover it and start trying user name and
   password combinations to try and log in. We configured the Docker dev
   container to disallow password access via ssh altogether to guard
   against such attacks. What password would we have used
   out-of-the-box anyway?
   
