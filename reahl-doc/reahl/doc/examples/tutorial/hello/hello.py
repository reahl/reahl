
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage

class HelloApp(UserInterface):
    def assemble(self):
        self.define_main_window(TwoColumnPage)
        self.define_view(u'/', title=u'Home')

