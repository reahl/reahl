# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.



from sqlalchemy import Column, ForeignKey, UnicodeText, Integer, LargeBinary
from sqlalchemy.orm import relationship
from reahl.sqlalchemysupport import Session, Base
from reahl.component.modelinterface import ExposedNames, EmailField, Field, Event, Action, FileField
from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import FieldSet, Div, P
from reahl.web.bootstrap.files import FileUploadInput
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import Form, FormLayout, ButtonInput, TextInput



class FileUploadUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=ColumnLayout(
                                                              ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        home = self.define_view('/', title='File upload demo')
        home.set_slot('main', CommentPostPanel.factory())


class Comment(Base):
    __tablename__ = 'fileupload_comment'

    id = Column(Integer, primary_key=True)
    email_address  = Column(UnicodeText)
    text           = Column(UnicodeText)
    attached_files = relationship('AttachedFile', backref='comment')
    
    fields = ExposedNames()
    fields.email_address = lambda i: EmailField(label='Email address', required=True)
    fields.text          = lambda i: Field(label='Comment', required=True)
    fields.uploaded_files = lambda i: FileField(allow_multiple=True, max_size_bytes=4*1000*1000, max_files=4, accept=['text/*'])

    events = ExposedNames()
    events.submit = lambda i: Event(label='Submit', action=Action(i.submit))

    def attach_uploaded_files(self):
        for f in self.uploaded_files:
            self.attached_files.append(AttachedFile(comment=self, filename=f.filename, contents=f.contents))

    def submit(self):
        self.attach_uploaded_files()
        Session.add(self)


class AttachedFile(Base):
    __tablename__ = 'fileupload_attached_file'

    id = Column(Integer, primary_key=True)
    filename = Column(UnicodeText)
    contents = Column(LargeBinary)
    comment_id = Column(Integer, ForeignKey(Comment.id))


class CommentPostPanel(Div):
    def __init__(self, view):
        super().__init__(view)

        self.add_child(CommentForm(view))

        for comment in Session.query(Comment).all():
            self.add_child(CommentBox(view, comment))


class CommentForm(Form):
    def __init__(self, view):
        super().__init__(view, 'myform')

        new_comment = Comment()
        grouped_inputs = self.add_child(FieldSet(view, legend_text='Leave a comment'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, new_comment.fields.email_address))
        grouped_inputs.layout.add_input(TextInput(self, new_comment.fields.text))


        attachments = self.add_child(FieldSet(view, legend_text='Attach files'))
        attachments.use_layout(FormLayout())
        attachments.layout.add_input(FileUploadInput(self, new_comment.fields.uploaded_files), hide_label=True)

        self.define_event_handler(new_comment.events.submit)
        self.add_child(ButtonInput(self, new_comment.events.submit, style='primary'))


class CommentBox(Div):
    def __init__(self, view, comment):
        super().__init__(view)
        self.add_child(P(view, text='By %s: %s' % (comment.email_address, comment.text)))
        



