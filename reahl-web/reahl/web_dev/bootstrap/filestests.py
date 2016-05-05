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

from __future__ import print_function, unicode_literals, absolute_import, division

import six
import time
import os
import threading 

import webob


from reahl.tofu import vassert, scenario, expected, test, Fixture, temp_file_with
from reahl.stubble import stubclass


from reahl.webdev.tools import XPath
from reahl.web_dev.fixtures import WebFixture, WebBasicsMixin

from reahl.sqlalchemysupport import Session
from reahl.webdeclarative.webdeclarative import PersistedFile
from reahl.component.modelinterface import exposed, Field, Event, FileField, Action, ValidationConstraint
from reahl.component.exceptions import DomainException
from reahl.web.fw import WebExecutionContext

from reahl.web.bootstrap.ui import Span, Div, P, TextNode
from reahl.web.bootstrap.forms import Form, Label
from reahl.web.bootstrap.files import FileUploadInput, FileUploadPanel, Button, FormLayout, FileInput, FileInputButton





#----------------------------------
class FileInputButtonFixture(Fixture, WebBasicsMixin):

    def upload_button_indicates_focus(self):
        element = self.driver_browser.find_element(XPath.label_with_text('Choose file(s)'))
        return 'focus' in element.get_attribute('class')

    def new_domain_object(self):
        class DomainObject(object):
            files = []
            @exposed
            def fields(self, fields):
                fields.files = FileField(allow_multiple=True, label='Attached files')

            @exposed
            def events(self, events):
                events.submit = Event(label='Submit')

        return DomainObject()

    def new_FileUploadForm(self):
        fixture = self
        class FileUploadForm(Form):
            def __init__(self, view):
                super(FileUploadForm, self).__init__(view, 'test')
                self.add_child(FileInputButton(self, fixture.domain_object.fields.files))
                self.define_event_handler(fixture.domain_object.events.submit)
                self.add_child(Button(self, fixture.domain_object.events.submit))
        return FileUploadForm   

    def new_wsgi_app(self, enable_js=False):
        return super(FileInputButtonFixture, self).new_wsgi_app(child_factory=self.FileUploadForm.factory(), enable_js=enable_js)

    def new_webconfig(self):
        web = super(FileInputButtonFixture, self).new_webconfig()
        web.frontend_libraries.enable_experimental_bootstrap()
        return web


@test(FileInputButtonFixture)
def file_upload_button(fixture):
    """A FileInputButton lets you upload files using the browser's file choosing mechanism."""

    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = fixture.driver_browser
    browser.open('/')
    
    file_to_upload = temp_file_with('some content')

    browser.type(XPath.input_labelled('Choose file(s)'), file_to_upload.name)
    
    vassert( len(fixture.domain_object.files) == 0 )
    browser.click(XPath.button_labelled('Submit'))
    vassert( len(fixture.domain_object.files) == 1 )


@test(FileInputButtonFixture)
def file_upload_button_focus(fixture):
    """If the FileInputButton gets tab focus, it is styled to appear focussed."""

    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = fixture.driver_browser
    browser.open('/')

    vassert( browser.wait_for_not(fixture.upload_button_indicates_focus) )
    browser.focus_on(XPath.input_labelled('Choose file(s)'))
    vassert( browser.wait_for(fixture.upload_button_indicates_focus) )


#@test(FilesUploadFixture)
#def select_file_dialog_opens(fixture):
#    """Clicking on the FileInputButton opens up the browser choose file dialog."""
#
#    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
#    browser = fixture.driver_browser
#    browser.open('/')
#
#    browser.click(fixture.upload_button_xpath)
#    # We can't dismiss the local file dialog with selenium


class FileInputFixture(FileInputButtonFixture):
    def new_FileUploadForm(self):
        fixture = self
        class FileUploadForm(Form):
            def __init__(self, view):
                super(FileUploadForm, self).__init__(view, 'test')
                self.add_child(FileInput(self, fixture.domain_object.fields.files))
        return FileUploadForm   

    message_span_xpath = '//div[contains(@class, "reahl-bootstrapfileinput")]//span[2]'
    def message_displayed_is(self, message):
        return message == self.driver_browser.get_inner_html_for(self.message_span_xpath)

    def message_is_visible(self):
        return self.driver_browser.is_visible(self.message_span_xpath)

    def standard_file_input_is_visible(self):
        input_element = self.driver_browser.find_element(XPath.input_labelled('Choose file(s)'))
        return not input_element.value_of_css_property('width').startswith('0.')


