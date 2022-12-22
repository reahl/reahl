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


import os
import threading 

from reahl.tofu import scenario, expected, Fixture, temp_file_with, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import XPath

from reahl.sqlalchemysupport import Session
from reahl.webdeclarative.webdeclarative import PersistedFile
from reahl.component.modelinterface import ExposedNames, Event, FileField, Action, ValidationConstraint
from reahl.component.exceptions import DomainException
from reahl.web.bootstrap.forms import Form
from reahl.web.bootstrap.files import FileUploadInput, FileUploadPanel, Button, FormLayout, FileInput, FileInputButton

from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class FileInputButtonFixture(Fixture):

    def upload_button_indicates_focus(self):
        element = self.web_fixture.driver_browser.find_element(XPath.label().with_text('Choose file(s)'))
        return 'focus' in element.get_attribute('class')

    def new_domain_object(self):
        class DomainObject:
            files = []
            fields = ExposedNames()
            fields.files = lambda i: FileField(allow_multiple=True, label='Attached files')

            events = ExposedNames()
            events.submit = lambda i: Event(label='Submit')

        return DomainObject()

    def new_FileUploadForm(self):
        fixture = self
        class FileUploadForm(Form):
            def __init__(self, view):
                super().__init__(view, 'test')
                self.add_child(FileInputButton(self, fixture.domain_object.fields.files))
                self.define_event_handler(fixture.domain_object.events.submit)
                self.add_child(Button(self, fixture.domain_object.events.submit))
        return FileUploadForm   


