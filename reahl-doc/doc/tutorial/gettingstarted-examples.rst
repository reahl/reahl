.. Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Run more examples
=================

Reahl comes with a number of examples. These are not self-explanatory
-- *they are referred to all over* in :doc:`the rest of the
tutorial<index>` to illustrate what is explained there.

Here is a cheat sheet when you come across an example in
and you wonder how to run it.

Listing and checking out examples
---------------------------------

To list all the examples that come with Reahl:

.. code-block:: python

   reahl listexamples

The list of example names this outputs are referred to all over in our
documentation.

To get an example, run (e.g.):

.. code-block:: python

   reahl example tutorial.hello

This will create a directory "hello" in your current location containing the
example.


Running examples
----------------

After first checking out an example, do the following
before trying to run it:

- Go to the checked out example:

  .. code-block:: bash

     cd hello

- Prepare the example for development:

  .. code-block:: bash

     python -m pip install --no-deps -e .

- Create a database:

  .. code-block:: bash

     reahl createdbuser etc
     reahl createdb etc
     reahl createdbtables etc


Once that is done, run the example:

.. code-block:: bash

   reahl serve etc


Helpful hints
-------------

Each examples creates a sqlite database file in the root the example's
directory with a name derived from its `reahlsystem.root_egg`
configuration setting. The latter defaults to the name of the
directory in which the example resides.

To see the current configuration of an example (and which file
to set it in) run:

.. code-block:: bash

   reahl listconfig -f -v


You can drop the database for an example with:

.. code-block:: bash

   reahl dropdb etc

To remove a previous example from development, run:

.. code-block:: bash

   python -m pip uninstall <name of example>
