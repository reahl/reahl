
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, SlidingPanel, Panel, P

class MyPage(HTML5Page):
    def __init__(self, view):
        super(MyPage, self).__init__(view, style='basic')
	 
        sliding_panel = SlidingPanel(view)
        self.body.add_child(sliding_panel)

        panel1 = Panel(view)
        panel1.add_child(P(view, text='a paragraph with text'))
        sliding_panel.add_panel(panel1)

        panel2 = Panel(view)
        panel2.add_child(P(view, text='a different paragraph'))
        sliding_panel.add_panel(panel2)


class SlidingPanelUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Sliding panel demo', page=MyPage.factory())



