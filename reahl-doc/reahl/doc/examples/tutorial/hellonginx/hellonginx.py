
from reahl.web.fw import Region
from reahl.web.ui import TwoColumnPage

class HelloApp(Region):
    def assemble(self):
        self.define_main_window(TwoColumnPage)
        self.define_view(u'/', title=u'Home')

