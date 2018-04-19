.. Copyright 2017 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Development environment setup
=============================

We use a bunch of tools while developing Reahl itself. Some are just
useful, some enable remote pair programming, and others make sure our
tests consistently run the same way.

To ensure things always work, and always work consistently, we employ
`Vagrant <https://www.vagrantup.com>`_ with our own `Vagrant box
<https://www.vagrantup.com/docs/boxes.html>`_ with all of these
pre-installed and configured.

If you just want to develop on your own project (even if it does not
use Reahl), you can still use the same tools as we do.

It may take some extra effort to set up and learn Vagrant if you don't
know it already, but it is well worth it.


The Reahl Vagrant box
---------------------

The Reahl vagrant box is called 'reahl/bionic64'[#lts]_, to use it put the
following in your Vagrantfile:

.. code-block:: ruby

   config.vm.box = "reahl/bionic64"

Reahl already has a correct Vagrantfile in the root of its source
tree. A project using Reahl can use the `vagrant/Vagrantfile.example`
file as starting point.

Inside the Vagrant box
----------------------

Inside the Vagrant box, we have:
 - Projects installed that Reahl depends on;
 - A postgresql database with the `vagrant` user set up as administrator;
 - A Python3 virtualenv prepared for Reahl development;
 - A version of chromium-browser that works well with tests;
 - A matching version of chromedriver to enable selenium tests; 
 - Various ways to access the GUI on the Vagrant machine; and
 - Configuration for pip to allow local installation of what is built (useful for tox tests).

Running the tests
-----------------

You should be able to run tests immediately:

.. code-block:: bash

   vagrant up
   vagrant ssh
   cd /vagrant
   reahl shell -sdX reahl unit

The last command changes into the directory of each separate Reahl component,
and run its tests in turn.

Browsers and seeing stuff
-------------------------

We use `an Xpra display server <https://xpra.org/>`_ for the Vagrant
machine. It allows headless operation and sharing of GUI windows for pair
programming.

When you run tests a per above instructions, the browser is fired up
headless on DISPLAY :100.

An xpra display server is automatically started on :100 when you `vagrant ssh`.

If you are working alone and would rather see what is happening, you
can bypass the headless server by forwarding your local X display
server. Do this by entering vagrant like so:

.. code-block:: bash

   vagrant ssh -- -X

The webserver ports of the Vagrant box are forwarded to your local
machine. Thus, you need not make use of the browser inside the Vagrant
box to check things out. You can use your own, on your own machine: if
you have a webserver running inside vagrant on port 8000, you can
visit it by surfing to http://localhost:8000

Editing code
------------

There's no IDE installed inside the Vagrant machine. You need to
install and configure one of your choosing on your own machine. You
need to use an IDE that is able to connect to a remote host (the
Vagrant machine is "remote" from the perspective of an IDE). Your IDE
also needs to be able to work with Python code *inside a specific
virtualenv* on the remote host.

To know to which machine to connect your IDE, run (on your own machine)::

  vagrant ssh-info

To know which virtualenv to connect to, ssh into the Vagrant machine, and run::

  echo $VIRTUAL_ENV

   
Pair programming
----------------

We often pair program remotely. Doing this requires a bit more
know-how. Here's how we do it:

Lets assume John and Jane want to work together, and decide to do so
on Jane's computer.  In order to do this, Jane needs to expose her
Vagrant machine on the Internet and allow John to log into it. From
there on, John can share various things with Jane via an ssh
connection to Jane's Vagrant machine.

From a security point of view, Jane never puts her real workstation at
risk of tampering by John.

Install reahl-workstation on your development machine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The reahl-workstation component of Reahl is meant to be installed
separately on your own development workstation. It contains the
`reahl` commandline and a few commands that are useful for pair
programming.

If you are on ubuntu install it like this:

.. code-block: bash

   sudo apt-get install python-pip
   sudo pip install reahl-workstation

(The rest of this text assumed that you have reahl-workstation installed.)


Use ngrok to expose the Vagrant machine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We use `ngrok <https://ngrok.com/>`_ to make a local Vagrant machine
accessible on the Internet to all the tools we use.

Jane must have an account at ngrok, and share her Vagrant machine.

In order to setup ngrok, download it--our scripts expect its executable
to be in `~/bin`. Follow the instructions on the ngrok website to
create an account and save your credentials locally.

To share a locally running Vagrant machine (assuming ngrok is all set
up), Jane can then run `reahl ngrok start -V` from the root
directory of the Reahl source.  This command will provide output in
the form of a DNS name and port number that the remote party can use
to access. Make a note of these for use later on.
   
Let the remote user connect securely
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We do not allow login via password for security reasons
[#passlogin]_. For John to be able to log in, his ssh public key needs
to be installed into Jane's Vagrant machine. To do this, John should
send his public key to Jane. John's public key is in
`~/.ssh/id_rsa.pub` on his computer.

To enable John to log in, Jane edits the
`/home/vagrant/.ssh/authorized_keys` file on the Vagrant machine and
append the contents of John's public key to whatever's in that file
already.

Now John will be allowed in. John also needs to make sure when
connecting that he is connecting to the correct machine and not some
impostor. When Jane logs into her Vagrant machine via `vagrant ssh`,
the various fingerprints belonging to the Vagrant machine are printed
out in various formats. Jane should send this to John.

John can now ssh as the user called `vagrant` to the host and port
reported to Jane when she started ngrok. John will be presented with
one of the fingerprints of the machine he is connecting to. This
fingerprint should match one of the ones Jane sent earlier. If it
matches, John can say 'yes' to ssh, which will now remember the
fingerprint was OK, and not ask again.

Sharing a terminal with screen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gnu screen is a program used to share a terminal between two
people. It is configured for this use on the Vagrant machine.

One user starts a screen session by doing (on the Vagrant machine):

.. code-block:: bash

   screen

The other connects to the same screen session by doing (on the Vagrant machine):

.. code-block:: bash

   screen -x

Now both can see and type on the same terminal.

Sharing a browser with xpra
~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is useful for both users to also see the same browser window also,
for example, when debugging JavaScript issues using in-browser tools.

If Jane logs into the Vagrant machine using only `vagrant ssh` (ie, no
`-- -X` argument), an xpra display server is automatically started on
the Vagrant machine and all GUI programs will be displayed there.

In order to see that GUI, both Jane and John need to connect to it. It
is often very useful NOT to connect to it, because its not very
interesting to see the tests execute. In some circumstances (such
as debugging) you *do* however want to see what is going on.

Jane and John need to have xpra and `reahl-workstation` installed on
their own machines for this to work.

Jane connects by running (on her own machine, from within
the root of the Reahl source code): `reahl xpra attach -V`

John connects via ngrok using the machine name and port number
provided earlier:

.. code-block:: bash

   reahl xpra attach -s vagrant@0.tcp.eu.ngrok.io -p 19837


Editing code together
~~~~~~~~~~~~~~~~~~~~~

To edit code collaboratively, we use `floobits
<https://floobits.com/>`_. Floobits is a hosted service, which
provides plugins for various IDEs to allow such collaborative editing
from your own IDE. It also allows editing on the web.


.. [#lts] We develop on the latest LTS version of Ubuntu.
   
.. [#passlogin] Once you expose a Vagrant machine to the Internet,
   malicious parties will discover it and start trying user name and
   password combinations to try and log in. We configured the Vagrant
   machine to disallow password access via ssh altogether to guard
   against such attacks. What password would we have used
   out-of-the-box anyway?
   
