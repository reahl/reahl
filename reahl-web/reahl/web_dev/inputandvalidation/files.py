# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
# -*- encoding: utf-8 -*-
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
import os.path
import threading 

from nose.tools import istest
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import expected
from reahl.tofu import temp_file_with
from reahl.tofu import vassert

from reahl.component.exceptions import DomainException
from reahl.component.modelinterface import FileField, exposed, Event, Action, ValidationConstraint
from reahl.web.ui import SimpleFileInput, FileUploadInput, FileUploadPanel, Button, Form
from reahl.web.fw import UploadedFile
from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath
from reahl.webelixirimpl import PersistedFile


class FileUploadInputFixture(WebFixture):
    def file_was_uploaded(self, filename):
        return PersistedFile.query.filter_by(filename=os.path.basename(filename)).count() == 1

    file_to_upload1_name = 'file1.html'
    file_to_upload2_name = 'file2.gif'
    file_to_upload1_content = 'some content'
    file_to_upload2_content = 'some different content'

    def new_file_to_upload1(self):
        return temp_file_with(self.file_to_upload1_content, name=self.file_to_upload1_name)

    def new_file_to_upload2(self):
        return temp_file_with(self.file_to_upload2_content, name=self.file_to_upload2_name)

    def new_domain_object(self):
        class DomainObject(object):
            def __init__(self):
                self.throws_exception = False
                self.files = []
                self.submitted_file_info = {}
                self.submitted = False
               
            @exposed
            def fields(self, fields):
                fields.files = FileField(allow_multiple=True, label='Attached files')

            @exposed
            def events(self, events):
                events.submit = Event(label='Submit', action=Action(self.submit))
                
            def submit(self):
                if self.throws_exception:
                    raise DomainException()
                for f in self.files:
                    with f.open() as opened_file:
                        contents = opened_file.read()
                    self.submitted_file_info[f.filename] = (contents, f.content_type)
                self.submitted = True
                
        return DomainObject()

    def new_FileUploadForm(self):
        fixture = self
        class FileUploadForm(Form):
            def __init__(self, view):
                super(FileUploadForm, self).__init__(view, 'test')
                self.add_child(FileUploadInput(self, fixture.domain_object.fields.files))
                self.define_event_handler(fixture.domain_object.events.submit)
                self.add_child(Button(self, fixture.domain_object.events.submit))

        return FileUploadForm

    def new_wsgi_app(self, enable_js=False):
        return super(FileUploadInputFixture, self).new_wsgi_app(child_factory=self.FileUploadForm.factory(), enable_js=enable_js)

    def uploaded_file_is_listed(self, filename):
        return self.driver_browser.is_element_present('//ul/li/span[text()="%s"]' % os.path.basename(filename))


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


class StubbedFileUploadInputFixture(FileUploadInputFixture):
    run_hook_before = False
    run_hook_after = False
    def new_FileUploadForm(self):
        fixture = self
        class FileUploadInputStub(FileUploadInput):
            def create_html_input(self):
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

