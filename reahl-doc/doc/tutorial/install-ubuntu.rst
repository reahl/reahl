.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
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

   sudo apt-get install python3-dev gcc cython python-virtualenv

.. note::

   For Python 2, just install python-dev (or python2.7-dev) instead of python3-dev above.


Additional necessary packages for a Reahl installation
------------------------------------------------------

The extra stuff needed by dependencies of Reahl itself are installed by issuing:

.. code-block:: bash

   sudo apt-get install libxml2-dev libxslt-dev libsqlite3-0



The first two of these packages (libxml2-dev and libxslt-dev) are used by some of our testing
infrastructure, and sqlite is the database used by the tutorial examples.

Remember to go back and :ref:`install Reahl itself in a virtualenv <install-reahl-itself>`!

Chromedriver
------------

You do not need to install chromedriver in order to follow this
tutorial. However, if you are going to use chromium for testing, you
will need chromedriver. Installation of chromedriver in Ubuntu need a
bit of tweaking, and this seemed toe appropriate place to jot down
what is needed:

Install the chromium-chromedriver package:

.. code-block:: bash

   sudo apt-get install chromium-chromedriver

In Ubuntu 14.4, this installs the chromedriver binary in
`/usr/lib/chromium-browser/chromedriver`, but it neglects setting
the LD_LIBRARY_PATH for it to work correctly. To correct this,
create the file `/etc/ld.so.conf.d/chrome_lib.conf`, with the
following contents:

.. code-block:: bash

   /usr/lib/chromium-browser/libs

Finally, run:

.. code-block:: bash

   sudo ldconfig

You also need to adjust your PATH so that /usr/lib/chromium-browser is
included. In your .bashrc, add the line:

.. code-block:: bash

   export PATH=$PATH:/usr/lib/chromium-browser
