from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, Form, TextInput, LabelledBlockInput, P, Panel
from reahl.web.pure import ColumnLayout, PageColumnLayout, UnitSize
from reahl.component.modelinterface import exposed, Field, EmailField

def lots_of(message):
    return message * 5

class LayoutUI(UserInterface):
    def assemble(self):
        layout = PageColumnLayout(('secondary', UnitSize(default='1/3')), 
                                  ('main', UnitSize(default='2/3')))
        self.define_page(HTML5Page, style='basic').use_layout(layout)  

        home = self.define_view('/', title='Layout demo')
        home.set_slot('main', CommentForm.factory())


        secondary_text = lots_of('The secondary column sits on '
                                 'the left side of the main column, '
                                 'spanning 1/3 of the body. ')
        home.set_slot('secondary', P.factory(text=secondary_text))


        header_text = lots_of('This text is located in the header,'
                              'which is added by the PageColumnLayout. ')
        home.set_slot('header', P.factory(text=header_text))


        footer_text = lots_of('The footer spans the bottom of all the '
                              'columns on a PageColumnLayout ')
        home.set_slot('footer', P.factory(text=footer_text))



class Comment(object):
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email address', required=True)
        fields.text = Field(label='Comment text')

class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, 'myform')

        comment = Comment()
        email_input = TextInput(self, comment.fields.email_address)
        self.add_child(LabelledBlockInput(email_input))

        text_input = TextInput(self, comment.fields.text)
        self.add_child(LabelledBlockInput(text_input))

        layout = ColumnLayout(('left', UnitSize(default='1/2')), 
                              ('right', UnitSize(default='1/2')))
        row = self.add_child(Panel(view).use_layout(layout))

        left_p = P(view, text='This is in the left column of the row')
        row.layout.columns['left'].add_child(left_p) 

        right_p = P(view, text='This is in the right column of the row')
        row.layout.columns['right'].add_child(right_p) 
