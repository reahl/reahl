
from reahl.web.fw import Region
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, P, YuiGrid, YuiUnit
from reahl.component.modelinterface import exposed, Field, EmailField

some_text = u'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'\
            u' Cras arcu libero, semper rutrum malesuada sit amet, mollis sed dui. '\
            u'Nulla eleifend mollis elit et luctus. Aliquam sollicitudin suscipit '\
            u'mattis. Morbi tincidunt enim non felis tempor rutrum. Donec id mi a '\
            u'neque rutrum dapibus. Nam sed nulla aliquam tellus feugiat mattis '\
            u'nec sit amet arcu. Ut non velit a risus hendrerit facilisis. Proin '\
            u'mattis orci sed sapien malesuada in consectetur eros pellentesque.'

class LayoutApp(Region):
    def assemble(self):
        self.define_main_window(TwoColumnPage, style=u'basic')  

        home = self.define_view(u'/', title=u'Layout demo')
        home.set_slot(u'main', CommentForm.factory())

        home.set_slot(u'secondary', P.factory(text=u'The secondary column sits on'
                                                   u' the left side of the main column. '+some_text))
        home.set_slot(u'header', P.factory(text=u'This text is located in the header,'
                                                u'which is provided for in a TwoColumnPage. '+some_text))
        home.set_slot(u'footer', P.factory(text=u'The footer spans the bottom of all the '
                                                u'columns on a TwoColumnPage '+ some_text))



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
