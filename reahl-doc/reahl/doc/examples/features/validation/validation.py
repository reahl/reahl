from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, Form, TextInput
from reahl.component.modelinterface import exposed, EmailField

class ValidationUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Validation demo', page=HomePage.factory())


class HomePage(HTML5Page):
    def __init__(self, view):
        super(HomePage, self).__init__(view, style='basic')
        self.body.add_child(CommentForm(view))


class Comment(object):
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email address', required=True)


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, 'myform')

        comment = Comment()
        self.add_child( TextInput(self, comment.fields.email_address) )




