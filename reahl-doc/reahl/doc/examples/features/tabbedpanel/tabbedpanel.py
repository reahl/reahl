
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, TabbedPanel, Tab, P

class MyPage(TwoColumnPage):
    def __init__(self, view):
        super(MyPage, self).__init__(view, style=u'basic')

        tabbed_panel = self.main.add_child(TabbedPanel(view, u'mytabbedpanel'))
        tabbed_panel.add_tab(Tab(view, u'Tab 1', u'1', P.factory(text=u'A paragraph to give content to the first tab.')))
        tabbed_panel.add_tab(Tab(view, u'Tab 2', u'2', P.factory(text=u'And another ...  to give content to the second tab.')))
        tabbed_panel.add_tab(Tab(view, u'Tab 3', u'3', P.factory(text=u'Something else on the third tab.')))


class TabbedPanelUI(UserInterface):
    def assemble(self):
        self.define_view(u'/', title=u'Tabbed panel demo', page=MyPage.factory())



