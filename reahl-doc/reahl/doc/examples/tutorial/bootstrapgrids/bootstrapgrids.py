
from reahl.web.fw import UserInterface, Layout
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P, Div, H
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.navs import Nav


class GridBasicsPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)

        self.body.use_layout(Container())

        self.add_four()
        self.add_twelve()

    def add_four(self):
        layout = ColumnLayout(ColumnOptions('first', ResponsiveSize(md=6)),
                              ColumnOptions('second', ResponsiveSize(md=6)),
                              ColumnOptions('third', ResponsiveSize(md=6)),
                              ColumnOptions('fourth', ResponsiveSize(md=6)))

        div = Div(self.view).use_layout(layout)
        self.body.add_child(div)

        message = '6/12ths on md and larger, else defaults to 12/12ths'
        div.layout.columns['first'].add_child(P(self.view, text=message))
        div.layout.columns['second'].add_child(P(self.view, text=message))
        div.layout.columns['third'].add_child(P(self.view, text=message))
        div.layout.columns['fourth'].add_child(P(self.view, text=message))


    def add_twelve(self):
        div = Div(self.view).use_layout(ColumnLayout())
        self.body.add_child(div)

        for i in range(1, 13):
            column = div.layout.add_column(str(i), size=ResponsiveSize(md=1))
            column.add_child(P(self.view, text='1/12th on md and larger'))


class PageLayoutPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.body.use_layout(Container())
        column_layout = ColumnLayout(ColumnOptions('left', ResponsiveSize(md=4)),
                                     ColumnOptions('right', ResponsiveSize(md=8)))
        self.use_layout(PageLayout(contents_layout=column_layout))

        self.layout.header.add_child(P(view, text='The header'))
        self.layout.footer.add_child(P(view, text='The footer'))

        left = column_layout.columns['left']
        left.add_child(P(view, text='To the left'))

        right = column_layout.columns['right']
        right.add_child(P(view, text='To the right'))


class CenteredLayout(Layout):
    def customise_widget(self):
        self.container = self.widget.add_child(Div(self.view))
        self.container.use_layout(Container(fluid=False))
        self.centre = self.container.add_child(Div(self.view))
        column_layout = ColumnLayout(ColumnOptions('left', ResponsiveSize(md=4)),
                                     ColumnOptions('right', ResponsiveSize(md=8)))
        self.centre.use_layout(column_layout)

    @property
    def columns(self):
        return self.centre.layout.columns


class ContainerPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)

        page_layout = PageLayout(contents_layout=CenteredLayout(),
                                 header_layout=Container(fluid=True),
                                 footer_layout=Container(fluid=True))

        self.use_layout(page_layout)

        self.layout.header.add_child(P(view, text='The header'))
        self.layout.footer.add_child(P(view, text='The footer'))

        columns = page_layout.contents_layout.columns
        left = columns['left']
        left.add_child(P(view, text='To the left'))

        right = columns['right']
        right.add_child(P(view, text='To the right'))


class HomePage(HTML5Page):
    def __init__(self, view, bookmarks):
        super().__init__(view)

        self.body.use_layout(Container())
        self.add_child(H(view, 1, text='Examples'))
        self.add_child(Nav(view).with_bookmarks(bookmarks))



class BootstrapGridsUI(UserInterface):
    def assemble(self):
        basics = self.define_view('/gridBasics', title='Grid basics', page=GridBasicsPage.factory())
        page_layout = self.define_view('/pageLayout', title='Page layout', page=PageLayoutPage.factory())
        container_layout = self.define_view('/containerLayout', title='Container layout', page=ContainerPage.factory())

        bookmarks = [
            basics.as_bookmark(self),
            page_layout.as_bookmark(self),
            container_layout.as_bookmark(self)]

        self.define_view('/', title='Home', page=HomePage.factory(bookmarks))


