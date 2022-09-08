.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.




What changed in version 6.1
===========================

Upgrading
---------

To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc
   

Deprecated functionality
------------------------
- field.bind with break if already bound
- ExposedNames changes
  

Updated dependencies
--------------------

Some dependencies on thirdparty python packages have been loosened to include a higher max version:
- setuptools should now be 51.0.0 or higher


  
