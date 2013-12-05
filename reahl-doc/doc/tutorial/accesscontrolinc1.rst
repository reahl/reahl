.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
A basic model
=============

.. sidebar:: Examples in this section

   - tutorial.access1

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

To start off, we first build some basic concepts from our planned
model. This gives a foundation onto which all the rest can be built,
and which can be extended as we go along. It is a good idea to write a
simple test that covers some facts explaining the model *before* the
actual code is written. 

Since we've been through writing tests for Addresses in the previous
examples, those will be skipped here. The tests below focus on the the
collaborators and rights aspects introduced by this
example. Previously an AddressBook was not necessary, since all
Addresses were seen to be in a single AddressBook -- the database
itself. This time around each Address belongs to a specific
AddressBook, so the concept of an AddressBook has to be mentioned in
our new tests:

.. literalinclude:: ../../reahl/doc/examples/tutorial/access1/access1_dev/accesstests1.py

After writing the test (and copying some code from the previous
examples), we're ready to write the model code that make the tests pass.

.. literalinclude:: ../../reahl/doc/examples/tutorial/access1/access1.py
