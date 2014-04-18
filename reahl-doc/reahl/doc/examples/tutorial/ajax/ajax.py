


from reahl.web.fw import UserInterface, Bookmark
from reahl.web.ui import TwoColumnPage, P, H, Panel, HMenu
from reahl.component.modelinterface import exposed, IntegerField


class WidgetRefreshUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style=u'basic')
        find = self.define_view(u'/', title=u'Refreshing widget')
        find.set_slot(u'main', HomePanel.factory())


class HomePanel(Panel):
    def __init__(self, view):
        super(HomePanel, self).__init__(view)

        panel = RefreshedPanel(view, u'my_refreshedpanel')
        bookmarks = [panel.get_bookmark(1),
                     panel.get_bookmark(2),
                     panel.get_bookmark(3)]

        self.add_child(H(view, 1, text=u'Refreshing widget'))
        self.add_child(HMenu.from_bookmarks(view, bookmarks))
        self.add_child(panel)


class RefreshedPanel(Panel):
    def __init__(self, view, css_id):
        super(RefreshedPanel, self).__init__(view, css_id=css_id)
        self.add_child(P(view, text=u'You selected link number %s' % self.selected))
        self.enable_refresh()

    @exposed
    def query_fields(self, fields):
        fields.selected = IntegerField(required=False, default=1)
        
    def get_bookmark(self, for_selected):
        return Bookmark.for_widget(u'Select %s' % for_selected, query_arguments={u'selected': for_selected})






