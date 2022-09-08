
from reahl.component.modelinterface import ExposedNames, EmailField, Field
from reahl.component.modelinterface import Event, Action, Not

from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.forms import Form, TextInput, FormLayout, ButtonInput
from reahl.web.bootstrap.grid import ResponsiveSize, ColumnLayout, ColumnOptions, Container


class PageFlowUI(UserInterface):
    def assemble(self):
        contents_layout = ColumnLayout(ColumnOptions('main', ResponsiveSize(lg=6))).with_slots()
        page_layout = PageLayout(contents_layout=contents_layout, document_layout=Container())
        self.define_page(HTML5Page).use_layout(page_layout)
        self.define_user_interface('/', PageFlowExampleUI, name='pageflow', slot_map={'main': 'main'})


class PageFlowExampleUI(UserInterface):
    def assemble(self):
        comment = Comment()

        home = self.define_view('/', title='Page flow demo')
        home.set_slot('main', CommentForm.factory(comment))

        thanks = self.define_view('/thanks', title='Thank you!')
        thanks_text = 'Thanks for submitting your comment'
        thanks.set_slot('main', P.factory(text=thanks_text))

        none_submitted = self.define_view('/none', title='Nothing to say?')
        none_text = 'Mmm, you submitted an empty comment??'
        none_submitted.set_slot('main', P.factory(text=none_text))

        self.define_transition(comment.events.submit, home, thanks, 
                               guard=Action(comment.contains_text))
        self.define_transition(comment.events.submit, home, none_submitted, 
                               guard=Not(Action(comment.contains_text)))

        
class Comment:
    fields = ExposedNames()
    fields.email_address = lambda i: EmailField(label='Email address', required=True)
    fields.text = lambda i: Field(label='Comment')

    events = ExposedNames()
    events.submit = lambda i: Event(label='Submit', action=Action(i.submit))

    def submit(self):
        print('%s submitted a comment:' % self.email_address)
        print(self.text)

    def contains_text(self):
        return self.text and self.text.strip() != ''


class CommentForm(Form):
    def __init__(self, view, comment):
        super().__init__(view, 'myform')
        self.use_layout(FormLayout())

        self.layout.add_input(TextInput(self, comment.fields.email_address))
        self.layout.add_input(TextInput(self, comment.fields.text))
        self.add_child(ButtonInput(self, comment.events.submit))






