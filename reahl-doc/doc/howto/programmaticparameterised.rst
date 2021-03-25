.. Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |define_view| replace:: :meth:`~reahl.web.fw.UserInterface.enable_refresh`
.. |UserInterface| replace:: :class:`~reahl.web.fw.UserInterface`
.. |UrlBoundView| replace:: :class:`~reahl.web.fw.UrlBoundView`
.. |assemble| replace:: :meth:`~reahl.web.fw.UrlBoundView.assemble`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |Bookmark| replace:: :class:`~reahl.web.fw.Bookmark`

Programmatic arguments to an UrlBoundView
=========================================

Usually, an |UrlBoundView| gets its arguments from the current URL. These are passed into 
its |assemble| method by the framework. In some cases it is useful to pass arguments directly 
from your code to |assemble|. 

For example, in the `tutorial.parameterised1` example the parameterised EditView is used in 
`AddressBookUI.assemble`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised1/parameterised1.py
   :pyobject: AddressBookUI

You might want to include a link on EditView for some or other |Bookmark| that is created in your 
code at this point.

If you want to do that, just pass your |Bookmark| as another keyword argument to |define_view|.
Keyword arguments of |define_view| that are *not* instances of |Field| are passed unchanged through 
to matching keyword arguments to the `EditView.assemble`.

So, if you did:

.. code-block::

   edit = self.define_view('/edit', view_class=EditView, address_id=IntegerField(), some_bookmark=a_bookmark)

You can change your |assemble| signature like this:

.. code-block::

   def assemble(self, address_id=None, some_bookmark=None):

... and then your |Bookmark| will be accessible as some_bookmark.