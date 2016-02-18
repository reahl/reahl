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

from reahl.tofu import vassert, scenario, expected, test, Fixture
from reahl.stubble import stubclass


from reahl.webdev.tools import XPath
from reahl.web_dev.fixtures import WebFixture, WebBasicsMixin

from reahl.component.modelinterface import exposed, Field, Event, FileField, Action
from reahl.web.fw import WebExecutionContext

from reahl.web.bootstrap.ui import Form, Span, Label, Div, P, SimpleFileInput, Button, TextNode
from reahl.web.bootstrap.files import FileInput, FileInputButton
from reahl.web.bootstrap.libraries import Bootstrap4, ReahlBootstrap4Additions, Tether

#TOTEST
# Focus, blur
# What shows in js and what without
# Filling in the filename when chosen (scenario for more than one file)
# i18n

class FilesSimpleFixture(WebFixture):

    def new_domain_object(self):
        class DomainObject(object):
            @exposed
            def fields(self, fields):
                fields.uploaded_file = FileField()
        return DomainObject()

    def new_form(self):
        return Form(self.view, 'myform')


@test(FilesSimpleFixture)
def file_input_basics(fixture):
    """"""
    file_input_wrap = FileInput(fixture.form, fixture.domain_object.fields.uploaded_file)

    [div] = file_input_wrap.children
    [file_input_button_span, filename_span] = div.children

    [file_input_button] = file_input_button_span.children
    [file_input_button_label] = file_input_button.children
    [simple_file_input, button_label] = file_input_button_label.children

    vassert( isinstance(simple_file_input, SimpleFileInput) )
    vassert( isinstance(file_input_button, FileInputButton) )

    vassert( 'reahl-bootstrapfileinputbutton' in file_input_button_label.get_attribute('class') )
    vassert( 'reahl-bootstrapfileinput' in div.get_attribute('class') )
    vassert( 'form-control' in filename_span.get_attribute('class') )




# class I18NFixture(FilesSimpleFixture):
#     # @scenario
#     # def default_context(self):
#     #     self.context = WebExecutionContext
#
#     @scenario
#     def alternate_context(self):
#         fixture = self
#         @stubclass(WebExecutionContext)
#         class AfrikaansContext(WebExecutionContext):
#             request = webob.Request.blank('/', charset='utf8')
#             config = fixture.config
#             session = None
#             #fixture.context.config.web.default_url_locale = 'af'
#
#             @property
#             def interface_locale(self):
#                 return 'af'
#
#         self.context = AfrikaansContext




@test(FilesSimpleFixture)
def i18n(fixture):
    """User-visible labels are internationalised."""
    @stubclass(WebExecutionContext)
    class AfrikaansContext(WebExecutionContext):
        request = webob.Request.blank('/', charset='utf8')
        config = fixture.config
        session = None
        #fixture.context.config.web.default_url_locale = 'af'

        @property
        def interface_locale(self):
            return 'af'

    with AfrikaansContext():
        file_input_wrap = FileInput(fixture.form, fixture.domain_object.fields.uploaded_file)

        [div] = file_input_wrap.children
        [file_input_button_span, filename_span] = div.children

        [file_input_button] = file_input_button_span.children
        [file_input_button_label] = file_input_button.children
        [simple_file_input, button_label] = file_input_button_label.children
        [button_label_text] = button_label.children

        [filename_span_text] = filename_span.children

        vassert( button_label_text.value == 'Kies lêer(s)')
        vassert( filename_span_text.value == 'Geen lêers gekies')

        # vassert( label_text.value == 'gekose lêers')





class FilesUploadFixture(Fixture, WebBasicsMixin):

    def element_has_focus_set(self, locator):
        self.driver_browser.does_element_have_attribute(locator, 'focus')

    def label_has_focus_set(self):
        return self.element_has_focus_set(self.label_xpath)

    @property
    def label_xpath(cls):
        #return XPath('//label[contains("@class", "reahl-bootstrapfileinputbutton")]')
        return XPath('//label')



    def new_domain_object(self):
        class DomainObject(object):
            def __init__(self):
                self.files = []

            @exposed
            def fields(self, fields):
                fields.files = FileField(allow_multiple=True, label='Attached files')

            # @exposed
            # def events(self, events):
            #     events.submit = Event(label='Submit', action=Action(self.submit))
            #
            # def submit(self):
            #     self.submitted = True
            #     for f in self.files:
            #         print (f)

        return DomainObject()

    def new_MainWidget(self):
        fixture = self
        class FileUploadForm(Form):
            def __init__(self, view):
                super(FileUploadForm, self).__init__(view, 'test')
                self.add_child(FileInput(self, fixture.domain_object.fields.files))
                #self.define_event_handler(fixture.domain_object.events.submit)
                #self.add_child(Button(self, fixture.domain_object.events.submit))

        return FileUploadForm

    def new_wsgi_app(self, enable_js=True):
        return super(FilesUploadFixture, self).new_wsgi_app(child_factory=self.MainWidget.factory(), enable_js=enable_js)


    def new_webconfig(self):
        web = super(FilesUploadFixture, self).new_webconfig()
        web.frontend_libraries.add(Tether())
        web.frontend_libraries.add(Bootstrap4())
        web.frontend_libraries.add(ReahlBootstrap4Additions())
        return web


@test(FilesUploadFixture)
def file_upload_button_focus(fixture):
    """"""

    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser
    browser.open('/')

    vassert( browser.is_element_present(fixture.label_xpath) )
    vassert( browser.wait_for_not(fixture.label_has_focus_set) )
    browser.mouse_over(fixture.label_xpath)
    vassert( browser.wait_for(fixture.label_has_focus_set) )

