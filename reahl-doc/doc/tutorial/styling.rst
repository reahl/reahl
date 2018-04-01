.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |Layout| replace:: :class:`~reahl.web.fw.Layout`
.. |HTML5Page| replace:: :class:`~reahl.web.ui.HTML5Page`
.. |Navbar| replace:: :class:`~reahl.web.bootstrap.navbar.Navbar`
.. |ResponsiveLayout| replace:: :class:`~reahl.web.bootstrap.navbar.ResponsiveLayout`
.. |Container| replace:: :class:`~reahl.web.bootstrap.grid.Container`


                         
Layout and styling
==================

.. sidebar:: Examples in this section

   - tutorial.pagelayout

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Reahl comes with |Widget|\s. You build your own by adding these
together to form more complicated |Widget|\s that add up to a complete
user interface.

Use |Widget|\s from :doc:`the bootstrap package
<../web/bootstrap/index>` for a styled site.

Lets start by adding a |Navbar| to the page:

.. literalinclude:: ../../reahl/doc/examples/tutorial/pagelayout/pagelayout.py

.. sidebar:: Behind the scenes

   Reahl uses `Bootstrap <http://getbootstrap.com/>`_ to deal
   with layout issues.

A |Layout| is used to change what a |Widget| looks like. The
|ResponsiveLayout| makes the |Navbar| collapse automatically on
devices smaller than medium (md) size.

Note how |ResponsiveLayout| is also used to add brand text and other
contents to the |Navbar|.

The |Container| |Layout| used on the body of our |HTML5Page| gives the page
some margins and is necessary for Bootstrap to work.


.. note:: Custom styling

   We dont want you to think of css anymore, but.. if you really want
   to you can add your own css too:
   
   Serve your own static files from a directory added using
   :meth:`~reahl.web.fw.UserInterface.define_static_directory` inside
   your :meth:`~reahl.web.fw.UserInterface.assemble`.

   .. code-block:: python

      self.define_static_directory('/css')


   To use your own CSS, add a link to such a static file on
   your HTML5Page subclass. For example in the `__init__`
   of your class, put:

   .. code-block:: python

      self.head.add_css(Url('/css/own.css'))


