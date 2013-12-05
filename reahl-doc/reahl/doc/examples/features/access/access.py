

from reahl.web.fw import Region
from reahl.web.ui import TwoColumnPage, Form, TextInput, Button, LabelledBlockInput
from reahl.component.modelinterface import exposed, EmailField, secured, Event, Action, PasswordField

class AccessApp(Region):
    def assemble(self):
        self.define_main_window(TwoColumnPage, style=u'basic')  

        home = self.define_view(u'/', title=u'Access control demo')
        home.set_slot(u'main', CommentForm.factory())


class Comment(object):
    def always_allowed(self):
        return True

    def never_allowed(self):
        return False

    @exposed
    def fields(self, fields):
        fields.greyed_out_field = EmailField(label=u'Greyed out',
                                             default=u'some default value',
                                             readable=Action(self.always_allowed),
                                             writable=Action(self.never_allowed))

    @exposed
    def events(self, events):
        events.greyed_out_event = Event(label=u'Greyed out button', action=Action(self.do_something))

    @secured(read_check=always_allowed, write_check=never_allowed)
    def do_something(self): 
        pass


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, u'myform')

        comment = Comment()
        self.add_child( LabelledBlockInput(TextInput(self, comment.fields.greyed_out_field)) )

        self.define_event_handler(comment.events.greyed_out_event)
        self.add_child( Button(self, comment.events.greyed_out_event) )






