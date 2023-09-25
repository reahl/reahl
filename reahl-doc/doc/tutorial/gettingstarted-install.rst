.. Copyright 2014-2023 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Install Reahl
=============

.. toctree::
   :hidden:

   install-docker
   install-ubuntu
   install-mac
   install-win

.. sidebar:: The bottom line

   Reahl itself is installed via pip, using extras in [] to select what you want:

   .. code-block:: bash

      python3 -m pip install 'reahl[declarative,sqlite,dev,doc]'


This version of Reahl requires version 3.6 of Python or greater.

If you know `Docker <https://www.docker.com>`_ then :doc:`use our
Docker dev box <install-docker>`. It contains a venv with Reahl
installed. Otherwise, follow the instructions below:


.. _prep_install:

Install Python with virtualenv support
--------------------------------------

On Linux, do:

   - Install Python:

      .. code-block:: bash

         sudo apt-get install python3 python3-venv

On Mac, do:

   - Install Homebrew:

     .. code-block:: bash

        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

   - Install python using homebrew:

     .. code-block:: bash

        brew install python

On Windows, do (in a command shell):

    - Download and install `Chocolatey <https://chocolatey.org/install>`_.
      
    - Install Python (in an Administrator shell): :code:`choco install python`.

.. _install-reahl-itself:

Create a virtualenv
-------------------

On Linux or Mac, do:

.. code-block:: bash

   python3 -m venv ./reahl_env

On Windows, do (in a command shell):

.. code-block:: bash

   python -m venv reahl_env

This creates a new directory `reahl_env` with an isolated Python
environment inside it.

Activate the virtualenv
-----------------------

On Linux or Mac:

.. code-block:: bash

   source ./reahl_env/bin/activate

On Windows:

.. code-block:: doscon

   reahl_env\Scripts\activate.ps1

Your prompt should change to reflect the active virtual environment.

Install Reahl in the virtualenv
-------------------------------

With your `virtualenv` activated, install Reahl:

.. code-block:: bash

   python -m pip install 'reahl[declarative,sqlite,dev,doc]'

Reahl is composed of different components---you only need some of them. The pip extras
(given in :code:`[]` above) let you choose what to install. 

You can install:

    declarative
      The SqlAlchemy declarative implementation of the web framework

    dev
      The development tools

    doc
      Documentation and examples

    sqlite
      Support for sqlite databases

    postgresql
      Support for postgresql databases

    mysql
      Support for MySQL databases


Congratulations!
----------------

With reahl installed, you can now:

   - :doc:`Explore a basic Hello World <gettingstarted-develop>`.
   - :doc:`Run one of our many examples <gettingstarted-examples>`.
