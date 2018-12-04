from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.component.modelinterface import exposed, EmailField, Field
from reahl.component.modelinterface import Event, Action, Not

from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.ui import HTML5Page, P
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
        self.use_layout(FormLayout())

        self.layout.add_input(TextInput(self, comment.fields.email_address))
        self.layout.add_input(TextInput(self, comment.fields.text))
        self.add_child(ButtonInput(self, comment.events.submit))






