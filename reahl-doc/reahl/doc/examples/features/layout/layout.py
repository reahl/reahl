
from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P, Div, LiteralHTML
from reahl.web.bootstrap.forms import Form, TextInput, FormLayout, InlineFormLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.component.modelinterface import ExposedNames, Field, EmailField

def lots_of(message):
    return message * 5

class LayoutUI(UserInterface):
    def assemble(self):
        contents_layout = ColumnLayout(ColumnOptions('main', ResponsiveSize())).with_slots()

        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=contents_layout))

        home = self.define_view('/', title='Layout demo')
        home.set_slot('main', CommentForm.factory())

        header_text = lots_of('This text is located in the header,'
                              'which is added by the PageLayout. ')
        home.set_slot('header', P.factory(text=header_text))


        footer_text = lots_of('The footer spans the bottom of all the '
                              'columns on a PageLayout ')
        home.set_slot('footer', P.factory(text=footer_text))


class Comment:
    fields = ExposedNames()
    fields.email_address = lambda i: EmailField(label='Email address', required=True)
    fields.text = lambda i: Field(label='Comment text')


class CommentForm(Form):
    def __init__(self, view):
        super().__init__(view, 'myform')
        comment = Comment()

        layout = ColumnLayout(ColumnOptions('left', size=ResponsiveSize(lg=6)),
                              ColumnOptions('right', size=ResponsiveSize(lg=6)))
        
        # .add_child() returns the added child here:
        row = self.add_child(Div(view).use_layout(layout))
        left_column = row.layout.columns['left']

        # ... and .use_layout() returns the Widget it is called on
        section = Div(view).use_layout(FormLayout())
        left_column.add_child(section)

        email_input = TextInput(self, comment.fields.email_address)
        section.layout.add_input(email_input)

        inline_section = Div(view).use_layout(InlineFormLayout())
        left_column.add_child(inline_section)

        text_input = TextInput(self, comment.fields.text)
        inline_section.layout.add_input(text_input)

        right_column = row.layout.columns['right']
        right_column.add_child(LiteralHTML.from_restructured_text(view,
        '''
           This form has two columns. Inputs go 
           into the left one and this text into the right one.

           Some inputs are stacked and others are inlined.

           Arbitrarily complicated layouts can be created like this.'''))

