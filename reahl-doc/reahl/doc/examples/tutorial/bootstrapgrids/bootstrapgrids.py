
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.bootstrap.ui import HTML5Page, P, Div, H
from reahl.web.bootstrap.grid import Container, ColumnLayout, ResponsiveSize, PageLayout
from reahl.web.bootstrap.navs import Nav


class GridBasicsPage(HTML5Page):
    def __init__(self, view):
        super(GridBasicsPage, self).__init__(view)

        self.body.use_layout(Container())

        self.add_twelve()
        self.add_two()

    def add_two(self):
        layout = ColumnLayout(('left', ResponsiveSize(md=4)), 
                              ('right', ResponsiveSize(md=8)))

        div = Div(self.view).use_layout(layout)
        self.body.add_child(div)

        div.layout.columns['left'].add_child(P(self.view, text='4/12ths on md and larger'))
        div.layout.columns['right'].add_child(P(self.view, text='8/12ths on md and larger'))

    def add_twelve(self):
        div = Div(self.view).use_layout(ColumnLayout())
        self.body.add_child(div)

        for i in range(1, 13):
            column = div.layout.add_column(ResponsiveSize(md=1))
            column.add_child(P(self.view, text='1/12th on md and larger'))


class PageLayoutPage(HTML5Page):
    def __init__(self, view):
        super(PageLayoutPage, self).__init__(view)

        self.body.use_layout(Container())

        column_layout = ColumnLayout(('left', ResponsiveSize(md=4)), 
                                     ('right', ResponsiveSize(md=8)))

        self.use_layout(PageLayout(contents_layout=column_layout))

        self.layout.header.add_child(P(view, text='The header'))
        self.layout.footer.add_child(P(view, text='The footer'))
        
        left = column_layout.columns['left']
        left.add_child(P(view, text='To the left'))

        right = column_layout.columns['right']
        right.add_child(P(view, text='To the right'))


class HomePage(HTML5Page):
    def __init__(self, view, bookmarks):
        super(HomePage, self).__init__(view)

        self.body.use_layout(Container())
        self.add_child(H(view, 1, text='Examples'))
        self.add_child(Nav.from_bookmarks(view, bookmarks))



class BootstrapGridsUI(UserInterface):
    def assemble(self):
        basics = self.define_view('/gridBasics', title='Grid basics', page=GridBasicsPage.factory())
        page_layout = self.define_view('/pageLayout', title='Page layout', page=PageLayoutPage.factory())

        bookmarks = [
            basics.as_bookmark(self),
            page_layout.as_bookmark(self)]

        self.define_view('/', title='Home', page=HomePage.factory(bookmarks))


