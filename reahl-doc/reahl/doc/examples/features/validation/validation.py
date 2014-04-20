
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput
from reahl.component.modelinterface import exposed, EmailField

class ValidationUI(UserInterface):
    def assemble(self):
        self.define_view(u'/', title=u'Validation demo', page=HomePage.factory())


class HomePage(TwoColumnPage):
    def __init__(self, view):
        super(HomePage, self).__init__(view, style=u'basic')
        self.main.add_child(CommentForm(view))


class Comment(object):
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label=u'Email address', required=True)


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, u'myform')

        comment = Comment()
        self.add_child( TextInput(self, comment.fields.email_address) )




