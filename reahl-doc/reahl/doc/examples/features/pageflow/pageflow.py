
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.ui import Button, Form, LabelledBlockInput, P, TextInput, HTML5Page
from reahl.web.pure import PageColumnLayout, UnitSize
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action, Not

class PageFlowUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page, style='basic').use_layout(PageColumnLayout(('main', UnitSize('1/2'))))  

        comment = Comment()

        home = self.define_view('/', title='Page flow demo')
        home.set_slot('main', CommentForm.factory(comment))

        thanks = self.define_view('/thanks', title='Thank you!')
        thanks.set_slot('main', P.factory(text='Thanks for submitting your comment'))

        none_submitted = self.define_view('/none', title='Nothing to say?')
        none_submitted.set_slot('main', P.factory(text='Mmm, you submitted an empty comment??'))

        self.define_transition(comment.events.submit, home, thanks, guard=Action(comment.contains_text))
        self.define_transition(comment.events.submit, home, none_submitted, guard=Not(Action(comment.contains_text)))

        
class Comment(object):
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email address', required=True)
        fields.text = Field(label='Comment')

    @exposed
    def events(self, events):
        events.submit = Event(label='Submit', action=Action(self.submit))

    def submit(self):
        print('%s submitted a comment:' % self.email_address)
        print(self.text)

    def contains_text(self):
        return self.text and self.text.strip() != ''


class CommentForm(Form):
    def __init__(self, view, comment):
        super(CommentForm, self).__init__(view, 'myform')

        self.add_child( LabelledBlockInput(TextInput(self, comment.fields.email_address)) )
        self.add_child( LabelledBlockInput(TextInput(self, comment.fields.text)) )
        self.add_child( Button(self, comment.events.submit) )



