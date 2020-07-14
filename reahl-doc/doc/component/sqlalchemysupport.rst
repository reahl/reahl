.. Copyright 2013, 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Module reahl.sqlalchemysupport
------------------------------

.. automodule:: reahl.sqlalchemysupport.sqlalchemysupport


For using SqlAlchemy with Reahl
"""""""""""""""""""""""""""""""

.. autoattribute:: reahl.sqlalchemysupport.sqlalchemysupport.Session

.. autoattribute:: reahl.sqlalchemysupport.sqlalchemysupport.Base

.. autoattribute:: reahl.sqlalchemysupport.sqlalchemysupport.metadata


Sessions
""""""""
           
.. autofunction:: reahl.sqlalchemysupport.sqlalchemysupport.session_scoped


Names of database objects
"""""""""""""""""""""""""

.. autofunction:: pk_name

.. autofunction:: fk_name

.. autofunction:: ix_name


QueryAsSequence
"""""""""""""""

.. autoclass:: QueryAsSequence
   :members:
   :special-members:
   :exclude-members: __weakref__

PersistedField
""""""""""""""

.. autoclass:: PersistedField
   :members:


SqlAlchemyControl
"""""""""""""""""

.. autoclass:: SqlAlchemyControl
   :members:


TransactionVeto
"""""""""""""""

.. autoclass:: TransactionVeto
   :members:

