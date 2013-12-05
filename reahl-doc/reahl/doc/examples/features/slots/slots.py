

from reahl.web.fw import Region
from reahl.web.ui import TwoColumnPage, P, HMenu


class MyCustomPage(TwoColumnPage):
    def __init__(self, view, bookmarks):
        super(MyCustomPage, self).__init__(view, style=u'basic')
        self.header.add_child(HMenu.from_bookmarks(view, bookmarks))

class SlotsApp(Region):
    def assemble(self):

        home = self.define_view(u'/', title=u'Page 1')
        home.set_slot(u'main', P.factory(text=u'In this slot will be some main content for the view on /'))
        home.set_slot(u'secondary', P.factory(text=u'Some secondary content related to /'))

        another = self.define_view(u'/page2', title=u'Page 2')
        another.set_slot(u'main', P.factory(text=u'This could, for example, be where a photo gallery shows a large photo.'))
        another.set_slot(u'secondary', P.factory(text=u'Thumbnails will then sit on the side of the big photo.'))

        bookmarks = [home.as_bookmark(self), another.as_bookmark(self)]
        self.define_main_window(MyCustomPage, bookmarks)
