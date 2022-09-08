

from sqlalchemy import Column, UnicodeText, Integer
from reahl.sqlalchemysupport import Session, Base

from reahl.web.fw import UserInterface, Widget
from reahl.web.bootstrap.forms import Form, FieldSet, TextInput, FormLayout, ButtonInput
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P, Div
from reahl.component.modelinterface import ExposedNames, EmailField, Field
from reahl.component.modelinterface import Event, Action


class PersistenceUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Persistence demo', page=HomePage.factory())


class HomePage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)

        self.body.add_child(PersistenceExample(view))

            
class PersistenceExample(Widget):
    def __init__(self, view):
        super().__init__(view)

        self.add_child(CommentForm(view))
        for comment in Session.query(Comment).all():
            self.add_child(CommentBox(view, comment))


class Comment(Base):
    __tablename__ = 'features_comment'
    
    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    text          = Column(UnicodeText)
    
    fields = ExposedNames()
    fields.email_address = lambda i: EmailField(label='Email address', required=True)
    fields.text          = lambda i: Field(label='Comment', required=True)

    events = ExposedNames()
    events.submit = lambda i: Event(label='Submit', action=Action(i.submit))

    def submit(self):
        Session.add(self)


class CommentForm(Form):
    def __init__(self, view):
        super().__init__(view, 'myform')

        new_comment = Comment()
        grouped_inputs = FieldSet(view, legend_text='Leave a comment').use_layout(FormLayout())
        self.add_child(grouped_inputs)

        grouped_inputs.layout.add_input(TextInput(self, new_comment.fields.email_address))
        grouped_inputs.layout.add_input(TextInput(self, new_comment.fields.text))

        self.define_event_handler(new_comment.events.submit)
        grouped_inputs.add_child(ButtonInput(self, new_comment.events.submit))


class CommentBox(Div):
    def __init__(self, view, comment):
        super().__init__(view)
        comment_text = 'By %s: %s' % (comment.email_address, comment.text)
        self.add_child(P(view, text=comment_text))
        

