.. Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.


Enabling Bootstrap
==================

.. sidebar:: Examples in this section

   - tutorial.addressbook2bootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


In order to use Bootstrap Widgets and Layouts, you need to enable
Bootstrap in your web.config.py.

Note that you cannot use Bootstrap-based Widgets *with* older Pure or
specially styled Reahl Widgets in the same project. If you enable
Bootstrap, the others will cease to work correctly.

In order to enable Bootstrap, call
:meth:`~reahl.web.libraries.LibraryIndex.enable_experimental_bootstrap()`
in your ``etc/web.config.py`` file:


.. literalinclude:: ../../../reahl/doc/examples/tutorial/addressbook2bootstrap/etc/web.config.py

In examples thus far, you will often see a keyword argument
`style='basic'` passed to a :class:`reahl.web.ui.HTML5Page`\. When
using Bootstrap, refrain from doing this and ensure that you import
all Widgets from modules underneath :mod:`reahl.web.bootstrap`. 

When using Bootstrap, always import basic HTML Widgets from
:mod:`reahl.web.bootstrap.ui` instead of from :mod:`reahl.web.ui`.
This ensures you will get customised, stylised versions of Widgets
where necessary -- Widgets that are unchanged from :mod:`reahl.web.ui`
are also available via :mod:`reahl.web.bootstrap.ui` so that you don't
need to differentiate.

