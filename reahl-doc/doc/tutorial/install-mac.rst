.. Copyright 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Preparing for installation on Mac OS/X
======================================

.. sidebar:: Behind the scenes

   `Homebrew <http://brew.sh/>`_, the "missing package manager for OS
   X" is a tool with which you can easily install certain packages on
   the Mac.

1. Python and basic development tools

   On Mac OS/X, you need a proper installation of Python (ie., not the
   standard Python that comes with the OS), you need a C compiler, Python
   development header files and `homebrew <http://brew.sh/>`_ to make
   installing what you need easier.

   Follow the installation instructions for Python on `The Hitchhiker's guide to Python
   <https://python-guide.readthedocs.io/en/latest/starting/install3/osx/#install3-osx>`_.
   
   Here is the super-short summary:

   - Install XCode, open it, go to Preferences, select Download and install "Command Line Tools"
   - Install Homebrew:

     .. code-block:: bash

        ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"

   - Put Homebrew in your path
   - Install python:

     .. code-block:: bash

        brew install python

   - Have some coffee.

2. Additional necessary packages for a Reahl installation

     .. code-block:: bash

        brew install libxml2 libxslt sqlite

   Next :ref:`create a virtualenv <install-reahl-itself>`.
