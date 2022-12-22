.. Copyright 2013, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |UrlBoundView| replace:: :class:`~reahl.web.fw.UrlBoundView`
.. |View| replace:: :class:`~reahl.web.fw.View`
.. |HTMLElement| replace:: :class:`~reahl.web.ui.HTMLElement`
.. |Bookmark| replace:: :class:`~reahl.web.fw.Bookmark`
.. |Div| replace:: :class:`~reahl.web.bootstrap.ui.Div`
.. |Nav| replace:: :class:`~reahl.web.bootstrap.navs.Nav`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |ExposedNames| replace:: :class:`~reahl.component.modelinterface.ExposedNames`
.. |SequentialPageIndex| replace:: :class:`~reahl.web.bootstrap.pagination.SequentialPageIndex`
.. |PageIndex| replace:: :class:`~reahl.web.bootstrap.pagination.PageIndex`
.. |PagedPanel| replace:: :class:`~reahl.web.bootstrap.pagination.PagedPanel`
.. |PageMenu| replace:: :class:`~reahl.web.bootstrap.pagination.PageMenu`
.. |AnnualPageIndex| replace:: :class:`~reahl.web.bootstrap.pagination.AnnualPageIndex`




Refreshing Widgets using query_arguments
========================================

.. sidebar:: Examples in this section

   - howtos.ajaxbootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>



You can build a :class:`~reahl.web.fw.Widget` which gets refreshed
without reloading the entire page.

The `howtos.ajaxbootstrap` example has |Nav| and a |Div|. The
contents of the |Div| changes each time an item is selected on the
|Nav| without reloading the entire page.

Only |HTMLElement|\s can refresh. To let an |HTMLElement| refresh, it
needs arguments and needs to call
:meth:`~reahl.web.ui.HTMLElement.enable_refresh` in its `__init__`
method.

In the example, RefreshedPanel is given arguments in an
|ExposedNames| namespace called
:attr:`~reahl.web.fw.Widget.query_fields`. Each argument is defined by
assigning a callable for it to an attribute of the |ExposedNames|. The
callable is called with an instance as argument and should return
a |Field| describing that argument. The `query_fields` declared on
RefreshedPanel is merged with that on :attr:`~reahl.web.fw.Widget.query_fields`
at runtime:


.. literalinclude:: ../../reahl/doc/examples/howtos/ajaxbootstrap/ajaxbootstrap.py
   :start-at: query_fields = 
   :end-at: query_fields.selected =

This makes the value of `self.selected` available in `RefreshedPanel.__init__` to be
used when generating the RefreshedPanel (`self.selected` is set from
the URL or the default of the |Field|):

.. literalinclude:: ../../reahl/doc/examples/howtos/ajaxbootstrap/ajaxbootstrap.py
   :pyobject: RefreshedPanel
   :end-before: query_fields

A special "in-page" |Bookmark| refers to a |Widget| on the current
|UrlBoundView|, but with different argument values.

Construct such a |Bookmark| for a given value of `selected` by calling
:meth:`~reahl.web.fw.Bookmark.for_widget` with suitable
`query_arguments`. Before using the |Bookmark|, call
:meth:`~reahl.web.fw.Bookmark.on_view` to bind it to the current
|View|.

.. literalinclude:: ../../reahl/doc/examples/howtos/ajaxbootstrap/ajaxbootstrap.py
   :pyobject: RefreshedPanel.get_bookmark

Use such bound |Bookmark|\s as usual:

.. literalinclude:: ../../reahl/doc/examples/howtos/ajaxbootstrap/ajaxbootstrap.py
   :pyobject: HomePanel

.. note:: If a |Widget| declares `query_fields`, it must have a unique css_id.


