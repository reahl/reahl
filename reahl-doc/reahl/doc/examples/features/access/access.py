from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, Form, TextInput, Button, LabelledBlockInput
from reahl.component.modelinterface import secured, Action, Event
from reahl.component.modelinterface import exposed, EmailField



class AccessUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Access control demo', 
                              page=HomePage.factory())


class HomePage(HTML5Page):
    def __init__(self, view):
        super(HomePage, self).__init__(view, style='basic')
        self.body.add_child(CommentForm(view))


class Comment(object):
    def always_allowed(self):
        return True

    def never_allowed(self):
        return False

    @exposed
    def fields(self, fields):
        fields.greyed_out_field = EmailField(label='Greyed out',
                                             default='some default value',
                                             readable=Action(self.always_allowed),
                                             writable=Action(self.never_allowed))

    @exposed
    def events(self, events):
        events.greyed_out_event = Event(label='Greyed out button', 
                                        action=Action(self.do_something))

    @secured(read_check=always_allowed, write_check=never_allowed)
    def do_something(self): 
        pass


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, 'myform')

        comment = Comment()
        text_input = TextInput(self, comment.fields.greyed_out_field)
        self.add_child(LabelledBlockInput(text_input))

        self.define_event_handler(comment.events.greyed_out_event)
        self.add_child( Button(self, comment.events.greyed_out_event) )






