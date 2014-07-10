# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import unicode_literals
from __future__ import print_function
import elixir

from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, \
                         P, H, InputGroup, FileUploadInput, SimpleFileInput
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action, FileField


class FileUploadUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style='basic')
        home = self.define_view('/', title='File upload demo')
        home.set_slot('main', CommentPostPanel.factory())


class Comment(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)
    
    email_address  = elixir.Field(elixir.UnicodeText)
    text           = elixir.Field(elixir.UnicodeText)
    attached_files = elixir.OneToMany('AttachedFile')
    
    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email address', required=True)
        fields.text          = Field(label='Comment', required=True)
        fields.uploaded_files = FileField(allow_multiple=True, max_size_bytes=4*1000*1000, max_files=4, accept=['text/*'])

    @exposed
    def events(self, events):
        events.submit = Event(label='Submit', action=Action(self.submit))

    def attach_uploaded_files(self):
        for f in self.uploaded_files:
            self.attached_files.append(AttachedFile(comment=self, filename=f.filename, contents=f.file_obj.read()))

    def submit(self):
        self.attach_uploaded_files()
        Session.add(self)


class AttachedFile(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    
    filename = elixir.Field(elixir.UnicodeText)
    contents = elixir.Field(elixir.LargeBinary)
    comment  = elixir.ManyToOne(Comment)

class CommentPostPanel(Panel):
    def __init__(self, view):
        super(CommentPostPanel, self).__init__(view)

        self.add_child(CommentForm(view))

        for comment in Comment.query.all():
            self.add_child(CommentBox(view, comment))


class CommentForm(Form):
    def __init__(self, view):
        super(CommentForm, self).__init__(view, 'myform')

        new_comment = Comment()
        self.add_child(H(view, 1, text='Leave a comment'))
        self.add_child(LabelledBlockInput(TextInput(self, new_comment.fields.email_address)))
        self.add_child(LabelledBlockInput(TextInput(self, new_comment.fields.text)))

        attachments = self.add_child(InputGroup(view, label_text='Attach files'))
        attachments.add_child(FileUploadInput(self, new_comment.fields.uploaded_files))

        self.define_event_handler(new_comment.events.submit)
        buttons = self.add_child(InputGroup(view, label_text=' '))
        buttons.add_child(Button(self, new_comment.events.submit))


class CommentBox(Panel):
    def __init__(self, view, comment):
        super(CommentBox, self).__init__(view)
        self.add_child(P(view, text='By %s: %s' % (comment.email_address, comment.text)))
        

