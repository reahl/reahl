# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
#-*- encoding: utf-8 -*-
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

"""
Widgets for uploading files.

.. versionadded:: 3.2

"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

from reahl.component.i18n import Translator
from reahl.component.modelinterface import exposed, Action, Event, Field, UploadedFile
from reahl.web.fw import WebExecutionContext
from reahl.web.ui import PrimitiveInput
from reahl.web.bootstrap.ui import Div, Span, Li, Button, NestedForm, Ul, ButtonLayout, FormLayout, FileInput

_ = Translator('reahl-web')




# Uses: reahl/web/reahl.fileuploadli.js
class FileUploadLi(Li):
    def __init__(self, form, remove_event, persisted_file, css_id=None):
        super(FileUploadLi, self).__init__(form.view, css_id=css_id)
        self.set_attribute('class', 'reahl-bootstrap-file-upload-li')
        self.add_child(Button(form, remove_event.with_arguments(filename=persisted_file.filename)))
        self.add_child(Span(self.view, persisted_file.filename))

    def get_js(self, context=None):
        return ['$(".reahl-bootstrap-file-upload-li").bootstrapfileuploadli();']


from reahl.web.ui import UniqueFilesConstraint

# Uses: reahl/web/reahl.fileuploadpanel.js
class FileUploadPanel(Div):
    def __init__(self, file_upload_input, css_id=None):
        super(FileUploadPanel, self).__init__(file_upload_input.view, css_id=css_id)
        self.set_attribute('class', 'reahl-bootstrap-file-upload-panel')
        self.file_upload_input = file_upload_input

        self.add_nested_form()
        self.add_uploaded_list()
        self.add_upload_controls()

    def add_nested_form(self):
        self.upload_form = self.add_child(NestedForm(self.view, '%s-%s-upload' % (self.input_form.css_id, self.bound_field.name)))
        self.upload_form.define_event_handler(self.events.upload_file)
        self.upload_form.define_event_handler(self.events.remove_file)
        self.upload_form.form.set_attribute('novalidate','novalidate')

    @property
    def name(self):
        return self.bound_field.variable_name

    def add_uploaded_list(self):
        ul = self.upload_form.add_child(Ul(self.view))
        for persisted_file in self.persisted_file_class.get_persisted_for_form(self.input_form, self.name):
            ul.add_child(FileUploadLi(self.upload_form.form, self.events.remove_file, persisted_file))

    def add_upload_controls(self):
        controls_panel = self.upload_form.add_child(Div(self.view)).use_layout(FormLayout())
        file_input = controls_panel.layout.add_input(FileInput(self.upload_form.form, self.fields.uploaded_file), hide_label=True)

        button_addon = file_input.html_representation.add_child(Span(self.view))
        button_addon.append_class('input-group-btn')
        button_addon.add_child(Button(self.upload_form.form, self.events.upload_file)).use_layout(ButtonLayout(style='primary'))


    @property
    def persisted_file_class(self):
        return self.file_upload_input.persisted_file_class

    @property
    def input_form(self):
        return self.file_upload_input.form

    @property
    def bound_field(self):
        return self.file_upload_input.bound_field

    @exposed
    def events(self, events):
        events.upload_file = Event(label=_('Upload'), action=Action(self.upload_file))
        events.remove_file = Event(label=_('Remove'),
                                   action=Action(self.remove_file, ['filename']),
                                   filename=Field(required=True))

    @exposed
    def fields(self, fields):
        fields.uploaded_file = self.bound_field.unbound_copy()
        fields.uploaded_file.disallow_multiple()
        fields.uploaded_file.label = _('Add file')
        fields.uploaded_file.make_optional()
        fields.uploaded_file.add_validation_constraint(UniqueFilesConstraint(self.input_form, self.bound_field.name))

    def attach_jq_widget(self, selector, widget_name, **options):
        def js_repr(value):
            if isinstance(value, six.string_types):
                return '"%s"' % value
            return value
        option_args = ','.join(['%s: %s' % (name, js_repr(value)) for name, value in options.items()])
        return '$(%s).%s({%s});' % (selector, widget_name, option_args)

    def get_js(self, context=None):
        selector = self.contextualise_selector('"#%s .reahl-bootstrap-file-upload-panel"' % self.input_form.css_id, context)
        unique_names_constraint = self.fields.uploaded_file.get_validation_constraint_of_class(UniqueFilesConstraint)
        js = self.attach_jq_widget(selector, 'bootstrapfileuploadpanel',
                    form_id=self.upload_form.form.css_id,
                    nested_form_id=self.upload_form.css_id,
                    input_form_id=self.input_form.css_id,
                    errorMessage=_('an error occurred, please try again later.'),
                    removeLabel=self.events.remove_file.label,
                    cancelLabel=_('Cancel'),
                    duplicateValidationErrorMessage=unique_names_constraint.message,
                    waitForUploadsMessage=_('Please try again when all files have finished uploading.'))
        return super(FileUploadPanel, self).get_js(context=context) + [js]

    def remove_file(self, filename):
        self.persisted_file_class.remove_persisted_for_form(self.input_form, self.name, filename)

    def upload_file(self):
        if self.uploaded_file is not None:
            self.persisted_file_class.add_persisted_for_form(self.input_form, self.name, self.uploaded_file)




class FileUploadInput(PrimitiveInput):
    """ """
    append_error = False
    add_default_attribute_source = False

    @property
    def persisted_file_class(self):
        config = WebExecutionContext.get_context().config
        return config.web.persisted_file_class

    def create_html_widget(self):
        return FileUploadPanel(self)

    def get_value_from_input(self, input_values):
        return [UploadedFile(f.filename, f.file_obj.read(), f.mime_type)
                 for f in self.persisted_file_class.get_persisted_for_form(self.form, self.name)]

    def enter_value(self, input_value):
        pass

