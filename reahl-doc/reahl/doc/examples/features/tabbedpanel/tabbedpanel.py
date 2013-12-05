
from reahl.web.fw import Region
from reahl.web.ui import TwoColumnPage, TabbedPanel, Tab, P


class TabbedPanelApp(Region):
    def assemble(self):
        self.define_main_window(TwoColumnPage, style=u'basic')  

        home = self.define_view(u'/', title=u'Tabbed panel demo')
        home.set_slot(u'main', MyTabbedPanel.factory())


class MyTabbedPanel(TabbedPanel):
    def __init__(self, view):
        super(MyTabbedPanel, self).__init__(view, u'mytabbedpanel')
        self.add_tab(Tab(view, u'Tab 1', u'1', P.factory(text=u'A paragraph to give content to the first tab.')))
        self.add_tab(Tab(view, u'Tab 2', u'2', P.factory(text=u'And another ...  to give content to the second tab.')))
        self.add_tab(Tab(view, u'Tab 3', u'3', P.factory(text=u'Something else on the third tab.')))


