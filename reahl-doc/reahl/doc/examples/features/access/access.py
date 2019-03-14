from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface
from reahl.web.bootstrap.ui import HTML5Page
from reahl.web.bootstrap.forms import Form, TextInput, FormLayout, Button
from reahl.component.modelinterface import secured, Action, Event
from reahl.component.modelinterface import exposed, Field


class AccessUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Access control demo', 
                              page=HomePage.factory())


class HomePage(HTML5Page):
    def __init__(self, view):
        super(HomePage, self).__init__(view)
        self.body.add_child(CommentForm(view))

class Comment(object):
    def allowed_to_see(self):
        # this is hard-coded, but you can check business rules here
        return True 

    def allowed_to_write(self):
        # this is hard-coded, but you can check business rules here
        return False

    @exposed
    def fields(self, fields):
        fields.greyed_out_field = Field(label='Some data',
                                        default='a value you\'re allowed to see, but not edit, so it is greyed out',
                                        readable=Action(self.allowed_to_see),
                                        writable=Action(self.allowed_to_write))

    @exposed
    def events(self, events):
        events.greyed_out_event = Event(label='Greyed out button', 
                                        action=Action(self.do_something))

    @secured(read_check=allowed_to_see, write_check=allowed_to_write)
    def do_something(self):
        pass


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, 'myform')
        comment = Comment()

        self.use_layout(FormLayout())

        self.layout.add_input(TextInput(self, comment.fields.greyed_out_field))

        self.define_event_handler(comment.events.greyed_out_event)
        self.add_child(Button(self, comment.events.greyed_out_event))





