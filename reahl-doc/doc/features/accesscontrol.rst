.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Access control example
======================

Fields are not only used for validation -- amongst other things they
are also used to declare who is allowed to see or change the data
items they represent. This information is used to automatically adapt
what is rendered on the screen to prevent editing or visibility when
necessary.

Similar access control features are present for Events controlling the
visibility or state of rendered Buttons.

The example program presented here renders a single page with an
input and a button. Each of these elements are restricted in some way:

 - The input labelled `Greyed out` is for a Field that is allowed to be
   *read* but not *written* (ie, changed).
 - The `Greyed out button` is greyed out for similar reasons: the user
   may see the button, but is not allowed to execute its action.

(Of course, Inputs that are not allowed to be *read* or *written* 
will simply not be rendered at all.)

 .. figure:: ../_build/screenshots/access.png
    :align: center
    :alt: An screenshot showing a greyed out input and disabled buttons.

Here is the example source code, followed by some explanation:

.. literalinclude:: ../../reahl/doc/examples/features/access/access.py


Notice how one specifies an Action for the framework to call in order
to determine whether a Field is readable or writable. These Actions
should return True or False to indicate whether the user has the
corresponding right or not, respectively (obviously you won't
hard-code them like in this example...).

Methods can be marked as `@secured`. A secured method is adorned with
similar checks which are called to establish whether the secured method
is allowed to be read (Buttons will be visible) or written (Buttons
will be enabled) respectively.  (These `check` methods
return True if the right is allowed, else False.)

An Event can infer its access rights directly from the access rights 
applicable to the method used as its `action`.  

If a programmer somehow mistakenly does call such a secured method
when it is not allowed, an exception will be raised.





