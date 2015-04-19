.. Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Reahl examples
==============

Reahl comes with a number of examples ready for you to check out and
play with. These typically do not mean much when seen on their own --
*they are referred to all over* in :doc:`the rest of the tutorial<index>` to 
illustrate what is explained there. 

Here is a quick guide you can use as a cheat sheet for running these
examples.  :doc:`The next section<gettingstarted-develop>` contains a
step-by-step explanation of all the details here.


Listing and checking out examples
---------------------------------

Once inside the virtualenv where you installed Reahl, you can use this 
command to list all the examples that come with Reahl:

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

After first checking out an example, you need to do the following
before you can run it:

 - Go to the checked out example:

   .. code-block:: bash

      cd hello

 - Prepare the example for development:

   .. code-block:: bash

      reahl setup -- develop -N

 - Create a database:

   .. code-block:: bash

      reahl-control createdbuser etc
      reahl-control createdb etc
      reahl-control createdbtables etc


Once that is done, run the example:

.. code-block:: bash

   reahl serve etc


Cleaning up
-----------

All examples use the same database. Before you run a different
example, you need to remove the previous database:

.. code-block:: bash

   reahl-control dropdb etc

To remove a previous example from development, run:

.. code-block:: bash

   reahl setup -- develop -N --uninstall
