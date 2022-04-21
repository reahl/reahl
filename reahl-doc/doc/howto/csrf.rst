.. Copyright 2022 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |RemoteMethod| replace:: :class:`~reahl.web.fw.RemoteMethod`


Protection against cross site request forgery (CSRF) attacks
============================================================

When a user is logged into a web application, their browser will automatically identify them as such on subsequent
requests from the browser. An attacker can then trick the user to click on a link (such as from a malicious email)
which is opened by the logged in browser and then performs an action on behalf of the logged-in user.

This kind of attack is called Cross site request forgery, or CSRF for short.

Reahl protects against a CSRF exploit by default. Each form always includes a hidden input with a value
linked to the current session and signed by a secret key (which is kept on the server). When it is submitted, the server
checks that the signature matches and that the hidden input was generated recently.

If you need to use JavaScript to invoke a |RemoteMethod|, do so using Jquery. This ensures that the correct CSRF token
is sent with such a JavaScript call as well. A |RemoteMethod| can be made to ignore the CSRF protection by passing
True to `disable_csrf_check` of |RemoteMethod|\.

The secret key can be configured in web.config.py as `web.csrf_key`. This key is defaulted to an insecure value ---
remember to set to a value of your choice on each production server.

The timeout can be configured in web.config.py as `web.csrf_timeout_seconds`.

.. note:: The web.csrf_timeout_seconds timeout should always be shorter than session_lifetime.