@with_fixtures(WebFixture, FileInputButtonFixture)
def test_file_upload_button(web_fixture, file_input_button_fixture):
    """A FileInputButton lets you upload files using the browser's file choosing mechanism."""

    fixture = file_input_button_fixture

    wsgi_app = web_fixture.new_wsgi_app(child_factory=file_input_button_fixture.FileUploadForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    file_to_upload = temp_file_with('some content')

    browser.type(XPath.input_labelled('Choose file(s)'), file_to_upload.name)

    assert len(fixture.domain_object.files) == 0 
    browser.click(XPath.button_labelled('Submit'))
    assert len(fixture.domain_object.files) == 1 


@with_fixtures(WebFixture, FileInputButtonFixture)
def test_file_upload_button_focus(web_fixture, file_input_button_fixture):
    """If the FileInputButton gets tab focus, it is styled to appear focussed."""

    fixture = file_input_button_fixture


    wsgi_app = web_fixture.new_wsgi_app(child_factory=file_input_button_fixture.FileUploadForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.wait_for_not(fixture.upload_button_indicates_focus) 
    browser.focus_on(XPath.input_labelled('Choose file(s)'))
    assert browser.wait_for(fixture.upload_button_indicates_focus) 


# @with_fixtures(WebFixture, FileInputButtonFixture)
# def test_select_file_dialog_opens(web_fixture, file_input_button_fixture):
#     """Clicking on the FileInputButton opens up the browser choose file dialog."""

#     fixture = file_input_button_fixture

#     wsgi_app = web_fixture.new_wsgi_app(child_factory=file_input_button_fixture.FileUploadForm.factory(), enable_js=True)
#     web_fixture.reahl_server.set_app(wsgi_app)
#     browser = web_fixture.driver_browser
#     browser.open('/')

#     import pdb; pdb.set_trace()
#     browser.click(XPath.span().with_text('Choose file(s)'))
#     browser.click(fixture.upload_button_xpath)
#     # We can't dismiss the local file dialog with selenium: yet?


class FileInputFixture(FileInputButtonFixture):
    def new_FileUploadForm(self):
        fixture = self
        class FileUploadForm(Form):
            def __init__(self, view):
                super().__init__(view, 'test')
                self.add_child(FileInput(self, fixture.domain_object.fields.files))
        return FileUploadForm   

    message_span_xpath = '//div[contains(@class, "reahl-bootstrapfileinput")]/span'
    def message_displayed_is(self, message):
        return message == self.web_fixture.driver_browser.get_inner_html_for(self.message_span_xpath)

    def message_is_visible(self):
        return self.web_fixture.driver_browser.is_visible(self.message_span_xpath)

    def standard_file_input_is_visible(self):
        input_element = self.web_fixture.driver_browser.find_element(XPath.input_labelled('Choose file(s)'))
        return not input_element.value_of_css_property('width').startswith('0.')


@with_fixtures(WebFixture, FileInputFixture)
def test_file_input_basics(web_fixture, file_input_fixture):
    """A FileInput is a FileInputButton combined with a area where the chosen file name is displayed."""
    fixture = file_input_fixture


    wsgi_app = web_fixture.new_wsgi_app(child_factory=file_input_fixture.FileUploadForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    file1 = temp_file_with('', name='file1.txt')
    file2 = temp_file_with('', name='file2.txt')
    browser.wait_for(fixture.message_displayed_is, 'No files chosen')
    browser.type(XPath.input_labelled('Choose file(s)'), file1.name)
    browser.wait_for(fixture.message_displayed_is, os.path.basename(file1.name))

    browser.type(XPath.input_labelled('Choose file(s)'), file2.name)
    browser.wait_for(fixture.message_displayed_is, '2 files chosen')


@with_fixtures(WebFixture, FileInputFixture)
def test_i18n(web_fixture, file_input_fixture):
    """All messages have translations."""
    fixture = file_input_fixture

    wsgi_app = web_fixture.new_wsgi_app(child_factory=file_input_fixture.FileUploadForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/af/')

    file1 = temp_file_with('', name='file1.txt')
    file2 = temp_file_with('', name='file2.txt')
    browser.wait_for(fixture.message_displayed_is, 'Geen lêers gekies')
    browser.wait_for_element_present(XPath.input_labelled('Kies lêer(s)'))

    browser.type(XPath.input_labelled('Kies lêer(s)'), file1.name)
    browser.type(XPath.input_labelled('Kies lêer(s)'), file2.name)
    browser.wait_for(fixture.message_displayed_is, '2 gekose lêers')


@with_fixtures(WebFixture, FileInputFixture)
def test_file_input_without_js(web_fixture, file_input_fixture):
    """If JS available, we display a bootstrap-styled button, and associated span that look like a pretty version of a standard file input; otherwise we degrade to displaying only the standard file input"""

    fixture = file_input_fixture


    wsgi_app = web_fixture.new_wsgi_app(child_factory=file_input_fixture.FileUploadForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)

    browser = web_fixture.driver_browser
    browser.open('/')

    browser.wait_for(fixture.message_is_visible)
    browser.wait_for_not(fixture.standard_file_input_is_visible)

    browser.switch_styling(javascript=False)

    browser.wait_for_not(fixture.message_is_visible)
    browser.wait_for(fixture.standard_file_input_is_visible)


@uses(web_fixture=WebFixture)
class FileUploadInputFixture(Fixture):

    def file_was_uploaded(self, filename):
        return Session.query(PersistedFile).filter_by(filename=os.path.basename(filename)).count() == 1

    file_to_upload1_name = 'file1.html'
    file_to_upload2_name = 'file2.gif'
    file_to_upload1_content = b'some content'
    file_to_upload2_content = b'some different content'

    def new_file_to_upload1(self):
        return temp_file_with(self.file_to_upload1_content, name=self.file_to_upload1_name, mode='w+b')

    def new_file_to_upload2(self):
        return temp_file_with(self.file_to_upload2_content, name=self.file_to_upload2_name, mode='w+b')

    def new_domain_object(self): 
        class DomainObject:
            def __init__(self):
                self.throws_exception = False
                self.files = []
                self.submitted_file_info = {}
                self.submitted = False
               
            fields = ExposedNames()
            fields.files = lambda i: FileField(allow_multiple=True, label='Attached files', required=True)

            events = ExposedNames()
            events.submit = lambda i: Event(label='Submit', action=Action(i.submit))
                
            def submit(self):
                if self.throws_exception:
                    raise DomainException()
                for f in self.files:
                    with f.open() as opened_file:
                        contents = opened_file.read()
                    self.submitted_file_info[f.filename] = (contents, f.mime_type)
                self.submitted = True
                
        return DomainObject()

    def new_FileUploadForm(self):
        fixture = self
        class FileUploadForm(Form):
            def __init__(self, view):
                super().__init__(view, 'test')
                self.set_attribute('novalidate','novalidate')
                self.use_layout(FormLayout())
                if self.exception:
                    self.layout.add_alert_for_domain_exception(self.exception)
                self.layout.add_input(FileUploadInput(self, fixture.domain_object.fields.files))
                self.define_event_handler(fixture.domain_object.events.submit)
                self.add_child(Button(self, fixture.domain_object.events.submit))

        return FileUploadForm

    def new_wsgi_app(self, enable_js=False):
        return self.web_fixture.new_wsgi_app(child_factory=self.FileUploadForm.factory(), enable_js=enable_js)

    def uploaded_file_is_listed(self, filename):
        return self.web_fixture.driver_browser.is_element_present('//ul/li/span[text()="%s"]/../input[@value="Remove"]' % os.path.basename(filename))

    def upload_file_is_queued(self, filename):
        return self.web_fixture.driver_browser.is_element_present('//ul/li/span[text()="%s"]/../input[@value="Cancel"]' % os.path.basename(filename))


class ConstrainedFileUploadInputFixture(FileUploadInputFixture):
    def new_domain_object(self):
        fixture = self
        class DomainObject:
            fields = ExposedNames()
            fields.files = lambda i: fixture.file_field

            events = ExposedNames()
            events.submit = lambda i: Event(label='Submit')

        return DomainObject()


class PerFileConstrainedFileUploadInputFixture(ConstrainedFileUploadInputFixture):
    @scenario
    def size_constrained(self):
        max_size = 13
        self.file_field = FileField(allow_multiple=True, max_size_bytes=max_size, label='Attached files')
        self.validation_error_message = 'files should be smaller than 13.0bytes'
        self.valid_file = temp_file_with('c'*max_size, name='valid_size.html')
        self.invalid_file = temp_file_with('c'*(max_size+1), name='invalid_size.html')

    @scenario
    def type_constrained(self):
        self.file_field = FileField(allow_multiple=True, accept=['text/*'])
        self.validation_error_message = 'files should be of type text/*'
        self.valid_file = temp_file_with('contents', name='valid.html')
        self.invalid_file = temp_file_with('contents', name='invalid.gif')


class MaxNumberOfFilesFileUploadInputFixture(ConstrainedFileUploadInputFixture):
    def new_file_field(self):
        return FileField(allow_multiple=True, max_files=1)


class ToggleableConstraint(ValidationConstraint):
    def __init__(self, fixture=None):
        super().__init__(error_message='test validation message')
        self.fixture = fixture
        
    def validate_input(self, unparsed_input):
        if self.fixture.make_validation_fail:
            raise self

    def __reduce__(self):
        reduced = super().__reduce__()
        pickle_dict = reduced[2]
        del pickle_dict['fixture']
        return reduced


class ToggleValidationFixture(FileUploadInputFixture):
    make_validation_fail = False
    def new_domain_object(self):
        fixture = self
        class DomainObject:
            fields = ExposedNames()
            def make_field(self):
                field = FileField(allow_multiple=True, label='Attached files')
                field.add_validation_constraint(ToggleableConstraint(fixture))
                return field
            fields.files = make_field
            events = ExposedNames()
            events.submit = lambda i: Event(label='Submit')
                                
        return DomainObject()

    check_script = 'return $(".reahl-nested-form").find(".reload_flag").length > 0'
    def mark_nested_form(self):
        self.web_fixture.driver_browser.execute_script('$(".reahl-nested-form").children().addClass("reload_flag")')
        has_class = self.web_fixture.driver_browser.execute_script(self.check_script)
        assert has_class, 'Something is wrong, could not place flags for checking reloading of form'

    def nested_form_was_reloaded(self):
        has_class = self.web_fixture.driver_browser.execute_script(self.check_script)
        return not has_class  # ie, the UploadPanel has been reloaded


class StubbedFileUploadInputFixture(FileUploadInputFixture):
    run_hook_before = False
    run_hook_after = False
    def new_FileUploadForm(self):
        fixture = self
        class FileUploadInputStub(FileUploadInput):
            def create_html_widget(self):
                return FileUploadPanelStub(self)
            
        class FileUploadPanelStub(FileUploadPanel):
            def upload_file(self):
                if fixture.run_hook_before:
                    fixture.file_upload_hook()
                super().upload_file()
                if fixture.run_hook_after:
                    fixture.file_upload_hook()

        class FileUploadForm(Form):
            def __init__(self, view):
                super().__init__(view, 'test')
                if self.exception:
                    self.use_layout(FormLayout())
                    self.layout.add_alert_for_domain_exception(self.exception)
                self.add_child(FileUploadInputStub(self, fixture.domain_object.fields.files))
                self.define_event_handler(fixture.domain_object.events.submit)
                self.add_child(Button(self, fixture.domain_object.events.submit))

        return FileUploadForm


class LargeFileUploadInputFixture(StubbedFileUploadInputFixture):
    def file_upload_hook(self):
        self.simulate_large_file_upload()

    def simulate_large_file_upload(self):
        self.upload_done.wait()

    def simulate_large_file_upload_done(self):
        self.upload_done.set()

    def new_upload_done(self):
        return threading.Event()


class BrokenFileUploadInputFixture(StubbedFileUploadInputFixture):
    run_hook_after = True
    def file_upload_hook(self):
        raise Exception('simulated exception condition')


class FailingConstraint(ValidationConstraint):
    fail = True
    def validate_input(self, unparsed_input):
        if self.fail:
            raise self


@with_fixtures(WebFixture, FileUploadInputFixture)
def test_file_upload_input_basics(web_fixture, file_upload_input_fixture):
    """A FileUploadInput allows its user to upload multiple files one by one before the Form that
       contains the FileUploadInput is submitted.  When the Form is finally submitted
       the FileField of the FileUploadInput receives all the files uploaded as UploadFile objects.
    """
    fixture = file_upload_input_fixture

    web_fixture.reahl_server.set_app(fixture.wsgi_app)

    browser = web_fixture.driver_browser
    browser.open('/')

    assert not fixture.domain_object.submitted 
    assert not fixture.file_was_uploaded( fixture.file_to_upload1.name ) 
    assert not fixture.file_was_uploaded( fixture.file_to_upload2.name ) 

    # Upload one file
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))

    assert not fixture.domain_object.submitted 
    assert fixture.file_was_uploaded( fixture.file_to_upload1.name ) 
    assert not fixture.file_was_uploaded( fixture.file_to_upload2.name ) 

    # Upload a second file
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.click(XPath.button_labelled('Upload'))

    assert not fixture.domain_object.submitted 
    assert fixture.file_was_uploaded( fixture.file_to_upload1.name ) 
    assert fixture.file_was_uploaded( fixture.file_to_upload2.name ) 

    # Submit the form
    browser.click( XPath.button_labelled('Submit') )
    assert fixture.domain_object.submitted 

    # All uploaded files were submitted
    assert sorted(fixture.domain_object.submitted_file_info.keys()) == sorted([os.path.basename(f.name)
                                                                           for f in [fixture.file_to_upload1, fixture.file_to_upload2]] )

    # Files that were submitted are correct
    file1_content, file1_mime_type = fixture.domain_object.submitted_file_info[os.path.basename(fixture.file_to_upload1.name)]
    assert file1_content == fixture.file_to_upload1_content 
    assert file1_mime_type == 'text/html' 


@with_fixtures(WebFixture, FileUploadInputFixture)
def test_file_upload_input_list_files(web_fixture, file_upload_input_fixture):
    """The FileUploadInput displays a list of files that were uploaded so far."""

    fixture = file_upload_input_fixture


    web_fixture.reahl_server.set_app(fixture.wsgi_app)

    browser = web_fixture.driver_browser
    browser.open('/')

    # Upload one file
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))

    assert fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) 

    # Upload a second file
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.click(XPath.button_labelled('Upload'))

    assert fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) 


