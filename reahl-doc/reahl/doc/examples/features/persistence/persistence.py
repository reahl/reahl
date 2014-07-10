
from __future__ import unicode_literals
from __future__ import print_function
import elixir

from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import UserInterface
from reahl.web.ui import Button
from reahl.web.ui import Form
from reahl.web.ui import InputGroup
from reahl.web.ui import LabelledBlockInput
from reahl.web.ui import P
from reahl.web.ui import Panel
from reahl.web.ui import TextInput
from reahl.web.ui import TwoColumnPage
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action


class PersistenceUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Persistence demo', page=HomePage.factory())


class HomePage(TwoColumnPage):
    def __init__(self, view):
        super(HomePage, self).__init__(view, style='basic')

        self.main.add_child(CommentForm(view))

        for comment in Comment.query.all():
            self.main.add_child(CommentBox(view, comment))


class Comment(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata, tablename='features_comment')
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    text          = elixir.Field(elixir.UnicodeText)
    
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
        grouped_inputs = self.add_child(InputGroup(view, label_text='Leave a comment'))
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_comment.fields.email_address)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_comment.fields.text)) )
        self.define_event_handler(new_comment.events.submit)
        grouped_inputs.add_child( Button(self, new_comment.events.submit) )


class CommentBox(Panel):
    def __init__(self, view, comment):
        super(CommentBox, self).__init__(view)
        self.add_child(P(view, text='By %s: %s' % (comment.email_address, comment.text)))
        

