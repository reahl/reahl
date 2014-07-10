
from __future__ import unicode_literals
from __future__ import print_function
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, P


class HelloPage(TwoColumnPage):
    def __init__(self, view):
        super(HelloPage, self).__init__(view)
        self.main.add_child(P(view, text='Hello World!'))


class HelloUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Home', page=HelloPage.factory())

