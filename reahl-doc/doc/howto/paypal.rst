.. Copyright 2022 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |PayPalButtonsPanel| replace:: :class:'~reahl.paypalsupport.paypalsupport.PayPalButtonsPanel`
.. |PayPalOrder| replace:: :class:'~reahl.paypalsupport.paypalsupport.PayPalOrder`

Add a PayPal payment option to your page
========================================

.. sidebar:: Examples in this section

   - howtos.paymentpaypal

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>


Add a |PayPalButtonsPanel| to setup standard paypal payments.
The panel displays the `PayPalButton <https://developer.paypal.com/docs/checkout/standard/>_` which makes calls on |PayPalOrder| to facilitate integration
to `PayPal <https://www.paypal.com>_` using the `PayPal REST API <https://developer.paypal.com/api/orders/v2/>_` under the hood.


Here is an example of a PurchaseSummary that shows a PayPal button:

.. literalinclude:: ../../reahl/doc/examples/howtos/paymentpaypal/paymentpaypal.py
   :pyobject: PurchaseSummary

