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


import webob


from reahl.tofu import vassert, scenario, expected, test, Fixture, temp_file_with
from reahl.stubble import stubclass


from reahl.webdev.tools import XPath
from reahl.web_dev.fixtures import WebFixture, WebBasicsMixin

from reahl.component.modelinterface import exposed, Field, Event, FileField, Action
from reahl.web.fw import WebExecutionContext

from reahl.web.bootstrap.ui import Form, Span, Label, Div, P, SimpleFileInput, Button, TextNode
from reahl.web.bootstrap.files import SimpleFileInput, FileInputButton
from reahl.web.bootstrap.libraries import Bootstrap4, ReahlBootstrap4Additions, Tether


#TODO:
# Names of FileInputButton/SimpleFileInput to be rethought







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
        web.frontend_libraries.add(Tether())
        web.frontend_libraries.add(Bootstrap4())
        web.frontend_libraries.add(ReahlBootstrap4Additions())
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
                self.add_child(SimpleFileInput(self, fixture.domain_object.fields.files))
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
    """A SimpleFileInput is a FileInputButton combined with a area where the chosen file name is displayed."""
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