@test(FileInputFixture)
def file_input_basics(fixture):
    """A FileInput is a FileInputButton combined with a area where the chosen file name is displayed."""
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = fixture.driver_browser
    browser.open('/')

    browser.wait_for(fixture.message_displayed_is, 'No files chosen')
    browser.type(XPath.input_labelled('Choose file(s)'), '/tmp/koos.html')
    browser.wait_for(fixture.message_displayed_is, 'koos.html')

    browser.type(XPath.input_labelled('Choose file(s)'), '/tmp/koos.html\n/tmp/jannie.html')
    browser.wait_for(fixture.message_displayed_is, '2 files chosen')


@test(FileInputFixture)
def i18n(fixture):
    """All messages have translations."""
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = fixture.driver_browser
    browser.open('/af/')

    browser.wait_for(fixture.message_displayed_is, 'Geen lêers gekies')
    browser.wait_for_element_present(XPath.input_labelled('Kies lêer(s)'))

    browser.type(XPath.input_labelled('Kies lêer(s)'), '/tmp/koos.html\n/tmp/jannie.html')
    browser.wait_for(fixture.message_displayed_is, '2 gekose lêers')


@test(FileInputFixture)
def file_input_without_js(fixture):
    """If JS available, we display a bootstrap-styled button, and associated span that look like a pretty version of a standard file input; otherwise we degrade to displaying only the standard file input"""
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = fixture.driver_browser
    browser.open('/')

    browser.wait_for(fixture.message_is_visible)
    browser.wait_for_not(fixture.standard_file_input_is_visible)
    
    browser.switch_styling(javascript=False)

    browser.wait_for_not(fixture.message_is_visible)
    browser.wait_for(fixture.standard_file_input_is_visible)







class FileUploadInputFixture(WebFixture):
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
        class DomainObject(object):
            def __init__(self):
                self.throws_exception = False
                self.files = []
                self.submitted_file_info = {}
                self.submitted = False
               
            @exposed
            def fields(self, fields):
                fields.files = FileField(allow_multiple=True, label='Attached files', required=True)

            @exposed
            def events(self, events):
                events.submit = Event(label='Submit', action=Action(self.submit))
                
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
                super(FileUploadForm, self).__init__(view, 'test')
                self.set_attribute('novalidate','novalidate')
                self.use_layout(FormLayout())
                self.layout.add_input(FileUploadInput(self, fixture.domain_object.fields.files))
                self.define_event_handler(fixture.domain_object.events.submit)
                self.add_child(Button(self, fixture.domain_object.events.submit))

        return FileUploadForm

    def new_wsgi_app(self, enable_js=False):
        return super(FileUploadInputFixture, self).new_wsgi_app(child_factory=self.FileUploadForm.factory(), enable_js=enable_js)

    def uploaded_file_is_listed(self, filename):
        return self.driver_browser.is_element_present('//ul/li/span[text()="%s"]/../input[@value="Remove"]' % os.path.basename(filename))

    def upload_file_is_queued(self, filename):
        return self.driver_browser.is_element_present('//ul/li/span[text()="%s"]/../input[@value="Cancel"]' % os.path.basename(filename))

    def new_webconfig(self):
        web = super(FileUploadInputFixture, self).new_webconfig()
        web.frontend_libraries.enable_experimental_bootstrap()
        return web


class ConstrainedFileUploadInputFixture(FileUploadInputFixture):
    def new_domain_object(self):
        fixture = self
        class DomainObject(object):
            @exposed
            def fields(self, fields):
                fields.files = fixture.file_field

            @exposed
            def events(self, events):
                events.submit = Event(label='Submit')

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
        super(ToggleableConstraint, self).__init__(error_message='test validation message')
        self.fixture = fixture
        
    def validate_input(self, unparsed_input):
        if self.fixture.make_validation_fail:
            raise self

    def __reduce__(self):
        reduced = super(ToggleableConstraint, self).__reduce__()
        pickle_dict = reduced[2]
        del pickle_dict['fixture']
        return reduced


class ToggleValidationFixture(FileUploadInputFixture):
    make_validation_fail = False
    def new_domain_object(self):
        fixture = self
        class DomainObject(object):
            @exposed
            def fields(self, fields):
                fields.files = FileField(allow_multiple=True, label='Attached files')
                fields.files.add_validation_constraint(ToggleableConstraint(fixture))
            @exposed
            def events(self, events):
                events.submit = Event(label='Submit')
                                
        return DomainObject()

    check_script = 'return $(".reahl-nested-form").find(".reload_flag").length > 0'
    def mark_nested_form(self):
        self.driver_browser.execute_script('$(".reahl-nested-form").children().addClass("reload_flag")')
        has_class = self.driver_browser.execute_script(self.check_script)
        assert has_class, 'Something is wrong, could not place flags for checking reloading of form'

    def nested_form_was_reloaded(self):
        has_class = self.driver_browser.execute_script(self.check_script)
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
                super(FileUploadPanelStub, self).upload_file()
                if fixture.run_hook_after:
                    fixture.file_upload_hook()

        class FileUploadForm(Form):
            def __init__(self, view):
                super(FileUploadForm, self).__init__(view, 'test')
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

    @property
    def web_driver(self):  
        return self.run_fixture.chrome_driver  # These tests only work on chrome

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



