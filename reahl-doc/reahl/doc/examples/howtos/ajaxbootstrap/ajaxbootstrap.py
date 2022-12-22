

from reahl.web.fw import UserInterface, Bookmark
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P, H, Div
from reahl.web.bootstrap.navs import Nav, TabLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, Container, ResponsiveSize
from reahl.component.modelinterface import ExposedNames, IntegerField



class WidgetRefreshUI(UserInterface):
    def assemble(self):
        page_layout = PageLayout(document_layout=Container(),
                                 contents_layout=ColumnLayout(ColumnOptions('main', ResponsiveSize(lg=6))).with_slots())
        self.define_page(HTML5Page).use_layout(page_layout)
        find = self.define_view('/', title='Refreshing widget')
        find.set_slot('main', HomePanel.factory())


class HomePanel(Div):
    def __init__(self, view):
        super().__init__(view)

        panel = RefreshedPanel(view, 'my_refreshedpanel')
        bookmarks = [panel.get_bookmark(1),
                     panel.get_bookmark(2),
                     panel.get_bookmark(3)]

        self.add_child(H(view, 1, text='Refreshing widget'))
        self.add_child(Nav(view).use_layout(TabLayout()).with_bookmarks(bookmarks))
        self.add_child(panel)


class RefreshedPanel(Div):
    def __init__(self, view, css_id):
        super().__init__(view, css_id=css_id)
        self.add_child(P(view, text='You selected link number %s' % self.selected))
        self.enable_refresh()

    query_fields = ExposedNames()
    query_fields.selected = lambda i: IntegerField(required=False, default=1)

    def get_bookmark(self, for_selected):
        return Bookmark.for_widget('Select %s' % for_selected, query_arguments={'selected': for_selected}).on_view(self.view)









