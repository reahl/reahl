

from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.ui import HTML5Page, P
from reahl.web.bootstrap.navs import Nav, TabLayout
from reahl.web.bootstrap.grid import ColumnLayout, ResponsiveSize, Container


class MyCustomPage(HTML5Page):
    def __init__(self, view, bookmarks):
        super(MyCustomPage, self).__init__(view)

        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(('secondary', ResponsiveSize(md=3)),
                                       ('main', ResponsiveSize(md=9))).with_slots()
        self.layout.contents.use_layout(contents_layout)

        menu = Nav(view).use_layout(TabLayout()).with_bookmarks(bookmarks)
        self.layout.header.add_child(menu)


class SlotsUI(UserInterface):
    def assemble(self):

        home = self.define_view('/', title='Page 1')
        home.set_slot('main', P.factory(text='In this slot will be some main content for the view on /'))
        home.set_slot('secondary', P.factory(text='Some secondary content related to /'))

        another = self.define_view('/page2', title='Page 2')
        another.set_slot('main', P.factory(text='This could, for example, be where a photo gallery shows a large photo.'))
        another.set_slot('secondary', P.factory(text='Thumbnails will then sit on the side of the big photo.'))

        bookmarks = [home.as_bookmark(self), another.as_bookmark(self)]
        self.define_page(MyCustomPage, bookmarks)
