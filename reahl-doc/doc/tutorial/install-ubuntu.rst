.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Preparing for installation on Ubuntu
====================================

Python is installed by default on Ubuntu and most other
distributions. Some Python packages that are going to be installed for
use by Reahl include source code written in C, and are compiled as
part of the installation. You need to install all the right tools to
make that possible.

It may very well be that these packages are already installed on your
system -- but we have to make sure. If you're not on a Debian-based
distro, you will have to find and install equivalents for your
platform. (Chances are they are called exactly the same.)

Python and basic development tools
----------------------------------

Python, a compiler and the basic python development tools are installed by issuing:

.. code-block:: bash

   sudo apt-get install python-dev gcc cython python-virtualenv

Additional necessary packages for a Reahl installation
------------------------------------------------------

The extra stuff needed by dependencies of Reahl itself are installed by issuing:

.. code-block:: bash

   sudo apt-get install libxml2-dev libxslt-dev libsqlite3-0



The first two of these packages (libxml2-dev and libxslt-dev) are used by some of our testing
infrastructure, and sqlite is the database used by the tutorial examples.

Remember to go back and :ref:`install Reahl itself in a virtualenv <install-reahl-itself>`!
