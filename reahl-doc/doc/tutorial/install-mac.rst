.. Copyright 2014-2023 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Preparing for installation on Mac OS/X
======================================

.. sidebar:: Behind the scenes

   `Homebrew <http://brew.sh/>`_, the "missing package manager for OS
   X" is a tool with which you can easily install certain packages on
   the Mac.

Follow the installation instructions for Python on `The Hitchhiker's guide to Python
<https://python-guide.readthedocs.io/en/latest/starting/install3/osx/#install3-osx>`_.

Here is the super-short summary:

- Install Homebrew:

  .. code-block:: bash

     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

- Install python:

  .. code-block:: bash

     brew install python

- Have some coffee.

Next :ref:`create a virtualenv <install-reahl-itself>`.
