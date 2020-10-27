
from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.component.modelinterface import exposed, Event, Action, IntegerField, Choice, ChoiceField
from reahl.sqlalchemysupport import session_scoped, Base, Integer, Column
from reahl.web.fw import UserInterface
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.forms import Form, SelectInput, InlineFormLayout, MarginLayout, TextInput
from reahl.web.bootstrap.ui import P, FieldSet
from reahl.web.bootstrap.grid import Container


@session_scoped
class DynamicContentSelect(Base):
    __tablename__ = 'dynamic_content_select'

    id              = Column(Integer, primary_key=True)
    operandA        = Column(Integer)
    operandB        = Column(Integer)
    sum             = Column(Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.select = False
        self.operandA = 1
        self.operandB = 4
        self.sum = 5

    @exposed
    def fields(self, fields):
        fields.operandA = ChoiceField([Choice(1, IntegerField(label='1')),
                                         Choice(2, IntegerField(label='2')),
                                         Choice(3, IntegerField(label='3'))],
                                        label='A')
        fields.operandB = ChoiceField([Choice(4, IntegerField(label='4')),
                                         Choice(5, IntegerField(label='5')),
                                         Choice(6, IntegerField(label='6'))],
                                        label='B')
        fields.sum = IntegerField(label='Sum')

    @exposed
    def events(self, events):
        events.something_changed = Event(action=Action(self.recalculate))

    def recalculate(self):
        self.sum = self.operandA + self.operandB


class DynamicContentForm(Form):
    def __init__(self, view):
        super().__init__(view, 'my_cool_form')

        model_object = DynamicContentSelect.for_current_session()
        self.enable_refresh(on_refresh=model_object.events.something_changed)

        grouped_inputs = self.add_child(FieldSet(view, legend_text='Calculator'))
        grouped_inputs.use_layout(InlineFormLayout())

        grouped_inputs.layout.add_input(TextInput(self, model_object.fields.operandA, refresh_widget=self)).use_layout(MarginLayout(2, right=True))
        grouped_inputs.layout.add_input(SelectInput(self, model_object.fields.operandB, refresh_widget=self))

        self.add_child(P(self.view, text='Sum: %s' % model_object.sum))


class DynamicContentPage(HTML5Page):
    def __init__(self, view):
        super(DynamicContentPage, self).__init__(view)
        self.body.use_layout(Container())
        self.body.add_child(DynamicContentForm(view))


class DynamicContentUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Dynamic content demo', page=DynamicContentPage.factory())



