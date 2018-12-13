.. Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved.


Programmatic arguments
======================

.. sidebar:: Examples in this section

   - web.xxxx

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Programmatic arguments
----------------------

If you pass a value to a keyword argument of |define_view| that is *not* a |Field|,
it is passed unchanged though to a matching keyword argument to the `.assemble` 
of your |UrlBoundView|.

For example, the `.assemble()` of a particular |UrlBoundView| may need
access to a :class:`~reahl.web.fw.Bookmark` which is computed inside
the `.assemble()` of its |UserInterface|.

.. code::

   edit = self.define_view('/edit', view_class=EditView, address_id=IntegerField(), some_bookmark=a_bookmark)


.. code::

   def assemble(self, address_id=None, some_bookmark=None):
