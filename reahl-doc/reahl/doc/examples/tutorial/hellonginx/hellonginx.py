
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage

class HelloUI(UserInterface):
    def assemble(self):
        self.define_view(u'/', title=u'Home', page=TwoColumnPage.factory())

