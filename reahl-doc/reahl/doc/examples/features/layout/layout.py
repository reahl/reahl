
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, Form, TextInput, LabelledBlockInput, P, Panel
from reahl.web.pure import ColumnLayout, PageColumnLayout, UnitSize
from reahl.component.modelinterface import exposed, Field, EmailField

def lots_of(message):
    return message * 5

class LayoutUI(UserInterface):
    def assemble(self):
        layout = PageColumnLayout(('secondary', UnitSize('1/3')), ('main', UnitSize(default='2/3')))
        self.define_page(HTML5Page, style='basic').use_layout(layout)  

        home = self.define_view('/', title='Layout demo')
        home.set_slot('main', CommentForm.factory())

        home.set_slot('secondary', P.factory(text=lots_of('The secondary column sits on'
                                                   ' the left side of the main column, spanning 1/3 of the body. ')))
        home.set_slot('header', P.factory(text=lots_of('This text is located in the header,'
                                                'which is added by the PageColumnLayout. ')))
        home.set_slot('footer', P.factory(text=lots_of('The footer spans the bottom of all the '
                                                'columns on a PageColumnLayout ')))



class Comment(object):
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email address', required=True)
        fields.text = Field(label='Comment text')

class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, 'myform')

        comment = Comment()
        self.add_child( LabelledBlockInput(TextInput(self, comment.fields.email_address)) )
        self.add_child( LabelledBlockInput(TextInput(self, comment.fields.text)) )

        layout = ColumnLayout(('left', UnitSize('1/2')), ('right', UnitSize('1/2')))
        row = self.add_child(Panel(view).use_layout(layout))

        row.layout.columns['left'].add_child( P(view, text='This is in the left block of the row') ) 
        row.layout.columns['right'].add_child( P(view, text='This is in the right block of the row') ) 
