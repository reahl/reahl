import decimal
import json

from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, UnicodeText, Numeric, ForeignKey

from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import Alert, P
from reahl.web.bootstrap.forms import Form, TextInput, Button, FormLayout, SelectInput
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.component.modelinterface import IntegerField, ChoiceField, Choice, Field, ExposedNames, Event, Action, Not, NumericField
from reahl.component.config import Configuration, ConfigSetting
from reahl.component.context import ExecutionContext
from reahl.sqlalchemysupport import Session, Base, session_scoped
from reahl.paypalsupport.paypalsupport import PayPalOrder, PayPalButtonsPanel, PayPalClientCredentials


class PaymentPayPalConfig(Configuration):
    filename = 'paymentpaypal.config.py'
    config_key = 'paymentpaypal'

    client_id = ConfigSetting(description='The PayPal client ID that needs to receive funds from payments')
    client_secret = ConfigSetting(description='The PayPal client secret')
    sandboxed = ConfigSetting(default=True, description='If False, use the PayPal live environment instead of sandboxed', dangerous=True)



class MainPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.use_layout(PageLayout(document_layout=Container(), 
                                   contents_layout=ColumnLayout(ColumnOptions('main', size=ResponsiveSize(md=4))).with_slots()))
                                   

class PurchaseSummary(Form):
    def __init__(self, view, shopping_cart):
        super().__init__(view, 'summary')
        self.use_layout(FormLayout())
        paypal_order = shopping_cart.paypal_order

        if self.exception:
            self.layout.add_alert_for_domain_exception(self.exception)

        self.add_child(P(view, text='%s: %s' % (shopping_cart.fields.item_name.label, shopping_cart.item_name)))
        self.add_child(P(view, text='%s: %s' % (shopping_cart.fields.quantity.label, shopping_cart.quantity)))
        self.add_child(P(view, text='%s: %s' % (shopping_cart.fields.price.label, shopping_cart.price)))
        self.add_child(P(view, text='%s: %s' % (shopping_cart.fields.currency_code.label, shopping_cart.currency_code)))

        self.add_child(Alert(view, 'Your order(%s) status: %s (%s)' % (paypal_order.id, paypal_order.status, paypal_order.paypal_id), 'secondary'))

        if paypal_order.is_due_for_payment:
            credentails = self.get_credentials_from_configuration()
            #credentails = self.get_credentials_hardcoded()
            self.add_child(PayPalButtonsPanel(view, 'paypal_buttons', shopping_cart.paypal_order, credentails, shopping_cart.currency_code))
        elif paypal_order.is_paid:
            self.add_child(Alert(view, 'Your order has been paid successfully', 'primary'))
            self.add_child(Button(self, shopping_cart.events.clear_event, style='primary'))
        else:
            self.add_child(Alert(view, 'We could not complete your payment at PayPal (Order status: %s)' % paypal_order.status, 'warning'))

    def get_credentials_hardcoded(self):
        return PayPalClientCredentials('test', 'invalidpassword', True)

    def get_credentials_from_configuration(self):
        config = ExecutionContext.get_context().config
        paypal_client_id = config.paymentpaypal.client_id
        paypal_client_secret = config.paymentpaypal.client_secret
        sandboxed = config.paymentpaypal.sandboxed
        return PayPalClientCredentials(paypal_client_id, paypal_client_secret, sandboxed)



class PurchaseForm(Form):
    def __init__(self, view, shopping_cart):
        super().__init__(view, 'purchase')
        self.use_layout(FormLayout())

        if self.exception:
            self.layout.add_alert_for_domain_exception(self.exception)

        self.layout.add_input(TextInput(self, shopping_cart.fields.item_name))
        self.layout.add_input(TextInput(self, shopping_cart.fields.quantity))
        self.layout.add_input(TextInput(self, shopping_cart.fields.price))
        self.layout.add_input(SelectInput(self, shopping_cart.fields.currency_code))

        self.add_child(Button(self, shopping_cart.events.pay_event, style='primary'))



@session_scoped
class ShoppingCart(Base):
    __tablename__ = 'paymentpaypal_shoppingcart'

    id = Column(Integer, primary_key=True)
    item_name = Column(UnicodeText)
    quantity = Column(Integer)
    price = Column(Numeric(precision=4, scale=2))
    currency_code = Column(String(3))
    paypal_order_id = Column(Integer, ForeignKey(PayPalOrder.id), nullable=True)
    paypal_order = relationship(PayPalOrder)

    fields = ExposedNames()
    fields.item_name = lambda i: Field(label='Item name')
    fields.quantity = lambda i: IntegerField(min_value=1, max_value=10, label='Quantity')
    fields.price = lambda i: NumericField(min_value=1, label='Price')
    fields.currency_code = lambda i: ChoiceField([Choice('USD', Field(label='USD')),
                                                  Choice('EUR', Field(label='EUR'))],
                                                 label='Currency')

    events = ExposedNames()
    events.pay_event = lambda i: Event(label='Pay', action=Action(i.pay))
    events.clear_event = lambda i: Event(label='Continue shopping', action=Action(i.clear))

    def pay(self):
        json_dict = self.as_json()
        print(json_dict)
        order = PayPalOrder(json_string=json.dumps(json_dict))
        Session.add(order)
        self.paypal_order = order

    def clear(self):
        self.paypal_order = None

    def as_json(self):
        tax_rate = decimal.Decimal('0.15')
        invoice_id = id(self)

        item_price = self.price
        item_tax = round(self.price * tax_rate, 2)
        item_quantity = self.quantity
        item_name = self.item_name

        order_pre_tax_total = item_quantity*item_price
        order_total_tax = item_quantity*item_tax
        order_total_including_tax = item_quantity*(item_price+item_tax)

        brand_name = 'My Example company'
        return \
        {
            "intent": "CAPTURE",

            "purchase_units": [
                {
                    "description": item_name,
                    "invoice_id": invoice_id,
                    "soft_descriptor": brand_name,
                    "amount": {
                        "currency_code": self.currency_code,
                        "value": str(order_total_including_tax),
                        "breakdown": {
                            "item_total": {
                                "currency_code": self.currency_code,
                                "value": str(order_pre_tax_total)
                            },
                            "tax_total": {
                                "currency_code": self.currency_code,
                                "value": str(order_total_tax)
                            },
                        }
                    },
                    "items": [
                        {
                            "name": item_name,
                            "unit_amount": {
                                "currency_code": self.currency_code,
                                "value": str(item_price)
                            },
                            "tax": {
                                "currency_code": self.currency_code,
                                "value": str(item_tax)
                            },
                            "quantity": str(item_quantity),
                            "category": "DIGITAL_GOODS"
                        },

                    ]

                }
            ]
        }


class ShoppingUI(UserInterface):
    def assemble(self):
        shopping_cart = ShoppingCart.for_current_session()

        home = self.define_view('/', title='Paypal Example')
        home.set_slot('main', PurchaseForm.factory(shopping_cart))

        order_summary_page = self.define_view('/order_summary', title='Order Summary')
        order_summary_page.set_slot('main', PurchaseSummary.factory(shopping_cart))

        self.define_transition(shopping_cart.events.pay_event, home, order_summary_page)
        self.define_transition(shopping_cart.events.clear_event, order_summary_page, home)

        self.define_page(MainPage)