@uses(file_upload_input_fixture=FileUploadInputFixture)
class ExceptionScenarios(Fixture):
    @scenario
    def no_exception(self):
        self.file_upload_input_fixture.domain_object.throws_exception = False

    @scenario
    def exception(self):
        self.file_upload_input_fixture.domain_object.throws_exception = True


@with_fixtures(WebFixture, FileUploadInputFixture, ExceptionScenarios)
def test_file_upload_input_list_files_clearing(web_fixture, file_upload_input_fixture, exception_scenario):
    """The list of uploaded files displayed by the FileUploadInput is cleared 
       once the Form is successfully submitted."""

    fixture = file_upload_input_fixture

    web_fixture.reahl_server.set_app(fixture.wsgi_app)

    browser = web_fixture.driver_browser
    browser.open('/')

    # Upload one file
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))

    assert fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 

    # Submit the form:
    browser.click( XPath.button_labelled('Submit') )
    if fixture.domain_object.throws_exception:
        assert fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    else:
        assert not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 


@with_fixtures(WebFixture, FileUploadInputFixture)
def test_file_upload_input_remove_files(web_fixture, file_upload_input_fixture):
    """A user can remove files that were uploaded but not yet submitted."""
    fixture = file_upload_input_fixture

    web_fixture.reahl_server.set_app(fixture.wsgi_app)

    browser = web_fixture.driver_browser
    browser.open('/')

    # Upload two files
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.click(XPath.button_labelled('Upload'))

    # Remove file1
    browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))

    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) 

    # Only the one file is submitted
    browser.click( XPath.button_labelled('Submit') )
    assert list(fixture.domain_object.submitted_file_info.keys()) == [fixture.file_to_upload2_name]


