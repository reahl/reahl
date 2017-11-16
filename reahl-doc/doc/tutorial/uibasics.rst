.. Copyright 2017 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |View| replace:: :class:`~reahl.web.fw.View`
.. |WidgetFactory| replace:: :class:`~reahl.web.fw.WidgetFactory`


Build a user interface with Widgets
===================================

.. sidebar:: Examples in this section

   - tutorial.addresslist

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


The next step is to change the page to display the list of Addresses in the address book.

Create your own AddressBox |Widget| to display a single Address.

Then add to the page a custom AddressBookPanel |Widget| that contains a nice
heading and many AddressBox instances: one for each Address in our
list.

(To keep things simple for now, hardcode the list of Addresses.)

.. note:: In the definition of the |View|, use a |WidgetFactory| for
   AddressBookPage: the |WidgetFactory| is used to create an
   AddressBookPage each time that URL is visited and only for
   the duration of the request.

.. literalinclude:: ../../reahl/doc/examples/tutorial/addresslist/addresslist.py





