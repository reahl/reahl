
import elixir

from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action


class PersistenceUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style=u'basic')
        home = self.define_view(u'/', title=u'Persistence demo')
        home.set_slot(u'main', CommentPostPanel.factory())


class Comment(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata, tablename=u'features_comment')
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    text          = elixir.Field(elixir.UnicodeText)
    
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label=u'Email address', required=True)
        fields.text          = Field(label=u'Comment', required=True)

    @exposed
    def events(self, events):
        events.submit = Event(label=u'Submit', action=Action(self.submit))

    def submit(self):
        Session.add(self)


class CommentPostPanel(Panel):
    def __init__(self, view):
        super(CommentPostPanel, self).__init__(view)

        self.add_child(CommentForm(view))

        for comment in Comment.query.all():
            self.add_child(CommentBox(view, comment))


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, u'myform')

        new_comment = Comment()
        grouped_inputs = self.add_child(InputGroup(view, label_text=u'Leave a comment'))
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_comment.fields.email_address)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_comment.fields.text)) )
        self.define_event_handler(new_comment.events.submit)
        grouped_inputs.add_child( Button(self, new_comment.events.submit) )


class CommentBox(Panel):
    def __init__(self, view, comment):
        super(CommentBox, self).__init__(view)
        self.add_child(P(view, text=u'By %s: %s' % (comment.email_address, comment.text)))
        

