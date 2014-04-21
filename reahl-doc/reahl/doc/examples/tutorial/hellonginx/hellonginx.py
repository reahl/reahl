
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, P


class HelloPage(TwoColumnPage):
    def __init__(self, view):
        super(HelloPage, self).__init__(view)
        self.main.add_child(P(view, text=u'Hello World!'))


class HelloUI(UserInterface):
    def assemble(self):
        self.define_view(u'/', title=u'Home', page=HelloPage.factory())

