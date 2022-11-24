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



from reahl.component.modelinterface import ExposedNames, Field, Event, Action, Choice, IntegerField
from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import FieldSet, Span
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import Form, FormLayout, TextInput, ChoiceField, InlineFormLayout, SelectInput

from sqlalchemy import Column, Integer, UnicodeText, orm
from reahl.sqlalchemysupport import Base, session_scoped


class DynamicUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=ColumnLayout(
                                                              ColumnOptions('main', size=ResponsiveSize(lg=7))).with_slots()))
        home = self.define_view('/', title='Dynamic error demo')
        home.set_slot('main', CalculatorForm.factory())


class CalculatorForm(Form):
    def __init__(self, view):
        super().__init__(view, 'dynamic_content_error_form')
        self.use_layout(FormLayout())
        self.calculator = Calculator.for_current_session()

        try:
            self.enable_refresh(on_refresh=self.calculator.events.inputs_changed)
        except DomainException as ex:
            self.layout.add_alert_for_domain_exception(ex)

        controls = self.add_child(FieldSet(view).use_layout(InlineFormLayout()))
        self.add_inputs(controls)
        self.display_result(controls)

    def add_inputs(self, controls):
        operand_a_input = TextInput(self, self.calculator.fields.operand_a, refresh_widget=self)
        controls.layout.add_input(operand_a_input, hide_label=True)

        operator_input = SelectInput(self, self.calculator.fields.operator, refresh_widget=self)
        controls.layout.add_input(operator_input, hide_label=True)

        operand_b_input = TextInput(self, self.calculator.fields.operand_b, refresh_widget=self)
        controls.layout.add_input(operand_b_input, hide_label=True)

    def display_result(self, controls):
        if self.calculator.result is not None:
            message = '= %s' % self.calculator.result
        else:
            message = '= ---'
        controls.add_child(Span(self.view, text=message))


@session_scoped
class Calculator(Base):
    __tablename__ = 'dynamic_content_error_calculator'

    id              = Column(Integer, primary_key=True)
    operand_a       = Column(Integer)
    operand_b       = Column(Integer)
    operator        = Column(UnicodeText)
    result          = Column(Integer)

    fields = ExposedNames()
    fields.operand_a  = lambda i: IntegerField(label='A', required=True)
    fields.operand_b  = lambda i: IntegerField(label='B', required=True)
    fields.operator   = lambda i: ChoiceField([Choice('plus', Field(label='+')),
                                          Choice('divide', Field(label='÷'))], required=True)

    events = ExposedNames()
    events.inputs_changed = lambda i: Event(action=Action(i.recalculate))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.operand_a = 1
        self.operand_b = 1
        self.operator = 'plus'
        self.recalculate()

    @property
    def is_divide_by_zero(self):
        return self.operator == 'divide' and self.operand_b == 0

    def recalculate(self):
        if self.is_divide_by_zero:
            self.result = None
            raise DomainException(message='I can\'t divide by 0')

        if self.operator == 'plus':
            self.result = self.operand_a + self.operand_b
        elif self.operator == 'divide':
            self.result = int(self.operand_a / self.operand_b)