@with_fixtures(WebFixture, FileUploadInputFixture)
def test_file_upload_input_double_uploads(web_fixture, file_upload_input_fixture):
    """The user is prevented from uploading more than one file with the same name.
    """
    fixture = file_upload_input_fixture

    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=False))

    browser = web_fixture.driver_browser
    browser.open('/')

    # Upload two files with the same name
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))

    # Expect an validation error message
    assert browser.is_element_present('//span[text()="uploaded files should all have different names"]') 
    assert fixture.file_was_uploaded(fixture.file_to_upload1.name) 


@with_fixtures(WebFixture, FileUploadInputFixture)
def test_async_upload(web_fixture, file_upload_input_fixture):
    """If JavaScript is enabled, the uploading of files happen in the background via ajax (without reloading the page)
       allowing the user to be busy with the rest of the form. The user does not need to click on the Upload button,
       uploading starts automatically upon choosing a file. The list of uploaded files is appropriately updated.
    """
    fixture = file_upload_input_fixture

    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = web_fixture.driver_browser
    browser.open('/')

    assert not fixture.file_was_uploaded( fixture.file_to_upload1.name ) 

    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    with browser.no_page_load_expected():
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)

    assert browser.get_value(XPath.input_labelled('Choose file(s)')) == ''   # Input is cleared for next file to be input
    assert fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert fixture.file_was_uploaded( fixture.file_to_upload1.name ) 


