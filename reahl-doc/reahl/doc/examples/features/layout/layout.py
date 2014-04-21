
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, P, YuiGrid, YuiUnit
from reahl.component.modelinterface import exposed, Field, EmailField

def lots_of(message):
    return message * 5

class LayoutUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style=u'basic')  

        home = self.define_view(u'/', title=u'Layout demo')
        home.set_slot(u'main', CommentForm.factory())

        home.set_slot(u'secondary', P.factory(text=lots_of(u'The secondary column sits on'
                                                   u' the left side of the main column. ')))
        home.set_slot(u'header', P.factory(text=lots_of(u'This text is located in the header,'
                                                u'which is provided for in a TwoColumnPage. ')))
        home.set_slot(u'footer', P.factory(text=lots_of(u'The footer spans the bottom of all the '
                                                u'columns on a TwoColumnPage ')))



class Comment(object):
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label=u'Email address', required=True)
        fields.text = Field(label=u'Comment text')

class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, u'myform')

        comment = Comment()
        self.add_child( LabelledBlockInput(TextInput(self, comment.fields.email_address)) )
        self.add_child( LabelledBlockInput(TextInput(self, comment.fields.text)) )

        row = self.add_child(YuiGrid(view))
        [left_unit, right_unit] = row.add_children([YuiUnit(view, first=True), YuiUnit(view)])

        left_unit.add_child( P(view, text=u'This is in the left block of the row') ) 
        right_unit.add_child( P(view, text=u'This is in the right block of the row') ) 