@test(FileUploadInputFixture)
def file_upload_input_basics(fixture):
    """A FileUploadInput allows its user to upload multiple files one by one before the Form that
       contains the FileUploadInput is submitted.  When the Form is finally submitted
       the FileField of the FileUploadInput receives all the files uploaded as UploadFile objects.
    """
    fixture.reahl_server.set_app(fixture.wsgi_app)

    browser = fixture.driver_browser
    browser.open('/')

    vassert( not fixture.domain_object.submitted )
    vassert( not fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
    vassert( not fixture.file_was_uploaded( fixture.file_to_upload2.name ) )

    # Upload one file
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))

    vassert( not fixture.domain_object.submitted )
    vassert( fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
    vassert( not fixture.file_was_uploaded( fixture.file_to_upload2.name ) )

    # Upload a second file
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.click(XPath.button_labelled('Upload'))

    vassert( not fixture.domain_object.submitted )
    vassert( fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
    vassert( fixture.file_was_uploaded( fixture.file_to_upload2.name ) )

    # Submit the form
    browser.click( XPath.button_labelled('Submit') )
    vassert( fixture.domain_object.submitted )

    # All uploaded files were submitted
    vassert( sorted(fixture.domain_object.submitted_file_info.keys()) == sorted([os.path.basename(f.name) 
                                                                           for f in [fixture.file_to_upload1, fixture.file_to_upload2]] ))

    # Files that were submitted are correct
    file1_content, file1_mime_type = fixture.domain_object.submitted_file_info[os.path.basename(fixture.file_to_upload1.name)]
    vassert( file1_content == fixture.file_to_upload1_content )
    vassert( file1_mime_type == 'text/html' )



@test(FileUploadInputFixture)
def file_upload_input_list_files(fixture):
    """The FileUploadInput displays a list of files that were uploaded so far, but is cleared 
       once the Form is submitted."""
    fixture.reahl_server.set_app(fixture.wsgi_app)

    browser = fixture.driver_browser
    browser.open('/')

    # Upload one file
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))

    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

    # Upload a second file
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.click(XPath.button_labelled('Upload'))

    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

    # Submit the form:
    # If an exception is raised, the list is NOT cleared
    fixture.domain_object.throws_exception = True
    browser.click( XPath.button_labelled('Submit') )
    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

    # Upon successful submit, the list IS cleared
    fixture.domain_object.throws_exception = False
    browser.click( XPath.button_labelled('Submit') )
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )


@test(FileUploadInputFixture)
def file_upload_input_remove_files(fixture):
    """A user can remove files that were uploaded before the Form which contains the 
       FileUploadInput is submitted."""
    fixture.reahl_server.set_app(fixture.wsgi_app)

    browser = fixture.driver_browser
    browser.open('/')

    # Upload two files
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.click(XPath.button_labelled('Upload'))

    # Remove file1
    browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))

    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

    # Only the one file is submitted
    browser.click( XPath.button_labelled('Submit') )
    vassert( list(fixture.domain_object.submitted_file_info.keys()) == [fixture.file_to_upload2_name] )


@test(FileUploadInputFixture)
def file_upload_input_double_uploads(fixture):
    """The user is prevented from uploading more than one file with the same name.
    """
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=False))
    browser = fixture.driver_browser
    browser.open('/')

    # Upload two files with the same name
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))

    # Expect an validation error message
    vassert( browser.is_element_present('//span[text()="uploaded files should all have different names"]') )
    vassert( fixture.file_was_uploaded(fixture.file_to_upload1.name) )

@test(FileUploadInputFixture)
def async_upload(fixture):
    """If JavaScript is enabled, the uploading of files happen in the background via ajax (without reloading the page)
       allowing the user to be busy with the rest of the form. The user does not need to click on the Upload button,
       uploading starts automatically upon choosing a file. The list of uploaded files is appropriately updated.
    """
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = fixture.driver_browser
    browser.open('/')

    vassert( not fixture.file_was_uploaded( fixture.file_to_upload1.name ) )

    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    with browser.no_page_load_expected():
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)

    vassert( browser.get_value(XPath.input_labelled('Choose file(s)')) == '' )  # Input is cleared for next file to be input
    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( fixture.file_was_uploaded( fixture.file_to_upload1.name ) )


