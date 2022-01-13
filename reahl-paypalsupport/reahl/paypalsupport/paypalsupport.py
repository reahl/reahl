# Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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


"""
import sys
import json
import logging

from reahl.component.context import ExecutionContext
from reahl.component.exceptions import DomainException
from reahl.sqlalchemysupport import Base, Session
from reahl.web.fw import RemoteMethod, JsonResult, CannotCreate
from reahl.web.ui import HTMLWidget, LiteralHTML
from reahl.web.bootstrap.ui import Div
from reahl.component.modelinterface import Field, exposed, Event, Action, IntegerField, JsonField
from reahl.sqlalchemysupport.sqlalchemysupport import Base, session_scoped


from paypalcheckoutsdk.orders import OrdersCaptureRequest, OrdersCreateRequest
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersGetRequest
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalhttp.serializers.json_serializer import Json
from sqlalchemy import Column, Integer, String, Unicode

from reahl.paypalsupport.paypallibrary import PayPalJS


class PayPalClientCredentials:
    def __init__(self, paypal_client_id, paypal_client_secret, sandboxed):
        self.client_id = paypal_client_id
        self.client_secret = paypal_client_secret
        self.sandboxed = sandboxed


class PayPalOrder(Base):

    __tablename__ = 'payment_paypal_order'

    id = Column(Integer, primary_key=True)
    paypal_id = Column(String(length=20), unique=True, nullable=True)
    status = Column(String(length=10))
    json_string = Column(Unicode)

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
                    'captureOrderUrl': str(capture_order_url)
                  }
        return super().get_js(context=context) + \
            ['$("#%s").paypalbuttonspanel(%s);' % (self.css_id, json.dumps(options))]

    def create_order(self):
        return self.order.create_on_paypal(self.credentials)

    def capture_order(self):
        return self.order.capture_on_paypal(self.credentials)



