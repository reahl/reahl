.. Copyright 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Preparing for installation on Windows
=====================================

We explain here how to prepare a proper Python development environment
for use with Reahl on Windows. When you've done this, :ref:`you still need to
install Reahl itself in a virtualenv -- (but that's a one-liner)
<install-reahl-itself>`.

Python and basic development tools
----------------------------------

On Windows, you need to install Python and a number of standard Python
development tools.

Installing all of this is explained excellently on `The Hitchhiker's guide to Python
<http://python-guide.readthedocs.org/en/latest/starting/install/win/>`_.

Here is the super-short summary:

- Download Python from `the official website <http://python.org/>`_ (version 2.7 or 3.3), and install it.
- Ensure that your path includes both the directory where the Python executable is located as well as Python's "Scripts" directory.
- Install setuptools:
    - download `ez_setup.py <https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py>`_ from the setuptools project on bitbucket.
    - run ez_setup.py (right-click, then choose "Open with > Python")
- Install pip:
    - download `get-pip.py <https://bootstrap.pypa.io/get-pip.py` from PyPA.
    - run get-pip.py (right-click, then choose "Open with > Python")

Wheel support and virtualenv
----------------------------

- Ensure you have the latest pip with wheel support

    In a command prompt window, execute:
    
    .. code-block:: bash
    
       pip install -U wheel

- Install virtualenv using wheels:

    In a command prompt window, execute:
    
    .. code-block:: bash
    
       pip install -U virtualenv


Remember to go back and :ref:`install Reahl itself in a virtualenv <install-reahl-itself>`!
