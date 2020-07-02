.. Copyright 2020 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Input| replace:: :class:`~reahl.web.ui.Input`
.. |PrimitiveInput| replace:: :class:`~reahl.web.ui.PrimitiveInput`
.. |Form| replace:: :class:`~reahl.web.ui.Form`
.. |add_alert_for_domain_exception| replace:: :meth:`~reahl.web.bootstrap.forms.FormLayout.add_alert_for_domain_exception`

.. |UserInterface| replace:: :class:`~reahl.web.fw.UserInterface`
.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |define_error_view| replace:: :meth:`~reahl.web.fw.UserInterface.define_error_view`
.. |assemble| replace:: :meth:`~reahl.web.fw.UserInterface.assemble`
.. |HTML5Page| replace:: :class:`~reahl.web.ui.HTML5Page`
.. |Bookmark| replace:: :class:`~reahl.web.fw.Bookmark` 

.. |ErrorWidget| replace:: :class:`~reahl.web.fw.ErrorWidget`
.. |get_widget_bookmark_for_error| replace:: :meth:`~reahl.web.bootstrap.page.BootstrapHTMLErrorPage.get_widget_bookmark_for_error`
.. |ErrorMessageBox| replace:: :meth:`~reahl.web.bootstrap.page.ErrorMessageBox`





Customised error views
======================

.. sidebar:: Examples in this section

   - howtos.customisingerrorpages

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


The default error view
----------------------

The `howtos.customisingerrorpages` example simulates a programming error when 
you click on 'Submit'. 

The config setting `reahlsystem.debug = True` in `reahl.config.py` controls
how an uncaught Exception in your application is handled.

If `reahlsystem.debug = True`, then a stacktrace is shown.

If `reahlsystem.debug = False`, your application renders a default error view 
derived from the root |UserInterface| (set in `web.site_root` config in 
reahl.web.config.py).

The default error view is sufficient in most cases.

This example has its `web.site_root` set to `BreakingUIWithBuiltInErrorPage` which
demonstrates the default behaviour:

.. literalinclude:: ../../reahl/doc/examples/howtos/customisingerrorpages/customisingerrorpages.py
   :pyobject: BreakingUIWithBuiltInErrorPage


Supplying a completely customised error view
--------------------------------------------

Uncomment `web.site_root = 'BreakingUIWithCustomErrorPage'` in `etc/web.config.py` to see
the example customised error view.

BreakingUIWithCustomErrorPage is a different |UserInterface| which defines a customised 
error view by calling |define_error_view| in its |assemble|\:

.. literalinclude:: ../../reahl/doc/examples/howtos/customisingerrorpages/customisingerrorpages.py
   :pyobject: BreakingUIWithCustomErrorPage

The |Widget| used in the call to |define_error_view| replaces the entire |HTML5Page|
when the error view is shown. On your |Widget|, provide a class-side method with the 
same name and signature as |get_widget_bookmark_for_error|. In your |get_widget_bookmark_for_error|, 
return a page-internal |Bookmark| to an instance of your |Widget| which is parameterised 
to display the given error message.

|ErrorWidget| or |ErrorMessageBox| are handy to use for this purpose:

.. literalinclude:: ../../reahl/doc/examples/howtos/customisingerrorpages/customisingerrorpages.py
   :pyobject: CustomErrorPage
