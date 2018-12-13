from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface
from reahl.web.bootstrap.ui import HTML5Page
from reahl.web.bootstrap.forms import Form, TextInput, FormLayout
from reahl.component.modelinterface import exposed, EmailField

class ValidationUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Validation demo', page=HomePage.factory())


class HomePage(HTML5Page):
    def __init__(self, view):
        super(HomePage, self).__init__(view)
        self.body.add_child(CommentForm(view))


class Comment(object):
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email address', required=True)


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, 'myform')

        new_comment = Comment()
        self.use_layout(FormLayout())
        self.layout.add_input( TextInput(self, new_comment.fields.email_address) )