@with_fixtures(WebFixture, LargeFileUploadInputFixture)
def test_async_in_progress(web_fixture, large_file_upload_input_fixture):
    """While a large file is being uploaded, a progress bar and a Cancel button are displayed. Clicking on the Cancel
       button stops the upload and clears the file name from the list of uploaded files.
    """
    fixture = large_file_upload_input_fixture


    fixture.run_hook_before = True
    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = web_fixture.driver_browser
    browser.open('/')

    assert not fixture.file_was_uploaded( fixture.file_to_upload1.name ) 
    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 

    with web_fixture.reahl_server.in_background(wait_till_done_serving=False):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name, wait_for_ajax=False) # Upload will block, see fixture

    assert browser.is_element_present('//ul/li/progress') 
    progress = browser.get_attribute('//ul/li/progress', 'value')
    assert progress == '100' 
    browser.click(XPath.button_labelled('Cancel'), wait_for_ajax=False)

    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert not fixture.file_was_uploaded( fixture.file_to_upload1.name ) 


@with_fixtures(WebFixture, LargeFileUploadInputFixture)
def test_cancelling_queued_upload(web_fixture, large_file_upload_input_fixture):
    """Cancelling an upload that is still queued (upload not started yet) removes the file from the list
       and removed it from the queue of uploads.
    """
    fixture = large_file_upload_input_fixture


    fixture.run_hook_before = True
    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = web_fixture.driver_browser
    browser.open('/')

    assert not fixture.file_was_uploaded( fixture.file_to_upload1.name ) 
    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert not fixture.file_was_uploaded( fixture.file_to_upload2.name ) 
    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) 

    with web_fixture.reahl_server.in_background(wait_till_done_serving=False):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name, wait_for_ajax=False) # Upload will block, see fixture
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name, wait_for_ajax=False) # Upload will block, see fixture

    browser.wait_for(fixture.upload_file_is_queued, fixture.file_to_upload1.name)
    browser.wait_for(fixture.upload_file_is_queued, fixture.file_to_upload2.name)

    browser.click(XPath.button_labelled('Cancel', filename=fixture.file_to_upload2_name), wait_for_ajax=False)

    browser.wait_for_not(fixture.upload_file_is_queued, fixture.file_to_upload2.name)
    fixture.simulate_large_file_upload_done()
    browser.wait_for(fixture.uploaded_file_is_listed, fixture.file_to_upload1.name)

    assert fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert fixture.file_was_uploaded( fixture.file_to_upload1.name ) 
    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) 
    assert not fixture.file_was_uploaded( fixture.file_to_upload2.name ) 


