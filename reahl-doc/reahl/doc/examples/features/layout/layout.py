
from __future__ import unicode_literals
from __future__ import print_function
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, P, YuiGrid, YuiUnit
from reahl.component.modelinterface import exposed, Field, EmailField

def lots_of(message):
    return message * 5

class LayoutUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style='basic')  

        home = self.define_view('/', title='Layout demo')
        home.set_slot('main', CommentForm.factory())

        home.set_slot('secondary', P.factory(text=lots_of('The secondary column sits on'
                                                   ' the left side of the main column. ')))
        home.set_slot('header', P.factory(text=lots_of('This text is located in the header,'
                                                'which is provided for in a TwoColumnPage. ')))
        home.set_slot('footer', P.factory(text=lots_of('The footer spans the bottom of all the '
                                                'columns on a TwoColumnPage ')))



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

        row = self.add_child(YuiGrid(view))
        [left_unit, right_unit] = row.add_children([YuiUnit(view, first=True), YuiUnit(view)])

        left_unit.add_child( P(view, text='This is in the left block of the row') ) 
        right_unit.add_child( P(view, text='This is in the right block of the row') ) 
