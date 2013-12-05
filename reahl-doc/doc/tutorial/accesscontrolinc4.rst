.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Hidden security features
========================

Malicious attackers can try to bypass any access control (or even
validation) that a programmer may have put in place. Reahl safeguards
against such attacks -- in most places without your having to worry
about it. Even so, a careful programmer would like to know what
happens under the hood to protect against breaches, and would want to
be able to direct the underlying mechanisms.

One form of attack concerns :class:`~reahl.web.ui.Button`\ s and Inputs. The server may have
served a page containing a :class:`~reahl.web.ui.Button` or :class:`~reahl.web.ui.Input` that is greyed out in order
to prevent the user from invoking an :class:`~reahl.component.modelinterface.Action` or from supplying input
via the :class:`~reahl.web.ui.Input` (respectively). A user could edit the HTML that was
served to make these elements active again, and in this way try to
forcebly click on a :class:`~reahl.web.ui.Button` or supply input.

This sort of attack is automatically stopped on the server side. Since
all the access control rules are available on the server, each
incoming request is checked against them as well. Attempts to click on
:class:`~reahl.web.ui.Button`\ s that were originally rendered greyed out, or to supply input
to an :class:`~reahl.web.ui.Input` that should be greyed out are dealt with by the server as
invalid input. So, there's nothing a programmer need to do in order to
safeguard the rules that have been put in place.

A malicious user still has the option of snooping on network traffic
between the server and the client browser on order to learn sensitive
information, such as a password. Some safeguarding does happen
automatically here, but the programmer may have to give some clues as
to what information needs to be protected.

If there are :class:`~reahl.web.fw.Widget`\ s that are deemed security sensitive on a
particular page, that page is served via encrypted connection. :class:`~reahl.web.ui.Button`
clicks originating from it are also sent via encrypted connection.

A programmer can explicitly mark a :class:`~reahl.web.fw.Widget` as being security
sensitive. However, it is sometimes possible to derive the security
sensitivity (or not) of a :class:`~reahl.web.fw.Widget` automatically: 
By default :class:`~reahl.web.fw.Widget`\ s have no access rights set for reading. By giving a
particular :class:`~reahl.web.fw.Widget` a `read_check` method, the programmer informs the
system that there's a chance that someone should not be able
to read the contents of the :class:`~reahl.web.fw.Widget`. In such a case the :class:`~reahl.web.fw.Widget` is
automatically deemed as being security sensitive.

In the case of :class:`~reahl.web.ui.Input` :class:`~reahl.web.fw.Widget`\ s, the same inference is made from the
access rights of the :class:`~reahl.component.modelinterface.Field` to which it is linked. 

Thus, in many cases the framework is able to detect when something
should be served via encrypted connection, but the programmer can also
force this behaviour simply by explicitly marking a :class:`~reahl.web.fw.Widget` as security
sensitive. This is done by calling the `.set_as_security_sensitive()`
method on a :class:`~reahl.web.fw.Widget`.

In this example, the :class:`~reahl.component.modelinterface.PasswordField` is security sensitive, since a
:class:`~reahl.component.modelinterface.PasswordField` is never allowed to be read. You will notice the effect
of this when logging into the application for the first time: the home
page will be served via HTTPS.
