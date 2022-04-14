.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.




What changed in version 6.0
===========================

Upgrading
---------

To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc
   

Doing "away with" .reahlproject
-------------------------------

The .reahlproject file is one aspect of a home-grown way we use internally to develop Reahl itself: Reahl comprises
several individually distributed components and this requires some scaffolding to help us deal with all of these components
together. This scaffolding lives in reahl-dev, and is controlled by the .reahlproject file.

We also needed to store other metadata for our flavour of component as implemented by reahl-component, and to do that we used (and
later on over-used) the entry points mechanism of setuptools for storing this metadata. Writing a plain setup.cfg or setup.py with all
this data crammed into entry points eventually became too cumbersome to explain, which is why we continued up to now
to use .reahlproject which hid that from its users.

We have now changed how we store extra metadata:

You now should package a Reahl component using setuptools in a PEP517 compliant way without using our homegrown .reahlproject.

The .reahlproject and some of its accompanying scaffolding does not go away: its use is now optional and what it can do has shrunk.
We really intend for it to be used internally only at this point, and it will be removed entirely in the near future since it relies on
executing `setuptools.setup()` -- a practice which is deprecated.

If you are currently using a `.reahlproject`, you will have to migrate now to using a `setup.cfg`.


Migrating old .reahlproject files
---------------------------------

If you have a project with a .reahlproject file, first run inside of its root directory::

  reahl migratereahlproject

This creates a `setup.cfg` file with all the information you used to have in the `.reahlproject`.

Note however that it will put hardcoded lists of things like packages etc. So the idea is that you then edit
the `setup.cfg` to your liking, removing such hardcoded values where needed.

Secondly, create a `pyproject.toml` file next to your `setup.cfg` in which you list both setuptools and the newly minted
`reahl-component-metadata` as build dependencies, for example:

  .. literalinclude:: ../pyproject.toml


New habits
----------

Whenever you used to run::

  reahl setup develop -N  # which is the equivalent of python setup.py develop -N 

You will from now on install packages in development mode by running::

  python -m pip install --no-deps -e .
  


  
