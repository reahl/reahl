# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from __future__ import print_function, unicode_literals, absolute_import, division
import os.path

from reahl.tofu import test
from reahl.tofu import temp_file_with
from reahl.tofu import vassert

from reahl.component.modelinterface import FileField, exposed, Event, UploadedFile
from reahl.web.ui import SimpleFileInput, Form, ButtonInput
from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath



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

        expected_content = b'some content'
        file_to_upload = temp_file_with(expected_content, mode='w+b')
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
                self.add_child(ButtonInput(self, domain_object.events.upload))


        wsgi_app = fixture.new_wsgi_app(child_factory=FileUploadForm.factory(), enable_js=False)
        fixture.reahl_server.set_app(wsgi_app)

        browser = fixture.driver_browser
        browser.open('/')

        browser.type(XPath.input_of_type('file'), file_to_upload.name)
        browser.click(XPath.button_labelled('Upload'))
        vassert( isinstance(domain_object.file, UploadedFile) )
        vassert( domain_object.file.filename == os.path.basename(file_to_upload.name) )
        with domain_object.file.open() as opened_file:
            read_contents = opened_file.read()
        vassert( read_contents == expected_content )


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
                self.add_child(ButtonInput(self, domain_object.events.upload))


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


