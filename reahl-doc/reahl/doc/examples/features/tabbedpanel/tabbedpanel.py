from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, TabbedPanel, Tab, P

class MyPage(HTML5Page):
    def __init__(self, view):
        super(MyPage, self).__init__(view, style='basic')

        tabbed_panel = self.body.add_child(TabbedPanel(view, 'mytabbedpanel'))

        contents1 = P.factory(text='A paragraph to give content to the first tab.')
        tabbed_panel.add_tab(Tab(view, 'Tab 1', '1', contents1))

        contents2 = P.factory(text='And another ...  to give content to the second tab.')
        tabbed_panel.add_tab(Tab(view, 'Tab 2', '2', contents2))
        
        contents3 = P.factory(text='Something else on the third tab.')
        tabbed_panel.add_tab(Tab(view, 'Tab 3', '3', contents3))


class TabbedPanelUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Tabbed panel demo', page=MyPage.factory())



