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

     reahl setup -- develop -N

- Create a database:

  .. code-block:: bash

     reahl createdbuser etc
     reahl createdb etc
     reahl createdbtables etc


Once that is done, run the example:

.. code-block:: bash

   reahl serve etc


Cleaning up
-----------

All examples use the same database. Before you run a different
example, you need to remove the previous database:

.. code-block:: bash

   reahl dropdb etc

To remove a previous example from development, run:

.. code-block:: bash

   reahl setup -- develop -N --uninstall
