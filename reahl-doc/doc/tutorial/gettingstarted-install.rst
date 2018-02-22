.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Install Reahl
=============

.. toctree::
   :hidden:

   install-vagrant
   install-ubuntu
   install-mac
   install-win

This version of Reahl requires version 2.7 of Python 2 or versions
of Python greater than 3.3.

Vagrant
-------

If you know `Vagrant <https://www.vagrantup.com>`_ then :doc:`use our
Vagrant box <install-vagrant>`. It contains a virtualenv with Reahl
installed as per the instructions below.


Without Vagrant
---------------

If you don't use Vagrant you should install Reahl within a sandboxed
Python environment provided by `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_.

.. sidebar:: The bottom line

   If you are a seasoned Python developer here is the quick summary of the more detailed 
   instructions.

   Reahl itself is installed via pip, using extras in [] to select what you want:
   
   .. code-block:: bash
   
      pip install reahl[declarative,sqlite,dev,doc]  

   On platforms other than Windows, some dependencies pulled in during installation
   will also need to be compiled. To be able to compile these, you will also need:

     - Libxml, libxslt
     - Libsqlite   
   
     - Python headers for compiling the above
     - A C/C++ compiler (such as gcc) 
     - Cython


.. _prep_install:

#. Prepare your platform

   Before you can install Reahl itself, you need to install several
   pieces of software on your platform (including Python and several
   Python development tools like virtualenv). This differs from platform
   to platform -- please follow the instructions for your platform:

   - :doc:`Ubuntu (or other Debian-based Linux distributions) <install-ubuntu>`
   - :doc:`Mac OS/X <install-mac>`
   - :doc:`Windows <install-win>`

   Once you have prepared your system, install Reahl itself in a virtualenv:

   .. _install-reahl-itself:

#. Create a virtualenv

   Next, you need to create a virtual environment using virtualenv and
   install Reahl inside it.

   On Linux or Mac, do:

   .. code-block:: bash

      virtualenv ./reahl_env

   .. note::

      If you have more than one version of Python installed, also pass the `-p` argument
      to virtualenv, specifying the path to the Python interpreter you want this
      virtualenv for.

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

#. Install Reahl in the virtualenv

   Reahl is composed of different components---you only need some of them
   (you probably do not want the development tools in a production
   environment).

   You can install:

       declarative
         The declarative implementation of the web framework

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

   With your `virtualenv` activated, Reahl can be installed into it by
   issuing (regardless of platform):

   .. code-block:: bash

      pip install reahl[declarative,sqlite,dev,doc]

   .. note::

      Some of Reahl's dependencies are distributed in binary form for
      Windows. These have to be installed using the wheel format when
      using pip, so do ensure that you are using a version of Pip > 6.

   This may run a while, as it installs all of the projects Reahl depends
   on as well. Some of these dependencies are installed and built from
   source (on platforms other than windows), hence, this process needs
   :ref:`your platform to be prepared properly for Python development
   <prep_install>` before you attempt to install Reahl.