@istest
class FileTests(object):
    @test(WebFixture)
    def form_encoding(self, fixture):
        """The enctype of a Form changes to multipart/form-data if it contains an input for a file."""
        class DomainObject(object):
            @exposed
            def fields(self, fields):
                fields.file = FileField(allow_multiple=False, label='Attached files')

        domain_object = DomainObject()

        form = Form(fixture.view, 'testform')
        vassert( 'enctype' not in form.attributes.v )
        
        form.add_child(SimpleFileInput(form, domain_object.fields.file))
        vassert( form.attributes.v['enctype'] == 'multipart/form-data' )

    @test(WebFixture)
    def simple_file_input(self, fixture):
        """A SimpleFileInput is a Widget with which a user can choose one or more files.
           The SimpleFileInput transforms the chosen files to UploadedFile objects, and passes these
           to its associated FileField upon a Form submit."""

        file_to_upload = temp_file_with('some content')
        class DomainObject(object):
            def __init__(self):
               self.file = None

            @exposed
            def fields(self, fields):
                fields.file = FileField(allow_multiple=False, label='Attached files')

            @exposed
            def events(self, events):
                events.upload = Event(label='Upload')
                
        domain_object = DomainObject()                
        class FileUploadForm(Form):
            def __init__(self, view):
                super(FileUploadForm, self).__init__(view, 'test')
                self.add_child(SimpleFileInput(self, domain_object.fields.file))
                self.define_event_handler(domain_object.events.upload)
                self.add_child(Button(self, domain_object.events.upload))


        wsgi_app = fixture.new_wsgi_app(child_factory=FileUploadForm.factory(), enable_js=False)
        fixture.reahl_server.set_app(wsgi_app)

        browser = fixture.driver_browser
        browser.open('/')

        browser.type(XPath.input_of_type('file'), file_to_upload.name)
        browser.click(XPath.button_labelled('Upload'))
        vassert( isinstance(domain_object.file, UploadedFile) )
        vassert( domain_object.file.filename == os.path.basename(file_to_upload.name) )
        with domain_object.file.open() as opened_file:
            contents = opened_file.read()
        vassert( contents == 'some content' )


    @test(WebFixture)
    def simple_file_input_exceptions(self, fixture):
        """Usually, when a DomainException happens during a form submit Inputs save the input they received so that
           such input can be pre-populated on the screen rendered by a subsequent GET for a user to correct 
           possible mistakes and resubmit.

           In the case of a SimpleFileInput however, the UploadedFile objects that serve as user input
           to a SimpleFileInput are discarded when a DomainException happens.  This is because it is not
           possible to prepopulate its value using HTML or JS as this would be a security risk.
        """

        file_to_upload = temp_file_with('some content')
        failing_constraint = FailingConstraint('I am breaking')
        class DomainObject(object):
            def __init__(self):
               self.file = None

            @exposed
            def fields(self, fields):
                fields.file = FileField(allow_multiple=False, label='Attached files')
                # FailingConstraint is declared in module level scope for it to be pickleable
                fields.file.add_validation_constraint(failing_constraint)

            @exposed
            def events(self, events):
                events.upload = Event(label='Upload')
                
        domain_object = DomainObject()                
        class FileUploadForm(Form):
            def __init__(self, view):
                super(FileUploadForm, self).__init__(view, 'test')
                self.add_child(SimpleFileInput(self, domain_object.fields.file))
                self.define_event_handler(domain_object.events.upload)
                self.add_child(Button(self, domain_object.events.upload))


        wsgi_app = fixture.new_wsgi_app(child_factory=FileUploadForm.factory(), enable_js=False)
        fixture.reahl_server.set_app(wsgi_app)

        browser = fixture.driver_browser
        browser.open('/')

        browser.type(XPath.input_of_type('file'), file_to_upload.name)
        browser.click(XPath.button_labelled('Upload'))
        vassert( browser.is_element_present('//label[text()="I am breaking"]') )

        # Message is cleared on second attempt
        failing_constraint.fail = False
        browser.type(XPath.input_of_type('file'), file_to_upload.name)
        browser.click(XPath.button_labelled('Upload'))
        vassert( not browser.is_element_present('//label[text()="I am breaking"]') )


    @test(FileUploadInputFixture)
    def file_upload_input_basics(self, fixture):
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
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)
        browser.click(XPath.button_labelled('Upload'))

        vassert( not fixture.domain_object.submitted )
        vassert( fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
        vassert( not fixture.file_was_uploaded( fixture.file_to_upload2.name ) )

        # Upload a second file
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
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
        file1_content, file1_content_type = fixture.domain_object.submitted_file_info[os.path.basename(fixture.file_to_upload1.name)]
        vassert( file1_content == fixture.file_to_upload1_content )
        vassert( file1_content_type == 'text/html' )



    @test(FileUploadInputFixture)
    def file_upload_input_list_files(self, fixture):
        """The FileUploadInput displays a list of files that were uploaded so far, but is cleared 
           once the Form is submitted."""
        fixture.reahl_server.set_app(fixture.wsgi_app)

        browser = fixture.driver_browser
        browser.open('/')

        # Upload one file
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)
        browser.click(XPath.button_labelled('Upload'))

        vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
        vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

        # Upload a second file
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
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
    def file_upload_input_remove_files(self, fixture):
        """A user can remove files that were uploaded before the Form which contains the 
           FileUploadInput is submitted."""
        fixture.reahl_server.set_app(fixture.wsgi_app)

        browser = fixture.driver_browser
        browser.open('/')

        # Upload two files
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)
        browser.click(XPath.button_labelled('Upload'))
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
        browser.click(XPath.button_labelled('Upload'))

        # Remove file1
        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))

        vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
        vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

        # Only the one file is submitted
        browser.click( XPath.button_labelled('Submit') )
        vassert( fixture.domain_object.submitted_file_info.keys() == [fixture.file_to_upload2_name] )
        

    @test(FileUploadInputFixture)
    def file_upload_input_double_uploads(self, fixture):
        """The user is prevented from uploading more than one file with the same name.
        """
        fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=False))
        browser = fixture.driver_browser
        browser.open('/')

        # Upload two files with the same name
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)
        browser.click(XPath.button_labelled('Upload'))
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)
        browser.click(XPath.button_labelled('Upload'))
        
        # Expect an validation error message
        vassert( browser.is_element_present('//label[text()="uploaded files should all have different names"]') )
        vassert( fixture.file_was_uploaded(fixture.file_to_upload1.name) )

    @test(FileUploadInputFixture)
    def async_upload(self, fixture):
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
            browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)

        vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
        vassert( fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
        
        
    @test(LargeFileUploadInputFixture)
    def async_in_progress(self, fixture):
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
            browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name) # Upload will block, see fixture

        vassert( browser.is_element_present('//ul/li/progress') )
        progress = browser.get_attribute('//ul/li/progress', 'value')
        vassert( progress == '100' )
        browser.click(XPath.button_labelled('Cancel'))

        vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
        vassert( not fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
            

    @test(FileUploadInputFixture)
    def prevent_duplicate_upload_js(self, fixture):
        """The user is prevented from uploading more than one file with the same name on the client side.
        """
        fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

        browser = fixture.driver_browser
        browser.open('/')

        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)
        vassert( not browser.is_element_present('//label[text()="uploaded files should all have different names"]') )

        browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
        vassert( not browser.is_element_present('//label[text()="uploaded files should all have different names"]') )

        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)
        vassert( browser.is_element_present('//label[text()="uploaded files should all have different names"]') )

        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload2_name))
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
        vassert( not browser.is_element_present('//label[text()="uploaded files should all have different names"]') )

        
    @test(LargeFileUploadInputFixture)
    def prevent_form_submit(self, fixture):
        """The user is prevented from submitting the Form while one or more file uploads are still in progress."""
        fixture.run_hook_after = True
        fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

        browser = fixture.driver_browser
        browser.open('/')

        with fixture.reahl_server.in_background(wait_till_done_serving=False):
            browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name) # Upload will block, see fixture

        with browser.no_page_load_expected():
            browser.click( XPath.button_labelled('Submit'), wait=False )

            alert = fixture.web_driver.switch_to_alert()
            vassert( alert.text == 'Please try again when all files have finished uploading.' )
            alert.accept()
        
        
    @test(FileUploadInputFixture)
    def async_remove(self, fixture):
        """With javascript enabled, removing of uploaded files take place via ajax."""
        fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

        browser = fixture.driver_browser
        browser.open('/')

        # Upload two files
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)
        browser.click(XPath.button_labelled('Upload'))
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
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
        vassert( fixture.domain_object.submitted_file_info.keys() == [] )

    @test(BrokenFileUploadInputFixture)
    def async_upload_error(self, fixture):
        """If an error happens during (ajax) upload, the user is notified."""
        fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
        fixture.config.reahlsystem.debug = False # So that we don't see the exception output while testing
        browser = fixture.driver_browser
        browser.open('/')

        vassert( not browser.is_element_present(XPath.label_with_text('an error ocurred, please try again later.')) )

        with expected(Exception):
            browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)

        vassert( browser.is_element_present(XPath.label_with_text('an error occurred, please try again later.')) )
        vassert( not browser.is_element_enabled(XPath.button_labelled('Cancel')) )

    @test(ToggleValidationFixture)
    def async_upload_domain_exception(self, fixture):
        """When a DomainException happens upon uploading via JavaScript, 
           the form is replaced with a rerendered version from the server."""
        
        fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
        browser = fixture.driver_browser
        browser.open('/')

        fixture.make_validation_fail = False
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)

        fixture.make_validation_fail = True
        browser.execute_script('$(".reahl-upload-panel").children().addClass("reload_flag")')
        with browser.no_page_load_expected():
            browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
        has_class = browser.execute_script('$(".reahl-upload-panel").children().hasClass("reload_flag")')
        vassert( not has_class ) # ie, the UploadPanel has been reloaded

        # JS Stuff on re-rendered form still work
        
        # 1: Server-rendered validation message has been cleared
        vassert( browser.is_element_present(XPath.label_with_text('test validation message')) )
        fixture.make_validation_fail = False
        with browser.no_page_load_expected():
            browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
        vassert( not browser.is_element_present(XPath.label_with_text('test validation message')) )

        # 2: The remove button still happens via ajax
        with browser.no_page_load_expected():
            browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))
            browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload2_name))

    @test(LargeFileUploadInputFixture)
    def queueing_async_uploads(self, fixture):
        """Asynchronous uploads do not happen concurrently, they are queued one after another.
        """
        fixture.run_hook_after = True
        fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

        browser = fixture.driver_browser
        browser.open('/')

        vassert( not fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
        vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )

        with fixture.reahl_server.in_background(wait_till_done_serving=False):
            browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name) # Upload will block, see fixture
            browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name) # Upload will block, see fixture

        progress1 = browser.get_attribute('//ul/li[1]/progress', 'value')
        progress2 = browser.get_attribute('//ul/li[2]/progress', 'value')
        vassert( progress1 == '100' )
        vassert( progress2 == '0' )

        fixture.simulate_large_file_upload_done()

        vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
        vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )
        vassert( fixture.file_was_uploaded( fixture.file_to_upload1.name ) )
        vassert( fixture.file_was_uploaded( fixture.file_to_upload2.name ) )

    @test(PerFileConstrainedFileUploadInputFixture)
    def async_validation(self, fixture):
        """Validations are checked in JavaScript before uploading.
        """
        # Only tested for the FileUploadInput, as it uses the SimpleFileInput
        # in its own implementation, in a NestedForm, and has to pass on the
        # filesize constraint all the way. This way, we test all of that.
        fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))

        browser = fixture.driver_browser
        browser.open('/')

        vassert( not fixture.uploaded_file_is_listed( fixture.valid_file.name ) )
        vassert( not fixture.uploaded_file_is_listed( fixture.invalid_file.name ) )

        browser.type(XPath.input_of_type('file'), fixture.invalid_file.name)
        vassert( not fixture.uploaded_file_is_listed( fixture.invalid_file.name ) )
        vassert( browser.is_element_present(XPath.label_with_text(fixture.validation_error_message)) )

        browser.type(XPath.input_of_type('file'), fixture.valid_file.name)
        vassert( fixture.uploaded_file_is_listed( fixture.valid_file.name ) )
    
    @test(MaxNumberOfFilesFileUploadInputFixture)
    def async_number_files_validation(self, fixture):
        """A Field set to only allow a maximum number of files is checked for validity before uploading in JS.
        """
        # Only tested for the FileUploadInput, as it uses the SimpleFileInput
        # in its own implementation, in a NestedForm, and has to pass on the
        # filesize constraint all the way. This way, we test all of that.
        fixture.reahl_server.set_app(fixture.new_wsgi_app(enable_js=True))
        
        browser = fixture.driver_browser
        browser.open('/')

        vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )
        vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )

        browser.type(XPath.input_of_type('file'), fixture.file_to_upload1.name)
        vassert( fixture.uploaded_file_is_listed( fixture.file_to_upload1.name ) )

        browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
        vassert( not fixture.uploaded_file_is_listed( fixture.file_to_upload2.name ) )
        vassert( browser.is_element_present(XPath.label_with_text('a maximum of 1 files may be uploaded')) )

        browser.click(XPath.button_labelled('Remove', filename=fixture.file_to_upload1_name))
        browser.type(XPath.input_of_type('file'), fixture.file_to_upload2.name)
        vassert( not browser.is_element_present(XPath.label_with_text('a maximum of 1 files may be uploaded')) )

