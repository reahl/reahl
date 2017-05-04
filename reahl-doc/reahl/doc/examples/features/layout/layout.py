from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.ui import HTML5Page, P, Div
from reahl.web.bootstrap.forms import Form, TextInput, FormLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.component.modelinterface import exposed, Field, EmailField

def lots_of(message):
    return message * 5

class LayoutUI(UserInterface):
    def assemble(self):
        contents_layout = ColumnLayout(ColumnOptions('secondary', ResponsiveSize(lg=4)),
                                       ColumnOptions('main', ResponsiveSize(lg=8)), add_slots=True)

        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=contents_layout))

        home = self.define_view('/', title='Layout demo')
        home.set_slot('main', CommentForm.factory())


        secondary_text = lots_of('The secondary column sits on '
                                 'the left side of the main column, '
                                 'spanning 1/3 of the body. ')
        home.set_slot('secondary', P.factory(text=secondary_text))


        header_text = lots_of('This text is located in the header,'
                              'which is added by the PageLayout. ')
        home.set_slot('header', P.factory(text=header_text))


        footer_text = lots_of('The footer spans the bottom of all the '
                              'columns on a PageLayout ')
        home.set_slot('footer', P.factory(text=footer_text))


class Comment(object):
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email address', required=True)
        fields.text = Field(label='Comment text')


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, 'myform')
        self.use_layout(FormLayout())
        comment = Comment()
        email_input = TextInput(self, comment.fields.email_address)
        self.layout.add_input(email_input)

        text_input = TextInput(self, comment.fields.text)
        self.layout.add_input(text_input)

        layout = ColumnLayout(ColumnOptions('left', size=ResponsiveSize(lg=6)),
                              ColumnOptions('right', size=ResponsiveSize(lg=6)))
        row = self.add_child(Div(view).use_layout(layout))

        left_p = P(view, text='This is in the left column of the row')
        row.layout.columns['left'].add_child(left_p)

        right_p = P(view, text='This is in the right column of the row')
        row.layout.columns['right'].add_child(right_p)

