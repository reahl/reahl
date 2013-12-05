.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Security considerations
=======================

The :doc:`access control example <accesscontrol>` shows how a
programmer can specify when elements of a page can be accessed or
not. Behind the scenes however, the framework needs to enforce those
rules in such a way that a user with malicious intent cannot
circumvent the access control measures. The things an attacker could
attempt have to do with the lower level implementation details we'd
like to alleviate the programmer from thinking about...but it is
worthwhile knowing something about what the framework does to
safeguard its own security.

Firstly, some Widgets are deemed security sensitive -- either because
they have been marked as such by a programmer, or if the framework can
deduce from the underlying access control rules that their contents
should not be visible to just anyone. Any page that contains a
security sensitive Widget is automatically served via an encrypted
connection. Button clicks on such a page are also submitted via
encrypted connection. This happens automatically, but it is useful for
a programmer to know when this mechanism will kick in.

Doing communication via encrypted connection prevents someone from
snooping on your network traffic to learn sensitive info, but it does
not protect against a malicious user or browser. A malicious user with
enough technical know-how can modify the HTML rendered in his browser
to, say, make a greyed out button active again so that it can be
clicked upon. This avenue of attack is blocked on the server, based on
the fact that all the access control rules are available
server-side. The server refuses Button clicks that are not allowed and
will discard input for a Field unless allowed.


