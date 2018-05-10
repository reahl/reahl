
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, P


class HelloPage(HTML5Page):
    def __init__(self, view):
        super(HelloPage, self).__init__(view)
        self.body.add_child(P(view, text='Hello World!'))


class HelloUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Home', page=HelloPage.factory())

