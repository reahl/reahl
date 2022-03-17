.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.




What changed in version 5.2
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
   

Graphing support
----------------

This release includes support for rendering Graphs. Instead of writing our own graphing library, we have added |Chart|
which renders a Figure created using `the Plotly Python library <https://github.com/plotly/plotly.py/>`_.

See the relevant HOWTOs for more information:

:doc:`howto/plotly`
  An example that shows the basics of using a |Chart|.

:doc:`howto/plotly2`
  An example showing how to update a |Chart| efficiently in response to user actions.


PayPal support
--------------

Added |PayPalButtonsPanel| which you can use to setup standard paypal payments. The panel displays the `PayPalButton <https://developer.paypal.com/docs/checkout/standard/>`_
for processing a given |PayPalOrder| providing seamless integration to PayPal using the `PayPal REST API <https://developer.paypal.com/api/orders/v2/>`_.

See the HOWTO for more information:

:doc:`howto/paypal`
  Add a |PayPalButtonsPanel| to your own shoppingcart for `PayPal <https://www.paypal.com>`_ payments.


Cross site request forgery (CSRF) protection
--------------------------------------------

When a user is logged into a web application, their browser will automatically identify them as such on subsequent
requests from the browser. An attacker can then trick the user to click on a link (such as from a malicious email)
which is opened by the logged in browser and then performs an action on behalf of the logged-in user.

This kind of attack is called Cross site request forgery, or CSRF for short.

In this version, Reahl protects against a CSRF exploit by default. Each form always includes a hidden input with a value
linked to the current session and signed by a secret key (which is kept on the server). When it is submitted, the server
checks that the signature matches and that the hidden input was generated recently.

If you need to use JavaScript to invoke a |RemoteMethod|, do so using Jquery. This ensures that the correct CSRF token
is sent with such a JavaScript call as well.

The secret key can be configured in web.config.py as `web.csrf_key`. This key is defaulted to an insecure value ---
remember to set to a value of your choice on each production server.

The timeout can be configured in web.config.py as `web.csrf_timeout_seconds`.

.. note:: The web.csrf_timeout_seconds timeout should always be shorter than session_lifetime.


Implemention interfaces
-----------------------

In order to accommodate CSRF protection three methods are added to |UserSessionProtocol|\: |preserve_session|,
|restore_session|, and |get_csrf_token|.


API changes
-----------

A |PrimitiveInput| is instructed to refresh a |Widget| upon change of the |Input|. This has always been done by
passing the `refresh_widget` keyword argument upon construction. The |set_refresh_widget| method has been added so that
this can be done at a later stage in order to simplify the order in which cooperating objects can be created.

The keyword argument `disable_csrf_check` was added to the `__init__` of |RemoteMethod| to enable selective exclusion
of a |RemoteMethod| from CSRF restrictions.

Updated dependencies
--------------------

Some included thirdparty JavaScript and CSS libraries were updated:

- The dependency on cssmin was removed, in favour of rcssmin 1.1.0.
- The dependency on slimit was removed, in favour of rjsmin 1.2.0.
- jQuery was upgraded from 3.5.1 to 3.6.0.
- jQueryUI was upgraded from 1.12.1 to 1.13.1.
- underscore.js was upgraded from 1.13.1 to 1.13.2.
- plotly.js was upgraded from 2.2.0 to 2.9.0.
- Bootstrap was upgraded from 4.5.3 to 4.6.1.

Some dependencies on thirdparty python packages have been loosened to include a higher max version:

- babel is allowed from 2.1.0 to 2.9.x
- twine is allowed from 1.15.0 to 3.8.x
- tzlocal is allowed from 2.0.0 to 4.1.x
- wheel is allowed from 0.34.0 to any larger version
- plotly is allowed from 5.1.0 to 5.6.x
- docutils is allowed from 0.14.0 to 0.18.x
- pygments is allowed from 2.1.0 to 2.11.x
- mysqlclient is allowed from 1.3.0 to 2.1.x
- wrapt is allowed from 1.11.0 to 1.13.x
- beautifulsoup4 is allowed from 4.6.0 to 4.10.x
- SQLAlchemy is allowed from 1.2 to 1.4
- alembic is allowed from 0.9 to 1.7

  