@with_fixtures(WebFixture, FileUploadInputFixture)
def test_prevent_duplicate_upload_js(web_fixture, file_upload_input_fixture):
    """The user is prevented from uploading more than one file with the same name on the client side.
    """

    fixture = file_upload_input_fixture


    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = web_fixture.driver_browser

    error_locator = XPath.span().including_text('uploaded files should all have different names')
    def error_is_visible():
        return browser.is_visible(error_locator)

    browser.open('/')

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.wait_for_not(error_is_visible)

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.wait_for_not(error_is_visible)

    with web_fixture.reahl_server.paused():
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
        assert not fixture.upload_file_is_queued(fixture.file_to_upload1.name) 
        browser.wait_for(error_is_visible)

    browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload2_name))
    browser.wait_for_not(error_is_visible)


@with_fixtures(WebFixture, LargeFileUploadInputFixture)
def test_prevent_form_submit(web_fixture, large_file_upload_input_fixture):
    """The user is prevented from submitting the Form while one or more file uploads are still in progress."""
    fixture = large_file_upload_input_fixture


    fixture.run_hook_after = True
    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = web_fixture.driver_browser
    browser.open('/')

    with web_fixture.reahl_server.in_background(wait_till_done_serving=False):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name, wait_for_ajax=False) # Upload will block, see fixture

    with browser.no_page_load_expected():
        browser.click( XPath.button_labelled('Submit'), wait=False, wait_for_ajax=False)
        alert = browser.web_driver.switch_to.alert
        assert alert.text == 'Please try again when all files have finished uploading.' 
        alert.accept()


@with_fixtures(WebFixture, FileUploadInputFixture)
def test_async_remove(web_fixture, file_upload_input_fixture):
    """With javascript enabled, removing of uploaded files take place via ajax."""

    fixture = file_upload_input_fixture

    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = web_fixture.driver_browser
    browser.open('/')

    # Upload two files
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.click(XPath.button_labelled('Upload'))

    # Remove file1
    with browser.no_page_load_expected():
        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))

    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) 

    # The javascript works on DOM elements that have been generated server-side as well:
    browser.refresh()
    with browser.no_page_load_expected():
        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload2_name))

    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) 

    # No files are submitted eventually
    browser.click( XPath.button_labelled('Submit') )
    assert list(fixture.domain_object.submitted_file_info.keys()) == [] 


@with_fixtures(WebFixture, BrokenFileUploadInputFixture)
def test_async_upload_error(web_fixture, broken_file_upload_input_fixture):
    """If an error happens during (ajax) upload, the user is notified."""
    fixture = broken_file_upload_input_fixture

    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = web_fixture.driver_browser
    browser.open('/')

    assert not browser.is_element_present(XPath.label().with_text('an error ocurred, please try again later.')) 

    with expected(Exception):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)

    assert browser.wait_for_element_present(XPath.span().including_text('an error occurred, please try again later.')) 
    assert not browser.is_element_enabled(XPath.button_labelled('Cancel')) 


