
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action, Not

class PageFlowUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style=u'basic')  

        comment = Comment()

        home = self.define_view(u'/', title=u'Page flow demo')
        home.set_slot(u'main', CommentForm.factory(comment))

        thanks = self.define_view(u'/thanks', title=u'Thank you!')
        thanks.set_slot(u'main', P.factory(text=u'Thanks for submitting your comment'))

        none_submitted = self.define_view(u'/none', title=u'Nothing to say?')
        none_submitted.set_slot(u'main', P.factory(text=u'Mmm, you submitted an empty comment??'))

        self.define_transition(comment.events.submit, home, thanks, guard=Action(comment.contains_text))
        self.define_transition(comment.events.submit, home, none_submitted, guard=Not(Action(comment.contains_text)))

        
class Comment(object):
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label=u'Email address', required=True)
        fields.text = Field(label=u'Comment')

    @exposed
    def events(self, events):
        events.submit = Event(label=u'Submit', action=Action(self.submit))

    def submit(self):
        print '%s submitted a comment:' % self.email_address
        print self.text

    def contains_text(self):
        return self.text and self.text.strip() != u''


class CommentForm(Form):
    def __init__(self, view, comment):
        super(CommentForm, self).__init__(view, u'myform')

        self.add_child( LabelledBlockInput(TextInput(self, comment.fields.email_address)) )
        self.add_child( LabelledBlockInput(TextInput(self, comment.fields.text)) )
        self.add_child( Button(self, comment.events.submit) )



