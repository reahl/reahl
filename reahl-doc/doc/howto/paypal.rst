.. Copyright 2022 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |@session_scoped| replace:: :func:`~reahl.sqlalchemysupport.sqlalchemysupport.session_scoped`
.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |UserInterface| replace:: :class:`~reahl.web.fw.UserInterface`
.. |UrlBoundView| replace:: :class:`~reahl.web.fw.UrlBoundView`
.. |Transition| replace:: :class:`~reahl.web.fw.Transition`
.. |Configuration| replace:: :class:`~reahl.component.config.Configuration`
.. |PayPalClientCredentials| replace:: :class:`~reahl.paypalsupport.paypalsupport.PayPalClientCredentials`
.. |PayPalButtonsPanel| replace:: :class:`~reahl.paypalsupport.paypalsupport.PayPalButtonsPanel`
.. |PayPalOrder| replace:: :class:`~reahl.paypalsupport.paypalsupport.PayPalOrder`


Add a PayPal payment option to your page
========================================

.. sidebar:: Examples in this section

   - howtos.paymentpaypal

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Overview
--------

This example shows how to process payments via PayPal. It contains a simplistic ShoppingCart which serves 
to allow a user to select items to buy. This happens on the home page of the example. When the user is satisfied
with their selections, the user clicks on "Pay" which transitions them to another "Summary" page on which an overview
of the order is shown and where a |PayPalButtonsPanel| is displayed.

Clicking on the PayPal button here ferries the user to PayPal and finally returns to the Summary page to show the status
of the order after payment.

.. uml:: paypal.puml


Create a ShoppingCart
---------------------

Create a |@session_scoped| ShoppingCart object to collect all the items you want to buy. It has a `pay` method which 
creates a |PayPalOrder| when called.

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/paymentpaypal.py
   :pyobject: ShoppingCart
   :end-before: def as_json

Create the order JSON
---------------------

Also add an `as_json` method which represents your order as a dictionary that conforms to 
`PayPal's JSON specification for creating orders <https://developer.paypal.com/api/orders/v2/#orders-create-request-body>`_ and
with "intent" set to "CAPTURE". 

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/paymentpaypal.py
   :pyobject: ShoppingCart.as_json


Create the PurchaseForm
-----------------------

Create a PurchaseForm class which is the user interface of your simple shopping cart. Wire its only button to the 
ShoppingCart's `pay` event so that a |PayPalOrder| is created when clicked.

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/paymentpaypal.py
   :pyobject: PurchaseForm


Create the PurchaseSummary
--------------------------

Create a Form to display the final order details. This |Widget| should contain a |PayPalButtonsPanel|, but only if the order
is ready to be paid. The same |Widget| is again displayed upon return from PayPal, and in that case only display the order
success message.

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/paymentpaypal.py
   :pyobject: PurchaseSummary
   :end-before: def get_credentials_from_configuration

.. note:: 

   Notice that in this example is a call to `get_credentials_from_configuration`, and a commented-out call to `get_credentials_hardcoded`.
   
   For now, comment out the call to `get_credentials_from_configuration` and use the one to `get_credentials_hardcoded`.


Combine it all in a |UserInterface|
-----------------------------------

Add Purchaseform to your |UserInterface| on the '/' |UrlBoundView| and PurchaseSummary on the '/order_summary' |UrlBoundView|.
Then define |Transition|\s between the two.

There is no need to add a |Transition| to PayPal. 

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/paymentpaypal.py
   :pyobject: ShoppingUI
  

Obtain sandbox credentials at PayPal
------------------------------------

At this point (provided you commented out the use of `get_credentials_from_configuration`) you can run the example up to a point.

To be able to interact with PayPal, `register as a developer at PayPal <https://developer.paypal.com/tools/sandbox/accounts/>`_


Create Configuration for your PayPal merchant account
-----------------------------------------------------

Create a |Configuration| for your project in which you can supply the credentials for interacting with PayPal while avoiding
hardcoding these in the source code of your app.

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/paymentpaypal.py
   :pyobject: PaymentPayPalConfig

Remember to also include this |Configuration| in your `setup.cfg`:

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/setup.cfg
   :language: ini

Create a `paymentpaypal.config.py` file in your configuration directory, with the necessary settings:

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/etc/paymentpaypal.config.py

.. note:: 

   Here, the config file is coded to read the settings from environment variables to make it easy for us to test, but
   you can hard-code the settings for yourself in the config file.


Update PurchaseSummary to read this configuration
-------------------------------------------------

In PurchaseSummary, write `get_credentials_from_configuration` to read the config and return a |PayPalClientCredentials| object
with the result. (Remember to also update the commented-out code to call this method.)

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/paymentpaypal.py
   :pyobject: PurchaseSummary.get_credentials_from_configuration


Congratulations!
----------------

You should now be able to make payments to the PayPal sandbox environment using the example.
