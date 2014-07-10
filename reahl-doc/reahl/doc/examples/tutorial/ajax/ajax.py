


from __future__ import unicode_literals
from __future__ import print_function
from reahl.web.fw import UserInterface, Bookmark
from reahl.web.ui import TwoColumnPage, P, H, Panel, HMenu
from reahl.component.modelinterface import exposed, IntegerField


class WidgetRefreshUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style='basic')
        find = self.define_view('/', title='Refreshing widget')
        find.set_slot('main', HomePanel.factory())


class HomePanel(Panel):
    def __init__(self, view):
        super(HomePanel, self).__init__(view)

        panel = RefreshedPanel(view, 'my_refreshedpanel')
        bookmarks = [panel.get_bookmark(1),
                     panel.get_bookmark(2),
                     panel.get_bookmark(3)]

        self.add_child(H(view, 1, text='Refreshing widget'))
        self.add_child(HMenu.from_bookmarks(view, bookmarks))
        self.add_child(panel)


class RefreshedPanel(Panel):
    def __init__(self, view, css_id):
        super(RefreshedPanel, self).__init__(view, css_id=css_id)
        self.add_child(P(view, text='You selected link number %s' % self.selected))
        self.enable_refresh()

    @exposed
    def query_fields(self, fields):
        fields.selected = IntegerField(required=False, default=1)
        
    def get_bookmark(self, for_selected):
        return Bookmark.for_widget('Select %s' % for_selected, query_arguments={'selected': for_selected})






