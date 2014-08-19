.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Reahl installation
==================

.. toctree::
   :hidden:

   install-ubuntu
   install-mac
   install-win


We recommend installing Reahl within a sandboxed Python environment
provided by `virtualenv <http://pypi.python.org/pypi/virtualenv>`_.
Doing this means that your main Python installation is left in the
state it currently is, and that you do not need permissions of
restricted users to install all the extra Python packages when
developing.

.. _prep_install:

Prepare your platform for Python development
--------------------------------------------

Before you can install Reahl itself, you need to install several
pieces of software on your platform (including Python and several
Python development tools like virtualenv). This differs from platform
to platform -- please follow the instructions for your platform:

- :doc:`Ubuntu (or other Debian-based Linux distributions) <install-ubuntu>`
- :doc:`Mac OS/X <install-mac>`
- :doc:`Windows <install-win>`

.. _install-reahl-itself:

Create a virtualenv and install Reahl inside it
-----------------------------------------------

If you followed the instructions above, virtualenv should have been
installed with the packages listed above. You need to now create a
virtual environment using virtualenv.

On Linux or Mac, do:

.. code-block:: bash

   virtualenv ./reahl_env

On Windows, do (in a command shell):

.. code-block:: bash

   virtualenv reahl_env
   
This creates a new directory `reahl_env` with an isolated Python
environment inside it.

In order to work inside that isolated environment, you need to execute
the following on the command line:

On Linux or Mac:

.. code-block:: bash

   source ./reahl_env/bin/activate

On Windows:

.. code-block:: bash

   reahl_env\Scripts\activate.bat

After activating your new environment, the prompt of the command line
changes to reflect the environment that is currently active.

.. sidebar:: For interest's sake

   Installing ``reahl[elixir,sqlite,dev,doc]`` results in an installation of
   Reahl implemented using Elixir (elixir), with Sqlite support (sqlite), the 
   Reahl development tools (dev) and documentation and examples (doc). This is
   all you need for following the tutorial.

   If you want to play with Postgresql too, you have to additionally
   install Postgresql itself and its client libraries for your
   platform before you install Reahl with PostgreSQL support inside
   the virtualenv:

   .. code-block:: bash

      easy_install reahl[postgresql]

With your `virtualenv` activated, Reahl can be installed into it by
issuing:

.. code-block:: bash

   easy_install reahl[elixir,sqlite,dev,doc]

.. note::

   If you're tempted to install using pip, be warned that on Windows
   that won't work... pip cannot install binary packages, and many of
   Reahl's dependencies are distributed in binary form for Windows.

This may run a while, as it installs all of the projects Reahl depends
on as well. Some of these dependencies are installed and built from
source, hence, this process needs :ref:`your platform to be prepared
properly for Python development <prep_install>` before you attempt to
install Reahl.

