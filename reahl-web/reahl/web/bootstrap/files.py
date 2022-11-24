# Copyright 2016-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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
.. versionadded:: 3.2


Styled Inputs that allow a user to choose or upload files.

"""


from reahl.component.i18n import Catalogue
from reahl.component.modelinterface import ExposedNames, Action, Event, Field, UploadedFile
from reahl.component.context import ExecutionContext
import reahl.web.ui
from reahl.web.ui import UniqueFilesConstraint
from reahl.web.bootstrap.ui import Div, Span, Li, Ul
from reahl.web.bootstrap.forms import Button, NestedForm, FormLayout, Label


_ = Catalogue('reahl-web')


class _UnstyledHTMLFileInput(reahl.web.ui.SimpleFileInput):
    def __init__(self, form, bound_field):
        super().__init__(form, bound_field)
        self.append_class('form-control-file')


class FileInputButton(reahl.web.ui.WrappedInput):
    """A single button which activates the browser's file choice dialog
       when clicked. The chosen file will only be uploaded once the
       user clicks on any :class:`Button` associated with the same
       :class:`Form` as this Input.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`, must be of 
              type :class:`reahl.component.modelinterface.FileField`)

    """
    def __init__(self, form, bound_field):
        label = Label(form.view)
        self.simple_input = label.add_child(_UnstyledHTMLFileInput(form, bound_field))
        self.simple_input.html_representation.append_class('btn-secondary')
        label.add_child(Span(form.view, text=_('Choose file(s)')))
        super().__init__(self.simple_input)
        self.add_child(label)

        label.append_class('reahl-bootstrapfileinputbutton')
        label.append_class('btn')
        label.append_class('btn-primary')
        self.set_html_representation(label)

    @property
    def html_control(self):
        return self.simple_input.html_control

    def get_js(self, context=None):
        js = ['$(".reahl-bootstrapfileinputbutton").bootstrapfileinputbutton({});']
        return super().get_js(context=context) + js


class FileInput(reahl.web.ui.WrappedInput):
    """A visual combination of a two buttons and a status area. When the
    user clicks on the 'Choose file' button, the browser's file choice
    dialog is activated. Once chosen the file name that was chosen is
    shown in the status area. The last button will upload this file
    when clicked (it is automatically clicked if the user's JavaScript
    is enabled).

    :param form: (See :class:`~reahl.web.ui.Input`)
    :param bound_field: (See :class:`~reahl.web.ui.Input`, must be of 
           type :class:`reahl.component.modelinterface.FileField`)

    """
    def __init__(self, form, bound_field):
        file_input = FileInputButton(form, bound_field)
        super().__init__(file_input)

        self.input_group = self.add_child(Div(self.view))
        self.input_group.append_class('input-group')
        self.input_group.append_class('reahl-bootstrapfileinput')
        self.set_html_representation(self.input_group)

        div = self.input_group.add_child(Div(form.view))
        div.append_class('input-group-prepend')
        div.add_child(file_input)

        filename_input = self.input_group.add_child(Span(self.view, text=_('No files chosen')))
        filename_input.append_class('form-control')


    def get_js(self, context=None):
        js = ['$(".reahl-bootstrapfileinput").bootstrapfileinput({nfilesMessage: "%s", nofilesMessage: "%s"});' % \
              (_('files chosen'), _('No files chosen'))]
        return super().get_js(context=context) + js



# Uses: reahl/web/reahl.files.js
class FileUploadLi(Li):
    def __init__(self, form, remove_event, persisted_file, css_id=None):
        super().__init__(form.view, css_id=css_id)
        self.set_attribute('class', 'reahl-bootstrap-file-upload-li')
        self.add_child(Button(form, remove_event.with_arguments(filename=persisted_file.filename), style='secondary'))
        self.add_child(Span(self.view, persisted_file.filename))

    def get_js(self, context=None):
        return ['$(".reahl-bootstrap-file-upload-li").bootstrapfileuploadli();']



# Uses: reahl/web/reahl.files.js
class FileUploadPanel(Div):
    def __init__(self, file_upload_input, css_id=None):
        super().__init__(file_upload_input.view, css_id=css_id)
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
        return self.upload_form

    @property
    def name(self):
        return self.bound_field.name_in_input

    def add_uploaded_list(self):
        ul = self.upload_form.add_child(Ul(self.view))
        for persisted_file in self.persisted_file_class.get_persisted_for_form(self.input_form, self.name):
            ul.add_child(FileUploadLi(self.upload_form.form, self.events.remove_file, persisted_file))
        return ul

    def add_upload_controls(self):
        controls_panel = self.upload_form.add_child(Div(self.view)).use_layout(FormLayout())
        file_input = controls_panel.layout.add_input(FileInput(self.upload_form.form, self.fields.uploaded_file), hide_label=True)
        
        button_addon = file_input.html_representation.add_child(Div(self.view))
        button_addon.append_class('input-group-append')
        button_addon.add_child(Button(self.upload_form.form, self.events.upload_file, style='secondary', outline=True))
        return controls_panel

    @property
    def persisted_file_class(self):
        return self.file_upload_input.persisted_file_class

    @property
    def input_form(self):
        return self.file_upload_input.form

    @property
    def bound_field(self):
        return self.file_upload_input.bound_field

    events = ExposedNames()
    events.upload_file = lambda i: Event(label=_('Upload'), action=Action(i.upload_file))
    events.remove_file = lambda i: Event(label=_('Remove'),
                                         action=Action(i.remove_file, ['filename']),
                                         filename=Field(required=True))

    fields = ExposedNames()
    def create_uploaded_file_field(i):
        field = i.bound_field.unbound_copy()
        field.disallow_multiple()
        field.label = _('Add file')
        field.make_optional()
        field.add_validation_constraint(UniqueFilesConstraint(i.input_form, i.bound_field.name_in_input))
        return field
    fields.uploaded_file = create_uploaded_file_field

    def attach_jq_widget(self, selector, widget_name, **options):
        def js_repr(value):
            if isinstance(value, str):
                return '"%s"' % value
            return value
        option_args = ','.join(['%s: %s' % (name, js_repr(value)) for name, value in options.items()])
        return '$(%s).%s({%s});' % (selector, widget_name, option_args)

    def get_js(self, context=None):
        selector = self.contextualise_selector('".reahl-bootstrap-file-upload-panel"', context)
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
        return super().get_js(context=context) + [js]

    def remove_file(self, filename):
        self.persisted_file_class.remove_persisted_for_form(self.input_form, self.name, filename)

    def upload_file(self):
        if self.uploaded_file is not None:
            self.persisted_file_class.add_persisted_for_form(self.input_form, self.name, self.uploaded_file)


class FileUploadInput(reahl.web.ui.Input):
    """A Widget that allows the user to upload several files.  FileUploadInput
    makes use of JavaScript to save a user some time: once you choose a file, 
    it is immediately uploaded to the server in the background so that you can
    continue choosing more files.

    Controls are provided so you can cancel uploads that are in
    progress or remove ones that have finished. While a file is
    uploading a progress bar is also shown.

    :param form: (See :class:`~reahl.web.ui.Input`)
    :param bound_field: (See :class:`~reahl.web.ui.Input`, must be of 
              type :class:`reahl.component.modelinterface.FileField`)
    :keyword ignore_concurrent_change: If True, don't check for possible concurrent changes by others to this input (just override such changes).


    .. versionchanged:: 5.0
       Subclass of :class:`~reahl.web.ui.Input` and not :class:`~reahl.web.ui.PrimitiveInput`

    .. versionchanged:: 5.0
       Added `ignore_concurrency_change`

    """
    is_for_file = False

    def __init__(self, form, bound_field, ignore_concurrency_change=False):
        super().__init__(form, bound_field)
        
        self.ignore_concurrency_change = ignore_concurrency_change

        form.register_input(self) # bound_field must be set for this registration to work

        self.set_html_representation(self.add_child(self.create_html_widget()))


    def get_concurrency_hash_strings(self):
        if not self.ignore_concurrency_change:
            yield self.original_database_value
            
    @property
    def name(self):
        return self.bound_field.name_in_input

    def get_ocurred_event(self):
        return None

    @property
    def persisted_file_class(self):
        config = ExecutionContext.get_context().config
        return config.web.persisted_file_class

    def create_html_widget(self):
        return FileUploadPanel(self)

    @property
    def html_control(self):
        return None

    def accept_input(self, input_values):
        value = [UploadedFile(f.filename, f.file_obj.read(), f.mime_type)
                 for f in self.persisted_file_class.get_persisted_for_form(self.form, self.name)]
        self.bound_field.from_input(value)

    def persist_input(self, input_values):
        pass
