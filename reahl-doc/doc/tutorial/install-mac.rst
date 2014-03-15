.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Preparing for installation on Mac OS/X
======================================

We explain here how to prepare a proper Python development environment
for use with Reahl on Mac OS/X together with one or two things also
needed by Reahl. When you've done this, :ref:`you still need to
install Reahl itself in a virtualenv -- (but that's a one-liner)
<install-reahl-itself>`.

Python and basic development tools
----------------------------------

.. sidebar:: Behind the scenes

   `Homebrew <http://brew.sh/>`_, the "missing package manager for OS
   X" is a tool with which you can easily install certain packages on
   the Mac.

On Mac OS/X, you need a proper installation of Python (ie., not the
standard Python that comes with the OS), you need a C compiler, Python
development header files and `homebrew <http://brew.sh/>`_ to make
installing what you need easier.

Installing all these as well as the necessary Python development tools
is explained excellently on `The Hitchhiker's guide to Python
<http://python-guide.readthedocs.org/en/latest/starting/install/osx/>`_.

Here is the super-short summary:

- Install XCode, open it, go to Preferences, select Download and install "Command Line Tools"
- Install Homebrew by running:

  .. code-block:: bash

     ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"

- Put Homebrew in your path
- Install python:

  .. code-block:: bash

     brew install python

- Have some coffee.

Additional necessary packages for a Reahl installation
------------------------------------------------------

Reahl will need a few additional packages to be installed. To install them, simply run:

  .. code-block:: bash

     brew install libxml2 libxslt sqlite

The first two (libxml2 and libxslt) are used by some of our testing
infrastructure, and sqlite is the database used by the tutorial examples.

Remember to go back and :ref:`install Reahl itself in a virtualenv <install-reahl-itself>`!
