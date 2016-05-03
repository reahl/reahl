.. Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.


Layout of forms
===============

.. sidebar:: Examples in this section

   - tutorial.addressbook2bootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


The basics of form layout
-------------------------

Creating a good-looking Form is a task with many facets. Inputs need
to be labelled, their validation error messages need to be put
somewhere and all of this must be neatly arranged.

To achieve this, the contents of a
:class:`~reahl.web.bootstrap.ui.Form` are added using a
:class:`~reahl.web.bootstrap.ui.FormLayout`.

A :class:`~reahl.web.bootstrap.ui.FormLayout` need not be applied
directly to a :class:`~reahl.web.bootstrap.ui.Form` itself. It can
also be applied to, say, a :class:`~reahl.web.bootstrap.ui.Div` which
is a child of a :class:`~reahl.web.bootstrap.ui.Form`. This makes the
arrangement quite flexible, since you could have different parts of a
:class:`~reahl.web.bootstrap.ui.Form` that are laid out using
different :class:`~reahl.web.bootstrap.ui.FormLayout`\s or even
by different *types* of :class:`~reahl.web.bootstrap.ui.FormLayout`.

In the styled version of our address book example below, a
:class:`~reahl.web.bootstrap.ui.FieldSet` is used to group a number of
Inputs together under a heading. Inputs are added to it by using a
:class:`~reahl.web.bootstrap.ui.FormLayout`. 

This produces a simple Bootstrap-styled form, with labels and inputs stacked
on top of one another, filling the whole width of their parent
regardless of the size of the user's device. The
:class:`~reahl.web.bootstrap.ui.FormLayout` also renders validation
error messages in the right place when necessary and highlights invalid
user input by changing the colour of the relevant Input.

.. literalinclude:: ../../../reahl/doc/examples/tutorial/addressbook2bootstrap/addressbook2bootstrap.py
   :pyobject: AddAddressForm

:class:`~reahl.web.bootstrap.ui.FormLayout.add_input()` has a number
of options to help you control how Inputs are added.

TODO: we need a test that produces a screenshot here... to show what it looks like


Other ways of laying out forms
------------------------------

The :class:`~reahl.web.bootstrap.ui.InlineFormLayout` arranges Inputs
and their labels flowing next to each other, whereas
:class:`~reahl.web.bootstrap.ui.GridFormLayout` allows you to put
Inputs and their labels arranged in columns that are sized differently
depending on the size of the device used to look at the page.

TODO: More screenshots? With examples of each and even mixing them?



