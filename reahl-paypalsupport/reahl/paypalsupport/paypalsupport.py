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
from reahl.web.ui import HTMLWidget
from reahl.web.bootstrap.ui import Div
from reahl.component.modelinterface import Field, exposed, Event, Action, IntegerField
from reahl.sqlalchemysupport.sqlalchemysupport import Base, session_scoped


from paypalcheckoutsdk.orders import OrdersCaptureRequest
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersGetRequest
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalhttp.serializers.json_serializer import Json
from paypalhttp.http_error import HttpError
from sqlalchemy import Column, Integer, String, Unicode


class PayPalRemoteEnvironment:
    def __init__(self, paypal_client_id, paypal_client_secret, live_environment=False):
        self.client_id = paypal_client_id
        self.cient_secret = paypal_client_secret
        self.live_environment = live_environment

    @property
    def http_client(self):
        if self.live_environment:
            env = LiveEnvironment(client_id=self.client_id, client_secret=self.client_secret)
        else:
            env = SandboxEnvironment(client_id=self.client_id, client_secret=self.client_secret)
        return PayPalHttpClient(env)

class PayPal:
    def __init__(self, paypal_remote_environment):
        self.remote_environment = paypal_remote_environment

    def object_to_json(self, json_data):
        result = {}
        if sys.version_info[0] < 3:
            itr = json_data.__dict__.iteritems()
        else:
            itr = json_data.__dict__.items()
        for key,value in itr:
            # Skip internal attributes.
            if key.startswith("__") or key.startswith("_"):
                continue
            result[key] = self.array_to_json_array(value) if isinstance(value, list) else\
                        self.object_to_json(value) if not self.is_primittive(value) else\
                         value
        return result

    def array_to_json_array(self, json_array):
        result = []
        if isinstance(json_array, list):
            for item in json_array:
                result.append(self.object_to_json(item) if  not self.is_primittive(item) \
                              else self.array_to_json_array(item) if isinstance(item, list) else item)
        return result

    def is_primittive(self, data):
        return isinstance(data, str) or isinstance(data, int)

    @property
    def debug(self):
        return ExecutionContext.get_context().config.reahlsystem.config

    def create_order(self, json_order):
        request = OrdersCreateRequest()
        request.headers['prefer'] = 'return=representation'
        request.request_body(json_order)

        if self.debug:
            logging.debug('Paypal order: %s' % json_order)

        response = self.remote_environment.http_client.execute(request)

        if self.debug:
            self.log_paypal_create_response(response)

        return response

    def capture_order(self, order_id):
        capture_request = OrdersCaptureRequest(order_id)
        capture_response = self.remote_environment.http_client.execute(capture_request)

        if self.debug:
            self.log_paypal_capture_response(capture_response)

        return capture_response

    def log_paypal_create_response(self, response):
        logging.debug('Paypal Status Code: ', response.status_code)
        logging.debug('Paypal Status: ', response.result.status)
        logging.debug('Paypal Order ID: ', response.result.id)
        logging.debug('Paypal Intent: ', response.result.intent)
        logging.debug('Paypal Links:')
        for link in response.result.links:
            logging.debug('\t{}: {}\tCall Type: {}'.format(link.rel, link.href, link.method))
        logging.debug('Paypal Total Amount: {} {}'.format(response.result.purchase_units[0].amount.currency_code,
                                                          response.result.purchase_units[0].amount.value))
        json_response = self.object_to_json(response.result)
        logging.debug("Paypal response: ", json.dumps(json_response, indent=4))


    def log_paypal_capture_response(self, capture_response):
        logging.debug('Status Code: ', capture_response.status_code)
        logging.debug('Status: ', capture_response.result.status)
        logging.debug('Order ID: ', capture_response.result.id)
        logging.debug('Links: ')
        for link in capture_response.result.links:
            logging.debug('\t{}: {}\tCall Type: {}'.format(link.rel, link.href, link.method))
        logging.debug('Capture Ids: ')
        for purchase_unit in capture_response.result.purchase_units:
            for capture in purchase_unit.payments.captures:
                logging.debug('\t', capture.id)
        json_data = self.object_to_json(capture_response.result)
        logging.debug("json_data: ", json.dumps(json_data, indent=4))


class PayPalOrder(Base):

    __tablename__ = 'payment_paypal_order'

    id = Column(Integer, primary_key=True)
    paypal_id = Column(String(length=20), unique=True, nullable=True)
    status = Column(String(length=10))
    approve_link = Column(Unicode)
    json_string = Column(Unicode)


    def create_on_paypal(self, paypal_remote_environment):
        paypal = PayPal(paypal_remote_environment)
        try:
            response = paypal.create_order(json.loads(self.json_string))
            if response.status_code != 201:
                raise DomainException(message='Could not connect with Paypal: %s' % response.result.status)
            self.status = response.result.status
            self.paypal_id = response.result.id
            [ self.approve_link ] = [ link.href for link in response.result.links if link.rel == 'approve' ]
            return response.result.dict()
        except HttpError as ex:
            raise Exception(str(ex))

    def capture_on_paypal(self, paypal_remote_environment):
        paypal = PayPal(paypal_remote_environment)
        response = paypal.capture_order(self.paypal_id)
        if response.status_code not in [200, 201]:
            raise DomainException(message='Could not connect with Paypal, HTTP error code: %s' % response.status_code)

        logging.debug('Updating status of order to: %s' % response.result.status)
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


class JsonField(Field):
    def parse_input(self, unparsed_input):
        return json.loads(unparsed_input if unparsed_input != '' else 'null')

    def unparse_input(self, parsed_value):
        return json.dumps(parsed_value)


class PayPalButtonsPanel(HTMLWidget):
    def __init__(self, view, css_id, order, paypal_remote_environment):
        super().__init__(view)
        self.set_as_security_sensitive()
        self.set_html_representation(self.add_child(Div(view)))
        self.set_id(css_id)
        self.paypal_remote_environment = paypal_remote_environment
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
        return self.order.create_on_paypal(self.paypal_remote_environment)

    def capture_order(self):
        return self.order.capture_on_paypal(self.paypal_remote_environment)