@test(LargeFileUploadInputFixture)
def async_in_progress(fixture):
    """While a large file is being uploaded, a progress bar and a Cancel button are displayed. Clicking on the Cancel
       button stops the upload and clears the file name from the list of uploaded files.
    """
    fixture.run_hook_before = True
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = fixture.driver_browser
    browser.open('/')

    vassert( not fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )

    with fixture.reahl_server.in_background(wait_till_done_serving=False):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name) # Upload will block, see fixture

    vassert( browser.is_element_present('//ul/li/progress') )
    progress = browser.get_attribute('//ul/li/progress', 'value')
    vassert( progress == '100' )
    browser.click(XPath.button_labelled('Cancel'))

    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( not fixture.file_was_uploaded( fixture.file_to_upload1.name ) )


@test(LargeFileUploadInputFixture)
def cancelling_queued_upload(fixture):
    """Cancelling an upload that is still queued (upload not started yet) removes the file from the list
       and removed it from the queue of uploads.
    """
    fixture.run_hook_before = True
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = fixture.driver_browser
    browser.open('/')

    vassert( not fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( not fixture.file_was_uploaded( fixture.file_to_upload2.name ) )
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

    with fixture.reahl_server.in_background(wait_till_done_serving=False):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name) # Upload will block, see fixture
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name) # Upload will block, see fixture

    browser.wait_for(fixture.upload_file_is_queued, fixture.file_to_upload1.name)
    browser.wait_for(fixture.upload_file_is_queued, fixture.file_to_upload2.name)

    browser.click(XPath.button_labelled('Cancel', filename=fixture.file_to_upload2_name))

    browser.wait_for_not(fixture.upload_file_is_queued, fixture.file_to_upload2.name)
    fixture.simulate_large_file_upload_done()
    browser.wait_for(fixture.uploaded_file_is_listed, fixture.file_to_upload1.name)

    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )
    vassert( not fixture.file_was_uploaded( fixture.file_to_upload2.name ) )


@test(FileUploadInputFixture)
def prevent_duplicate_upload_js(fixture):
    """The user is prevented from uploading more than one file with the same name on the client side.
    """

    error_locator = XPath.span_containing('uploaded files should all have different names')
    def error_is_visible():
        return browser.is_visible(error_locator)

    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = fixture.driver_browser
    browser.open('/')

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.wait_for_not(error_is_visible)

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.wait_for_not(error_is_visible)

    with fixture.reahl_server.paused():
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
        vassert( not fixture.upload_file_is_queued(fixture.file_to_upload1.name) )
        browser.wait_for(error_is_visible)

    browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload2_name))
    browser.wait_for_not(error_is_visible)


@test(LargeFileUploadInputFixture)
def prevent_form_submit(fixture):
    """The user is prevented from submitting the Form while one or more file uploads are still in progress."""
    fixture.run_hook_after = True
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = fixture.driver_browser
    browser.open('/')

    with fixture.reahl_server.in_background(wait_till_done_serving=False):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name) # Upload will block, see fixture

    with browser.no_page_load_expected():
        browser.click( XPath.button_labelled('Submit'), wait=False )

        alert = fixture.web_driver.switch_to.alert
        vassert( alert.text == 'Please try again when all files have finished uploading.' )
        alert.accept()


@test(FileUploadInputFixture)
def async_remove(fixture):
    """With javascript enabled, removing of uploaded files take place via ajax."""
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = fixture.driver_browser
    browser.open('/')

    # Upload two files
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    browser.click(XPath.button_labelled('Upload'))
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.click(XPath.button_labelled('Upload'))

    # Remove file1
    with browser.no_page_load_expected():
        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))

    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

    # The javascript works on DOM elements that have been generated server-side as well:
    browser.refresh()
    with browser.no_page_load_expected():
        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload2_name))

    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

    # No files are submitted eventually
    browser.click( XPath.button_labelled('Submit') )
    vassert( list(fixture.domain_object.submitted_file_info.keys()) == [] )

