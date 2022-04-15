.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
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

      python -m pip install reahl[declarative,sqlite,dev,doc]

   On platforms other than Windows, some dependencies pulled in during installation
   will also need to be compiled. To be able to compile these, you will also need:

     - Libxml, libxslt
     - Libsqlite

     - Python headers for compiling the above
     - A C/C++ compiler (such as gcc)
     - Cython

This version of Reahl requires version 3.6 of Python or greater.

Reahl depends on a lot of other software. Installing it is not just a
straight `python -m pip install reahl`. You need to install a couple of other
things first.

If you know `Docker <https://www.docker.com>`_ then :doc:`use our
Docker dev box <install-docker>`. It contains a virtualenv with Reahl
installed. Otherwise, follow the instructions below:


.. _prep_install:

1. Prepare your platform

   - :doc:`Ubuntu (or other Debian-based Linux distributions) <install-ubuntu>`
   - :doc:`Mac OS/X <install-mac>`
   - :doc:`Windows <install-win>`


.. _install-reahl-itself:

2. Create a virtualenv

   On Linux or Mac, do:

   .. code-block:: bash

      python3 -m venv ./reahl_env

   On Windows, do (in a command shell):

   .. code-block:: bash

      python3 -m venv reahl_env

   This creates a new directory `reahl_env` with an isolated Python
   environment inside it.

3. Activate the virtualenv

   On Linux or Mac:

   .. code-block:: bash

      source ./reahl_env/bin/activate

   On Windows:

   .. code-block:: doscon

      reahl_env\Scripts\activate.ps1

   Your prompt should change to reflect the active virtual environment.

4. Install Reahl in the virtualenv

   With your `virtualenv` activated, install Reahl:

   .. code-block:: bash

      python -m pip install reahl[declarative,sqlite,dev,doc]

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

   .. note::

      You need pip > 6 (for wheel support) on Windows.



