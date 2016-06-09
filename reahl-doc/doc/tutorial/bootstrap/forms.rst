.. Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.


Layout of forms
===============

.. sidebar:: Examples in this section

   - tutorial.addressbook2bootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

.. |Form| replace:: :class:`~reahl.web.bootstrap.forms.Form`
.. |FormLayout| replace:: :class:`~reahl.web.bootstrap.forms.FormLayout`

The basics of form layout
-------------------------

Creating a good-looking Form is a task with many facets. Inputs need
to be labelled, their validation error messages need to be put
somewhere and all of this must be neatly arranged.

To achieve this, the contents of a |Form| are added using a
|FormLayout|.

A |FormLayout| need not be applied directly to a |Form| itself. It can
also be applied to, say, a :class:`~reahl.web.bootstrap.ui.Div` which
is a child of a |Form|. This makes the arrangement quite flexible,
since you could have different parts of a |Form| that are laid out
using different |FormLayout|\s or even by different *types* of
|FormLayout|.

In the styled version of our address book example below, a
:class:`~reahl.web.bootstrap.forms.FieldSet` is used to group a number of
Inputs together under a heading. Inputs are added to it by using a
|FormLayout|. 

This produces a simple Bootstrap-styled form, with labels and inputs
stacked on top of one another, filling the whole width of their parent
regardless of the size of the user's device. The |FormLayout| also
renders validation error messages in the right place when necessary
and highlights invalid user input by changing the colour of the
relevant Input.

.. literalinclude:: ../../../reahl/doc/examples/tutorial/addressbook2bootstrap/addressbook2bootstrap.py
   :pyobject: AddAddressForm

:class:`~reahl.web.bootstrap.forms.FormLayout.add_input()` has a number
of options to help you control how Inputs are added.

Here is a screen shot of the form:

.. figure:: ../../_build/screenshots/bootstrapform.png
  :align: center
  :width: 70%
  :alt: A screenshot of the form.

Other ways of laying out forms
------------------------------

The :class:`~reahl.web.bootstrap.forms.InlineFormLayout` arranges Inputs
and their labels flowing next to each other like words in text, whereas
:class:`~reahl.web.bootstrap.forms.GridFormLayout` arranges Labels in
underneath each other in one column and their corresponding Inputs in 
another column.




