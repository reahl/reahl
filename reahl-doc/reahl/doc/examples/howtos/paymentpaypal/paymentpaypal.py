import decimal
import json

from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, UnicodeText, Numeric, ForeignKey


from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import Alert
from reahl.web.bootstrap.forms import Form, TextInput, Button, FormLayout, SelectInput
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.component.modelinterface import IntegerField, ChoiceField, Choice, Field, exposed, Event, Action, Not, NumericField
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



class MenuPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', size=ResponsiveSize(md=4))).with_slots()
        self.layout.contents.use_layout(contents_layout)



class PurchaseSummary(Form):
    def __init__(self, view, shopping_cart):
        super().__init__(view, 'summary')
        self.use_layout(FormLayout())

        self.layout.add_input(TextInput(self, shopping_cart.fields.item_name))
        self.layout.add_input(TextInput(self, shopping_cart.fields.quantity))
        self.layout.add_input(TextInput(self, shopping_cart.fields.price))
        self.layout.add_input(SelectInput(self, shopping_cart.fields.currency_code))

        paypal_order = shopping_cart.paypal_order


        self.add_child(Alert(view, 'Your order(%s) status: %s (%s)' % (paypal_order.id, paypal_order.status, paypal_order.paypal_id), 'secondary'))

        if paypal_order.is_due_for_payment:
            config = ExecutionContext.get_context().config
            paypal_client_id = config.paymentpaypal.client_id
            paypal_client_secret = config.paymentpaypal.client_secret
            sandboxed = config.paymentpaypal.sandboxed
            credentails = PayPalClientCredentials(paypal_client_id, paypal_client_secret, sandboxed)
            self.add_child(PayPalButtonsPanel(view, 'paypal_buttons', shopping_cart.paypal_order, credentails, shopping_cart.currency_code))
        elif paypal_order.is_paid:
            self.add_child(Alert(view, 'Your order has been paid successfully', 'primary'))
            self.add_child(Button(self, shopping_cart.events.clear_event.with_label('Continue')))
        else:
            self.add_child(Alert(view, 'We could not complete your payment at PayPal (Order status: %s)' % paypal_order.status, 'warning'))


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
        self.define_event_handler(shopping_cart.events.clear_event)
        self.add_child(Button(self, shopping_cart.events.clear_event, style='secondary'))


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

    def as_json(self):
        tax_rate = decimal.Decimal('0.15');
        invoice_id = id(self)

        print('Order:')

        item_price = self.price
        item_tax = round(self.price * tax_rate, 2)
        item_quantity = self.quantity
        item_name = self.item_name

        print('Item:')
        print('item_price: %s' % item_price)
        print('item_quantity: %s' % item_quantity)
        print('item_tax: %s' % item_tax)

        order_pre_tax_total = item_quantity*item_price
        order_total_tax = item_quantity*item_tax
        order_total_including_tax = item_quantity*(item_price+item_tax)
        print('order_pre_tax_total: %s' % order_pre_tax_total)
        print('order_total_tax: %s' % order_total_tax)
        print('order_total_including_tax: %s' % order_total_including_tax)

        brand_name = 'My Example company'
        return \
        {
            "intent": "CAPTURE",

            "application_context": {
                "return_url": "http://localhost:8000/paypal_return",
                "cancel_url": "https://www.example.com",
                "brand_name": brand_name,
                "landing_page": 'NO_PREFERENCE',
                "shipping_preference": "NO_SHIPPING",
                "user_action": "CONTINUE"
            },
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

    @exposed
    def fields(self, fields):
        is_unlocked = Not(Action(self.is_locked))
        fields.item_name = Field(label='Item name', writable=is_unlocked)
        fields.quantity = IntegerField(min_value=1, max_value=10, label='Quantity', writable=is_unlocked)
        fields.price = NumericField(min_value=1, label='Price', writable=is_unlocked)
        fields.currency_code = ChoiceField([Choice('USD', Field(label='USD')),
                                            Choice('EUR', Field(label='EUR'))],
                                           label='Currency', writable=is_unlocked)

    def is_locked(self):
        return self.paypal_order is not None

    @exposed
    def events(self, events):
        events.pay_event = Event(label='Pay', action=Action(self.pay))
        events.clear_event = Event(label='Clear', action=Action(self.clear))

    def pay(self):
        self.paypal_order = PayPalOrder(json_string=json.dumps(self.as_json()))
        return self.paypal_order.id

    def clear(self):
        self.paypal_order = None


class ShoppingUI(UserInterface):
    def assemble(self):
        shopping_cart = ShoppingCart.for_current_session()

        home = self.define_view('/', title='Paypal Example')
        home.set_slot('main', PurchaseForm.factory(shopping_cart))

        order_summary_page = self.define_view('/order_summary', title='Order Summary')
        order_summary_page.set_slot('main', PurchaseSummary.factory(shopping_cart))

        self.define_transition(shopping_cart.events.pay_event, home, order_summary_page)
        self.define_transition(shopping_cart.events.clear_event, order_summary_page, home)

        self.define_page(MenuPage)



