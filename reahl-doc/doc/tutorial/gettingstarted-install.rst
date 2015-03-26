.. Copyright 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
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


The bottom line
---------------

If you are a seasoned Python developer here is the quick summary. More detailed 
installation instructions follow below this section.

Reahl itself is installed via pip, using extras in [] to select what you want:
   
.. code-block:: bash
   
   pip install reahl[declarative,sqlite,dev,doc]  

On platforms other than Windows, some dependencies pulled in during installation
will also need to be compiled, needing:

   - Libxml, libxslt
   - Libsqlite   
   
   - Python headers for compiling the above
   - A C/C++ compiler (such as gcc) 
   - Cython


Read on for detailed instructions.

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
installed along with other required packages. You need to now create a
virtual environment using virtualenv.

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

Choose what to install
----------------------

Reahl is composed of a number of different components that you
can mix and match depending on your requirements. For example, 
you probably do not want the development tools in a production
environment, so they are packaged in a component you can omit.

In order to specify which sets of components you want installed,
you use keywords in square brackets behind `reahl` in the command
to pip as shown above. Here is a list of keywords you can 
include, and what they install:

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
 


