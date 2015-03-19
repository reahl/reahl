.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
A basic model
=============

.. sidebar:: Examples in this section

   - tutorial.modeltests1

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Models
------

In an object oriented program, the problem domain for which the
program is written is modelled by creating a class representing each
concept in that domain.

Here is a simple model for an address book application:

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests1.py
   :pyobject: Address

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests1.py
   :pyobject: AddressBook


Exercising a model
------------------

.. sidebar:: Behind the scenes

   `Nosetests <https://nose.readthedocs.org/en/latest/>`_ is a project
   that makes writing and running tests a bit easier. Reahl provides
   some extensions to nosetests as well -- but that is a topic for
   another day.

   Be sure to check out Nosetests, as it is used throughout examples
   and Reahl code.

Whenever you write code that forms part of a model, it is useful to be
able to execute that code. The same is true for the examples presented
in this tutorial.

The sensible way to execute code is to write some tests for that code.
Hence *each example here is a test* -- and to keep things simple we
include the toy model and its test together in a single file for now.

To put the simple model presented above through its paces, you can
put it together with a test in a file as follows, say test.py:

.. literalinclude:: ../../reahl/doc/examples/tutorial/modeltests1.py

You can execute this example by running:

.. code-block:: bash

   nosetests modeltests1.py

Sometimes it is useful to include a line somewhere in that test which
will invoke the Python debugger so that you can play around with the
running code:

.. code-block:: python

   import pdb; pdb.set_trace()

...but then be sure to invoke nosetests with its `-s` commandline
option:

.. code-block:: bash

   nosetests -s modeltests1.py

   