@test(BrokenFileUploadInputFixture)
def async_upload_error(fixture):
    """If an error happens during (ajax) upload, the user is notified."""
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    fixture.config.reahlsystem.debug = False # So that we don't see the exception output while testing
    browser = fixture.driver_browser
    browser.open('/')

    vassert( not browser.is_element_present(XPath.label_with_text('an error ocurred, please try again later.')) )

    with expected(Exception):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)

    vassert( browser.wait_for_element_present(XPath.span_containing('an error occurred, please try again later.')) )
    vassert( not browser.is_element_enabled(XPath.button_labelled('Cancel')) )

@test(ToggleValidationFixture)
def async_upload_domain_exception(fixture):
    """When a DomainException happens upon uploading via JavaScript, 
       the form is replaced with a rerendered version from the server."""

    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
    browser = fixture.driver_browser
    browser.open('/')

    fixture.make_validation_fail = False
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)

    fixture.make_validation_fail = True
    fixture.mark_nested_form()
    with browser.no_page_load_expected():
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    vassert(fixture.nested_form_was_reloaded())

    # JS Stuff on re-rendered form still work

    # 1: Server-rendered validation message has been cleared
    vassert( browser.is_visible(XPath.span_containing('test validation message')) )
    fixture.make_validation_fail = False
    with browser.no_page_load_expected():
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    browser.wait_for_not(browser.is_visible, XPath.span_containing('test validation message'))

    # 2: The remove button still happens via ajax
    with browser.no_page_load_expected():
        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))
        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload2_name))

@test(LargeFileUploadInputFixture)
def queueing_async_uploads(fixture):
    """Asynchronous uploads do not happen concurrently, they are queued one after another.
    """
    fixture.run_hook_after = True
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = fixture.driver_browser
    browser.open('/')

    vassert( not fixture.file_was_uploaded(fixture.file_to_upload1.name) )
    vassert( not fixture.uploaded_file_is_listed(fixture.file_to_upload1.name) )

    with fixture.reahl_server.in_background(wait_till_done_serving=False):
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name) # Upload will block, see fixture
        browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name) # Upload will block, see fixture

    progress1 = browser.get_attribute('//ul/li[1]/progress', 'value')
    vassert(progress1 == '100')
    progress2 = browser.get_attribute('//ul/li[2]/progress', 'value')
    vassert(progress2 == '0')

    fixture.simulate_large_file_upload_done()
    browser.wait_for( fixture.uploaded_file_is_listed, fixture.file_to_upload2.name )

    vassert( fixture.uploaded_file_is_listed(fixture.file_to_upload1.name) )
    vassert( fixture.uploaded_file_is_listed(fixture.file_to_upload2.name) )
    vassert( fixture.file_was_uploaded(fixture.file_to_upload1.name) )
    vassert( fixture.file_was_uploaded(fixture.file_to_upload2.name) )

@test(PerFileConstrainedFileUploadInputFixture)
def async_validation(fixture):
    """Validations are checked in JavaScript before uploading.
    """
    # Only tested for the FileUploadInput, as it uses the FileInput
    # in its own implementation, in a NestedForm, and has to pass on the
    # filesize constraint all the way. This way, we test all of that.
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = fixture.driver_browser
    browser.open('/')

    vassert( not fixture.uploaded_file_is_listed( fixture.valid_file.name ) )
    vassert( not fixture.uploaded_file_is_listed( fixture.invalid_file.name ) )

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.invalid_file.name)
    vassert( not fixture.uploaded_file_is_listed( fixture.invalid_file.name ) )
    vassert( browser.is_element_present(XPath.span_containing(fixture.validation_error_message)) )

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.valid_file.name)
    vassert( fixture.uploaded_file_is_listed( fixture.valid_file.name ) )

@test(MaxNumberOfFilesFileUploadInputFixture)
def async_number_files_validation(fixture):
    """A Field set to only allow a maximum number of files is checked for validity before uploading in JS.
    """
    # Only tested for the FileUploadInput, as it uses the FileInput
    # in its own implementation, in a NestedForm, and has to pass on the
    # filesize constraint all the way. This way, we test all of that.
    fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

    browser = fixture.driver_browser
    browser.open('/')

    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload1.name)
    vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
    # Corner case: max are uploaded, but you've not asked to add to them yet:
    vassert( browser.wait_for_not(browser.is_visible, XPath.span_containing('a maximum of 1 files may be uploaded')) )

    # Normal case: max are uploaded, and you're asking to upload another:
    browser.type(XPath.input_labelled('Choose file(s)'), fixture.file_to_upload2.name)
    vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )
    vassert( browser.wait_for(browser.is_visible, XPath.span_containing('a maximum of 1 files may be uploaded')) )

    browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))
    vassert( browser.wait_for_not(browser.is_visible, XPath.span_containing('a maximum of 1 files may be uploaded')) )
