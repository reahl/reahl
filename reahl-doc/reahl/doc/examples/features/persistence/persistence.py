
from __future__ import print_function, unicode_literals, absolute_import, division

from sqlalchemy import Column, UnicodeText, Integer
from reahl.sqlalchemysupport import Session, Base

from reahl.web.fw import UserInterface
from reahl.web.ui import Button, Form, InputGroup, LabelledBlockInput
from reahl.web.ui import HTML5Page, P, Panel, TextInput
from reahl.component.modelinterface import exposed, EmailField, Field
from reahl.component.modelinterface import Event, Action


class PersistenceUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Persistence demo', page=HomePage.factory())


class HomePage(HTML5Page):
    def __init__(self, view):
        super(HomePage, self).__init__(view, style='basic')

        self.body.add_child(CommentForm(view))

        for comment in Session.query(Comment).all():
            self.body.add_child(CommentBox(view, comment))


class Comment(Base):
    __tablename__ = 'features_comment'
    
    id = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    text          = Column(UnicodeText)
    
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email address', required=True)
        fields.text          = Field(label='Comment', required=True)

    @exposed
    def events(self, events):
        events.submit = Event(label='Submit', action=Action(self.submit))

    def submit(self):
        Session.add(self)


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, 'myform')

        new_comment = Comment()
        grouped_inputs = InputGroup(view, label_text='Leave a comment')
        self.add_child(grouped_inputs)

        email_input = TextInput(self, new_comment.fields.email_address)
        grouped_inputs.add_child( LabelledBlockInput(email_input) )

        text_input = TextInput(self, new_comment.fields.text)
        grouped_inputs.add_child( LabelledBlockInput(text_input) )

        self.define_event_handler(new_comment.events.submit)
        grouped_inputs.add_child( Button(self, new_comment.events.submit) )


class CommentBox(Panel):
    def __init__(self, view, comment):
        super(CommentBox, self).__init__(view)
        comment_text = 'By %s: %s' % (comment.email_address, comment.text)
        self.add_child(P(view, text=comment_text))
        

