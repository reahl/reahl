.. Copyright 2013, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |UrlBoundView| replace:: :class:`~reahl.web.fw.UrlBoundView`
.. |View| replace:: :class:`~reahl.web.fw.View`
.. |HTMLElement| replace:: :class:`~reahl.web.ui.HTMLElement`
.. |Bookmark| replace:: :class:`~reahl.web.fw.Bookmark`
.. |Div| replace:: :class:`~reahl.web.bootstrap.ui.Div`
.. |Nav| replace:: :class:`~reahl.web.bootstrap.navs.Nav`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |SequentialPageIndex| replace:: :class:`~reahl.web.bootstrap.pagination.SequentialPageIndex`
.. |PageIndex| replace:: :class:`~reahl.web.bootstrap.pagination.PageIndex`
.. |PagedPanel| replace:: :class:`~reahl.web.bootstrap.pagination.PagedPanel`
.. |PageMenu| replace:: :class:`~reahl.web.bootstrap.pagination.PageMenu`
.. |AnnualPageIndex| replace:: :class:`~reahl.web.bootstrap.pagination.AnnualPageIndex`



Paging long lists
=================

.. sidebar:: Examples in this section

   - howtos.pagerbootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>



The `howtos.pagerbootstrap` example lets a user page though a very
long list of Addresses, displaying only a managable number at a time.

Three objects play a role in this scenario:

* A |SequentialPageIndex| breaks the long list of Addresses into
  separate chunks.
* AddressList is a |PagedPanel|\---it displays the
  appropriate chunk of Addresses (its
  :meth:`~reahl.web.bootstrap.pagination.PagedPanel.current_contents`).
* An accompanying |PageMenu| allows the user to navigate.

.. literalinclude:: ../../reahl/doc/examples/howtos/pagerbootstrap/pagerbootstrap.py
   :pyobject: AddressBookPanel

Since AddressList is a |PagedPanel|, it automatically refreshes and
computes its :attr:`~reahl.web.bootstrap.pagination.PagedPanel.current_contents` based on the given
|SequentialPageIndex|.

.. literalinclude:: ../../reahl/doc/examples/howtos/pagerbootstrap/pagerbootstrap.py
   :pyobject: AddressList

Other implementations of |PageIndex| are possible, such as
|AnnualPageIndex| which arranges all items with the same year
together.

 .. figure:: pager.png
    :align: center

