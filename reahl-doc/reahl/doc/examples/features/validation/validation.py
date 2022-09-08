
from reahl.web.fw import UserInterface
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.forms import Form, TextInput, FormLayout, ButtonInput
from reahl.component.modelinterface import ExposedNames, EmailField, Event

class ValidationUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Validation demo', page=HomePage.factory())


class HomePage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.body.add_child(CommentForm(view))


class Comment:
    fields = ExposedNames()
    fields.email_address = lambda i: EmailField(label='Email address', required=True)
    
    events = ExposedNames()
    events.do_nothing = lambda i: Event(label='Submit')


class CommentForm(Form):
    def __init__(self, view):
        super().__init__(view, 'myform')

        new_comment = Comment()
        self.use_layout(FormLayout())
        self.layout.add_input( TextInput(self, new_comment.fields.email_address) )

        self.define_event_handler(new_comment.events.do_nothing)
        self.add_child(ButtonInput(self, new_comment.events.do_nothing))




