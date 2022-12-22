# Copyright 2020, 2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import random
import string

from reahl.component.modelinterface import ExposedNames, Event, Action, Field
from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface, ErrorWidget, Url, Widget
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import Form, Button, FormLayout, TextInput
from reahl.web.bootstrap.ui import H, P, A

from sqlalchemy import Column, Integer
from reahl.sqlalchemysupport import Base, UnicodeText, Session


class OptimisticConcurrencyUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=ColumnLayout(
                                                              ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        home = self.define_view('/', title='Concurrency demo')
        home.set_slot('main', SimpleForm.factory())


class SimpleForm(Form):
    def __init__(self, view):
        super().__init__(view, 'simple_form')
        self.use_layout(FormLayout())
        if self.exception:
            self.layout.add_alert_for_domain_exception(self.exception)

        domain_object = self.get_or_create_domain_object()

        link = self.add_child(A(view, Url('/'), description='Open another tab...'))
        link.set_attribute('target', '_blank')
        self.add_child(P(view, text='...and increment the value there. Come back here and submit the value. A Concurrency error will be shown'))

        #Your own widget that tracks changes
        self.add_child(MyConcurrencyWidget(view, domain_object))

        self.layout.add_input(TextInput(self, domain_object.fields.some_field_value))
        self.define_event_handler(domain_object.events.submit)
        self.add_child(Button(self, domain_object.events.submit))
        self.define_event_handler(domain_object.events.increment)
        self.add_child(Button(self, domain_object.events.increment))

    def get_or_create_domain_object(self):
        domain_objects = Session.query(MyDomainObject).all()
        if len(domain_objects) == 0:
            domain_object = MyDomainObject()
            Session.add(domain_object)
            return domain_object
        return domain_objects[0]


class MyConcurrencyWidget(Widget):
    def __init__(self, view, domain_object):
        super().__init__(view)
        self.domain_object = domain_object
        self.add_child(P(view, text='Counter: %s' % domain_object.counter))

    def get_concurrency_hash_strings(self):
        yield '%s' % self.domain_object.counter


class MyDomainObject(Base):
    __tablename__ = 'optimistic_concurrency_domain_object'

    id = Column(Integer, primary_key=True)
    some_field_value = Column(UnicodeText)
    counter = Column(Integer)

    def __init__(self):
        self.counter = 0
        self.some_field_value = '123'

    fields = ExposedNames()
    fields.some_field_value = lambda i: Field(label='Some value')

    events = ExposedNames()
    events.submit = lambda i: Event(label='Submit')
    events.increment = lambda i: Event(label='Increment', action=Action(i.increment))

    def increment(self):
        self.counter += 1
