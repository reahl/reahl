
from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.component.modelinterface import ExposedNames, Event, Action, IntegerField, Choice, ChoiceField
from reahl.sqlalchemysupport import session_scoped, Base, Integer, Column
from reahl.web.fw import UserInterface
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.forms import Form, SelectInput, InlineFormLayout, MarginLayout, TextInput
from reahl.web.bootstrap.ui import P, FieldSet
from reahl.web.bootstrap.grid import Container


@session_scoped
class Calculator(Base):
    __tablename__ = 'dynamic_content_select'

    id              = Column(Integer, primary_key=True)
    operandA        = Column(Integer)
    operandB        = Column(Integer)
    sum             = Column(Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.operandA = 1
        self.operandB = 4
        self.recalculate()

    fields = ExposedNames()
    fields.operandA = lambda i: IntegerField(label='A')
    fields.operandB = lambda i: ChoiceField([Choice(4, IntegerField(label='4')),
                                       Choice(5, IntegerField(label='5')),
                                       Choice(6, IntegerField(label='6'))],
                                      label='B')

    events = ExposedNames()
    events.input_changed = lambda i: Event(action=Action(i.recalculate))

    def recalculate(self):
        self.sum = self.operandA + self.operandB


class DynamicContentForm(Form):
    def __init__(self, view):
        super().__init__(view, 'my_cool_form')

        calculator = Calculator.for_current_session()
        self.enable_refresh(on_refresh=calculator.events.input_changed)

        grouped_inputs = self.add_child(FieldSet(view, legend_text='Calculator'))
        grouped_inputs.use_layout(InlineFormLayout())

        grouped_inputs.layout.add_input(TextInput(self, calculator.fields.operandA, refresh_widget=self)).use_layout(MarginLayout(2, right=True))
        grouped_inputs.layout.add_input(SelectInput(self, calculator.fields.operandB, refresh_widget=self))

        self.add_child(P(self.view, text='Sum: %s' % calculator.sum))


class DynamicContentPage(HTML5Page):
    def __init__(self, view):
        super(DynamicContentPage, self).__init__(view)
        self.body.use_layout(Container())
        self.body.add_child(DynamicContentForm(view))


class DynamicContentUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Dynamic content demo', page=DynamicContentPage.factory())



