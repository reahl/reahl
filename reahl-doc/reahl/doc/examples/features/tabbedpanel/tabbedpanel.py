
from __future__ import unicode_literals
from __future__ import print_function
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, TabbedPanel, Tab, P

class MyPage(TwoColumnPage):
    def __init__(self, view):
        super(MyPage, self).__init__(view, style='basic')

        tabbed_panel = self.main.add_child(TabbedPanel(view, 'mytabbedpanel'))
        tabbed_panel.add_tab(Tab(view, 'Tab 1', '1', P.factory(text='A paragraph to give content to the first tab.')))
        tabbed_panel.add_tab(Tab(view, 'Tab 2', '2', P.factory(text='And another ...  to give content to the second tab.')))
        tabbed_panel.add_tab(Tab(view, 'Tab 3', '3', P.factory(text='Something else on the third tab.')))


class TabbedPanelUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Tabbed panel demo', page=MyPage.factory())



