
from reahl.web.fw import Widget, UserInterface
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.tabbedpanel import TabbedPanel, Tab


class TabbedPanelExample(Widget):
    def __init__(self, view):
        super().__init__(view)

        tabbed_panel = self.add_child(TabbedPanel(view))

        contents1 = P.factory(text='A paragraph to give content to the first tab.')
        tabbed_panel.add_tab(Tab(view, 'Tab 1', '1', contents1))

        contents2 = P.factory(text='And another ...  to give content to the second tab.')
        tabbed_panel.add_tab(Tab(view, 'Tab 2', '2', contents2))

        contents3 = P.factory(text='Something else on the third tab.')
        tabbed_panel.add_tab(Tab(view, 'Tab 3', '3', contents3))


class MyPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.body.add_child(TabbedPanelExample(view))


class TabbedPanelUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Tabbed panel demo', page=MyPage.factory())



