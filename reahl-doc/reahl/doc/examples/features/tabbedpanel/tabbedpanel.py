from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface
from reahl.web.bootstrap.ui import HTML5Page, P
from reahl.web.bootstrap.tabbedpanel import TabbedPanel, Tab

class MyPage(HTML5Page):
    def __init__(self, view):
        super(MyPage, self).__init__(view)

        tabbed_panel = self.body.add_child(TabbedPanel(view))

        contents1 = P.factory(text='A paragraph to give content to the first tab.')
        tabbed_panel.add_tab(Tab(view, 'Tab 1', '1', contents1))

        contents2 = P.factory(text='And another ...  to give content to the second tab.')
        tabbed_panel.add_tab(Tab(view, 'Tab 2', '2', contents2))
        
        contents3 = P.factory(text='Something else on the third tab.')
        tabbed_panel.add_tab(Tab(view, 'Tab 3', '3', contents3))


class TabbedPanelUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Tabbed panel demo', page=MyPage.factory())



