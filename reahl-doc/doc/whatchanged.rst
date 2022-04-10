.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.




What changed in version 6.0
===========================

.. |PrimitiveInput| replace:: :class:`~reahl.web.ui.PrimitiveInput`
.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |Chart| replace:: :class:`~reahl.web.plotly.Chart`
.. |Input| replace:: :class:`~reahl.web.ui.Input`
.. |set_refresh_widget| replace:: :meth:`~reahl.web.ui.PrimitiveInput.set_refresh_widget`
.. |RemoteMethod| replace:: :class:`~reahl.web.fw.RemoteMethod`
.. |UserSessionProtocol| replace:: :class:`~reahl.web.interfaces.UserSessionProtocol`
.. |preserve_session| replace:: :meth:`~reahl.web.interfaces.UserSessionProtocol.preserve_session`
.. |restore_session| replace:: :meth:`~reahl.web.interfaces.UserSessionProtocol.restore_session`
.. |get_csrf_token| replace:: :meth:`~reahl.web.interfaces.UserSessionProtocol.get_csrf_token`
.. |PayPalButtonsPanel| replace:: :class:`~reahl.paypalsupport.paypalsupport.PayPalButtonsPanel`
.. |PayPalOrder| replace:: :class:`~reahl.paypalsupport.paypalsupport.PayPalOrder`


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
this data crammed in weird ways into entry points eventually became too cumbersome to even explain, which is why we continued to push
for the use of .reahlproject which hid that from its users.

We have now changed how we store extra metadata.

You now should package a Reahl component using setuptools in a PEP517 compliant way without using our homegrown .reahlproject.

The .reahlproject and some of its accompanying scaffolding does not go away: its use is now optional and what it can do has shrunk.
We really intend for it to be used internally only at this point.

If you really DO want to use a `.reahlcomponent` -- that is a separate concern and you can do that too, although there are changes to what
you can put in it.


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
  


  