@with_fixtures(WebFixture, ToggleValidationFixture)
def test_async_upload_domain_exception(web_fixture, toggle_validation_fixture):
    """When a DomainException happens upon uploading via JavaScript, 
       the form is replaced with a rerendered version from the server."""

    fixture = toggle_validation_fixture

    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = web_fixture.driver_browser
    browser.open('/')

    fixture.make_validation_fail = False
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)

    fixture.make_validation_fail = True
    fixture.mark_nested_form()
    with browser.no_page_load_expected():
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name, trigger_blur=False)
    assert fixture.nested_form_was_reloaded()

    # JS Stuff on re-rendered form still work

    # 1: Server-rendered validation message has been cleared
    assert browser.is_visible(XPath.span().including_text('test validation message')) 
    fixture.make_validation_fail = False
    with browser.no_page_load_expected():
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.wait_for_not(browser.is_visible, XPath.span().including_text('test validation message'))

    # 2: The remove button still happens via ajax
    with browser.no_page_load_expected():
        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))
        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload2_name))


@with_fixtures(WebFixture, LargeFileUploadInputFixture)
def test_queueing_async_uploads(web_fixture, large_file_upload_input_fixture):
    """Asynchronous uploads do not happen concurrently, they are queued one after another.
    """
    fixture = large_file_upload_input_fixture

    fixture.run_hook_after = True
    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = web_fixture.driver_browser
    browser.open('/')

    assert not fixture.file_was_uploaded(fixture.file_to_upload1.name) 
    assert not fixture.uploaded_file_is_listed(fixture.file_to_upload1.name) 

    with web_fixture.reahl_server.in_background(wait_till_done_serving=False):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name, wait_for_ajax=False) # Upload will block, see fixture
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name, wait_for_ajax=False) # Upload will block, see fixture

    progress1 = browser.get_attribute('//ul/li[1]/progress', 'value')
    assert progress1 == '100'
    progress2 = browser.get_attribute('//ul/li[2]/progress', 'value')
    assert progress2 == '0'

    fixture.simulate_large_file_upload_done()
    browser.wait_for( fixture.uploaded_file_is_listed, fixture.file_to_upload2.name )

    assert fixture.uploaded_file_is_listed(fixture.file_to_upload1.name) 
    assert fixture.uploaded_file_is_listed(fixture.file_to_upload2.name) 
    assert fixture.file_was_uploaded(fixture.file_to_upload1.name) 
    assert fixture.file_was_uploaded(fixture.file_to_upload2.name) 


@with_fixtures(WebFixture, PerFileConstrainedFileUploadInputFixture)
def test_async_validation(web_fixture, per_file_constrained_file_upload_input_fixture):
    """Validations are checked in JavaScript before uploading.
    """
    # Only tested for the FileUploadInput, as it uses the FileInput
    # in its own implementation, in a NestedForm, and has to pass on the
    # filesize constraint all the way. This way, we test all of that.
    fixture = per_file_constrained_file_upload_input_fixture

    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = web_fixture.driver_browser
    browser.open('/')

    assert not fixture.uploaded_file_is_listed( fixture.valid_file.name ) 
    assert not fixture.uploaded_file_is_listed( fixture.invalid_file.name ) 

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.invalid_file.name)
    assert not fixture.uploaded_file_is_listed( fixture.invalid_file.name ) 
    assert browser.is_element_present(XPath.span().including_text(fixture.validation_error_message)) 

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.valid_file.name)
    assert fixture.uploaded_file_is_listed( fixture.valid_file.name ) 


@with_fixtures(WebFixture, MaxNumberOfFilesFileUploadInputFixture)
def test_async_number_files_validation(web_fixture, max_number_of_files_file_upload_input_fixture):
    """A Field set to only allow a maximum number of files is checked for validity before uploading in JS.
    """
    # Only tested for the FileUploadInput, as it uses the FileInput
    # in its own implementation, in a NestedForm, and has to pass on the
    # filesize constraint all the way. This way, we test all of that.
    fixture = max_number_of_files_file_upload_input_fixture

    web_fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = web_fixture.driver_browser
    browser.open('/')

    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) 

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    assert fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) 
    # Corner case: max are uploaded, but you've not asked to add to them yet:
    assert browser.wait_for_not(browser.is_visible, XPath.span().including_text('a maximum of 1 files may be uploaded')) 

    # Normal case: max are uploaded, and you're asking to upload another:
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    assert not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) 
    assert browser.wait_for(browser.is_visible, XPath.span().including_text('a maximum of 1 files may be uploaded')) 

    browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))
    assert browser.wait_for_not(browser.is_visible, XPath.span().including_text('a maximum of 1 files may be uploaded')) 
