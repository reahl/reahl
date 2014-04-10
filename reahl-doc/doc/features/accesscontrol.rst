.. Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Access control example
======================

Fields and Events can be set up with special methods that the
framework can call in order to determine what rights the current user
has regarding the Field or Event.  There are two kinds of rights:
whether one can *read* or *write* the item.

An Input will only be visible and editable if the user is allowed to
*read* and *write* the Field to which the Input is linked.  A Field that is
readable but not writable will cause an Input to be visible but greyed
out. If the Field is not readable and also not writable to a user, it
will not appear on Views shown to that user.

The access rights of an Event influence a Button linked to it similarly 
to how the access rights on a Field control the display of an Input 
linked to it.

The example program presented here renders a single page with an
input and a button. Each of these elements are restricted in some way:

 - The input labelled `Greyed out` is for a Field that is allowed to be
   *read* but not *written* (ie, changed).
 - The `Greyed out button` is greyed out for similar reasons: the user
   may see the button, but is not allowed to execute its action.

 .. figure:: ../_build/screenshots/access.png
    :align: center
    :alt: An screenshot showing a greyed out input and disabled buttons.

Notice in the code below that one specifies an Action for the
framework to call in order to determine whether a Field is readable or
writable. These Actions should return True or False to indicate whether
the user has the corresponding right or not, respectively.

Methods can be marked as `@secured`. A secured method is adorned with
other methods which are called to establish whether the secured method
is allowed to be read or written respectively.  (These `check` methods
should return True if the right is allowed, else False.)

An Event can infer its access rights directly from the access rights 
applicable to the method used as its `action`.  

If a programmer somehow mistakenly does call such a secured method
when it is not allowed, an exception will be raised.


.. literalinclude:: ../../reahl/doc/examples/features/access/access.py



