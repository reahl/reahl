.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Session| replace:: :class:`~reahl.sqlalchemysupport.sqlalchemysupport.Session`
.. |Base| replace:: :class:`~reahl.sqlalchemysupport.sqlalchemysupport.Base`

Fetch Addresses from the database
=================================

.. sidebar:: Behind the scenes

   Persistence is done directly using `SqlAlchemy
   <http://www.sqlalchemy.org/>`_. 


Persisted Address instances
---------------------------


Reahl provides glue so you can persist Addresses in a database using
`SqlAlchemy <http://www.sqlalchemy.org/>`_:

.. sidebar:: Examples in this section

   - tutorial.addressbook1

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

* Use the SqlAlchemy |Session| and |Base| provided by
  :mod:`~reahl.sqlalchemysupport.sqlalchemysupport`.
* __tablename__ identifies the table Address instances go into;
* The `Column`\s map similarly named attributes to database columns;
* The id `Column` is the primary key for Addresses;
* Persist an Address instance with `Session.add()`.


.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/addressbook1.py
   :lines: 7-8

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/addressbook1.py
   :pyobject: Address


Change AddressBookPanel to query the database
---------------------------------------------

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/addressbook1.py
   :pyobject: AddressBookPanel

	      
Register Address with setup.cfg
-------------------------------

Reahl needs to know about persisted classes so it can (for example):

* create database tables
* migrate older databases to newer schemas

Register Address in your project by adding it to the :ref:`the "persisted" list <setup_cfg_persisted>` in :doc:`setup.cfg <../component/setup.cfg>`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/addressbook1/setup.cfg
   :language: ini
   :start-after: component =
   :prepend: component =


Housekeeping and your database schema
-------------------------------------

Whenever you change a `setup.cfg` file though, be sure to run:

.. code-block:: bash

   python -m pip install --no-deps -e .

To create a database, run:

.. code-block:: bash

   reahl createdbuser etc  # If you have not already
   reahl createdb etc
   reahl createdbtables etc

More useful commands:

.. code-block:: bash

   reahl dropdb etc
   reahl dropdbtables etc   

Configuration
-------------

Wonder where the database is? Check applicable config settings with:

.. code-block:: bash

   reahl listconfig etc -i

To see the actual current values of those:

.. code-block:: bash

   reahl listconfig etc -v
