.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.




What changed in version 5.2
===========================

.. |PrimitiveInput| replace:: :class:`~reahl.web.ui.PrimitiveInput`
.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |Chart| replace:: :class:`~reahl.web.plotly.Chart`
.. |Input| replace:: :class:`~reahl.web.ui.Input`
.. |set_refresh_widget| replace:: :meth:`~reahl.web.ui.PrimitiveInput.set_refresh_widget`


Upgrading
---------

To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc
   

Graphing support
----------------

This release includes support for rendering Graphs. Instead of writing our own graphing library, we have added a |Chart|
|Widget| which renders a Figure created using `the Plotly Python library <https://github.com/plotly/plotly.py/>_`.

See the relevant HOWTOs for more information:

:doc:`<howto/plotly>`
  An example that shows the basics of using a |Chart|.

:doc:`<howto/plotly2>`
  An example showing how to update a |Chart| efficiently in response to user actions.


API changes
-----------

A |PrimitiveInput| is instructed to refresh a |Widget| upon change of the |Input|. This has always been done by
passing the `refresh_widget` keyword argument upon construction. The |set_refresh_widget| method has been added so that
this can be done at a later stage in order to simplify the order in which cooperating objects can be created.


Updated dependencies
--------------------

Some included thirdparty JavaScript and CSS libraries were updated:

-