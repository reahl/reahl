# Copyright 2021, 2022 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Support for payment via PayPal.

.. versionadded: 5.2
"""
import json
import logging

from reahl.component.exceptions import DomainException
from reahl.web.fw import RemoteMethod, JsonResult
from reahl.web.ui import HTMLWidget, LiteralHTML
from reahl.web.bootstrap.ui import Div
from reahl.component.modelinterface import JsonField
from reahl.component.i18n import Catalogue
from reahl.sqlalchemysupport.sqlalchemysupport import Base
from reahl.paypalsupport.paypallibrary import PayPalJS


from paypalcheckoutsdk.orders import OrdersCaptureRequest, OrdersCreateRequest
from paypalcheckoutsdk.orders import OrdersCreateRequest
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from sqlalchemy import Column, Integer, String, UnicodeText

_ = Catalogue('reahl-paypalsupport')

class PayPalClientCredentials:
    """
    Credentials needed to log into PayPal via API.

    :param paypal_client_id: The PayPal API client id of a merchant account.
    :param paypal_client_secret: The PayPal API client secret of a merchant account.
    :param sandboxed: If True, these credentials are for the sandbox environment, otherwise they are for the live environment.
    """
    def __init__(self, paypal_client_id, paypal_client_secret, sandboxed):
        self.client_id = paypal_client_id
        self.client_secret = paypal_client_secret
        self.sandboxed = sandboxed


class PayPalOrder(Base):
    """
    A PayPalOrder is a proxy of an order created on PayPal via its API.

    Create a PayPalOrder to keep track of the process of creating and finalising a matching order on PayPal.

    :keyword json_string: Json string based on `the PayPal specification for orders <https://developer.paypal.com/api/orders/v2/#orders-create-request-body>`_.

    """
    __tablename__ = 'payment_paypal_order'

    id = Column(Integer, primary_key=True)
    paypal_id = Column(String(length=20), unique=True, nullable=True)  #: The ID of the corresponding order on PayPal.
    status = Column(String(length=10))     #: If not None, the status of this order on PayPal's side.
    json_string = Column(UnicodeText)  #: The json specification of how to create this order on PayPal

    def get_http_client(self, credentials):
        if credentials.sandboxed:
            env = SandboxEnvironment(client_id=credentials.client_id, client_secret=credentials.client_secret)
        else:
            env = LiveEnvironment(client_id=credentials.client_id, client_secret=credentials.client_secret)
        return PayPalHttpClient(env)

    def create_on_paypal(self, credentials):
        request = OrdersCreateRequest()
        request.headers['prefer'] = 'return=representation'
        request.request_body(json.loads(self.json_string))

        logging.getLogger(__name__).debug('Create Paypal order: %s' % self.json_string)
        response = self.get_http_client(credentials).execute(request)
        logging.getLogger(__name__).debug('Paypal Status Code: %s', response.status_code)
        logging.getLogger(__name__).debug('Paypal Response: %s', response.result.dict())

        if response.status_code != 201:
            raise DomainException(message='Could not connect with Paypal: %s' % response.result.status)
        self.status = response.result.status
        self.paypal_id = response.result.id
        return response.result.dict()

    def capture_on_paypal(self, credentials):
        capture_request = OrdersCaptureRequest(self.paypal_id)

        logging.getLogger(__name__).debug('Capture Paypal order: %s' % self.paypal_id)
        capture_response = self.get_http_client(credentials).execute(capture_request)
        logging.getLogger(__name__).debug('Paypal Status Code: %s', capture_response.status_code)
        logging.getLogger(__name__).debug('Paypal Response: %s', capture_response.result.dict())

        response = capture_response
        if response.status_code not in [200, 201]:
            raise DomainException(message='Could not connect with Paypal, HTTP error code: %s' % response.status_code)

        logging.getLogger(__name__).debug('Updating status of order to: %s' % response.result.status)
        self.status = response.result.status
        return response.result.dict()

    def is_in_state(self, state):
        return self.status == state

    @property
    def is_due_for_payment(self):
        return self.is_in_state(None) or self.is_in_state('CREATED')

    @property
    def is_paid(self):
        return self.is_in_state('COMPLETED')


class PayPalButtonsPanel(HTMLWidget):
    """
    A Widget containing various buttons supplied by PayPal. Clicking on one of these invokes the payment process at PayPal.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param css_id: A unique ID for this PayPalButtonsPanel.
    :param order: The :class:`PayPalOrder` this PayPalButtonsPanel is for.
    :param credentials: The :class:`PayPalClientCredentials` for the merchant.
    :param currency: A string with `the ISO-4217 3 character currency code <https://en.wikipedia.org/wiki/ISO_4217#Active_codes>`_ which is `supported by PayPal <https://developer.paypal.com/api/rest/reference/currency-codes/#link-currencycodes>`_.

    .. note:: the `currency` of the PayPalButtonsPanel has to correspond with the currency used in the `json_string` of the :class:`PayPalOrder`.
    """
    def __init__(self, view, css_id, order, credentials, currency):
        super().__init__(view)
        self.set_as_security_sensitive()
        self.set_html_representation(self.add_child(Div(view)))
        self.set_id(css_id)
        self.credentials = credentials
        self.add_child(LiteralHTML(view, PayPalJS.get_instance().inline_material(self.credentials, currency)))
        self.order = order
        self.create_order_method = RemoteMethod(view, 'create_order', self.create_order, JsonResult(JsonField()))
        self.view.add_resource(self.create_order_method)
        self.capture_order_method = RemoteMethod(view, 'capture_order', self.capture_order, JsonResult(JsonField()))
        self.view.add_resource(self.capture_order_method)

    def get_js(self, context=None):
        create_order_url = self.create_order_method.get_url().as_network_absolute()
        capture_order_url = self.capture_order_method.get_url().as_network_absolute()
        options = { 'createOrderUrl': str(create_order_url),
                    'captureOrderUrl': str(capture_order_url),
                    'error_announce_text' : _('Error while talking to PayPal:'),
                    'transaction_not_processed_text' : _('Sorry, your transaction could not be processed.')
                  }
        return super().get_js(context=context) + \
            ['$("#%s").paypalbuttonspanel(%s);' % (self.css_id, json.dumps(options))]

    def create_order(self):
        return self.order.create_on_paypal(self.credentials)

    def capture_order(self):
        return self.order.capture_on_paypal(self.credentials)



