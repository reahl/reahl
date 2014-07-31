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
import os
import os.path

from reahl.tofu import Fixture
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import vassert, expected, temp_file_with
from reahl.stubble import SystemOutStub
from reahl.component.shelltools import Executable

from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.webdev.tools import XPath, Browser

from reahl.doc.examples.tutorial.hello.hello import HelloUI
from reahl.doc.examples.tutorial.helloapache import helloapache
from reahl.doc.examples.tutorial.hellonginx import hellonginx
from reahl.doc.examples.tutorial.slots.slots import SlotsUI
from reahl.doc.examples.features.tabbedpanel.tabbedpanel import TabbedPanelUI
from reahl.doc.examples.features.validation.validation import ValidationUI
from reahl.doc.examples.features.layout.layout import LayoutUI
from reahl.doc.examples.features.pageflow.pageflow import PageFlowUI
from reahl.doc.examples.features.persistence.persistence import PersistenceUI
from reahl.doc.examples.features.access.access import AccessUI
from reahl.doc.examples.features.i18nexample.i18nexample import TranslatedUI

from reahl.doc.fileupload import FileUploadUI, AttachedFile

from reahl.doc.basichtmlwidgets import BasicHTMLWidgetsUI
from reahl.doc.basichtmlinputs import BasicHTMLInputsUI

from reahl.doc.examples.tutorial.addressbook1 import addressbook1
from reahl.doc.examples.tutorial.addressbook2 import addressbook2
from reahl.doc.examples.tutorial.pageflow1 import pageflow1
from reahl.doc.examples.tutorial.pageflow2 import pageflow2
from reahl.doc.examples.tutorial.parameterised1 import parameterised1


class ExampleFixture(Fixture, WebBasicsMixin):
    def start_example_app(self):
        self.reahl_server.set_app(self.wsgi_app)

    def new_screenshot_directory(self):
        relative_path = 'doc/_build/screenshots'
        if not os.path.isdir(relative_path):
            os.makedirs(relative_path)
        return relative_path

    def new_screenshot_path(self, filename='screenshot.png'):
        return os.path.join(os.getcwd(), self.screenshot_directory, filename)
    
    def tab_is_active(self, tab_name):
        return self.driver_browser.execute_script('return window.jQuery("a:contains(\'%s\')").parent().hasClass("active")' % tab_name)

    def tab_contents_equals(self, expected_contents):
        return self.driver_browser.execute_script('return window.jQuery("div.reahl-tabbedpanel div p").html() == "%s"' % expected_contents)

    def error_is_visible(self):
        return self.driver_browser.execute_script('return window.jQuery(".reahl-form label.error").is(":visible")')

    def is_error_text(self, text):
        return text == self.driver_browser.get_text("//form/label[@class='error']")

    def get_main_slot_contents(self):
        return self.driver_browser.get_text('//div[@id="yui-main"]//p')

    def get_secondary_slot_contents(self):
        return self.driver_browser.get_text('//div[@id="yui-main"]/following-sibling::div/p')

    def uploaded_file_is_listed(self, filename):
        return self.driver_browser.is_element_present('//ul/li/span[text()="%s"]' % os.path.basename(filename))

    @scenario
    def hello(self):
        self.wsgi_app = self.new_wsgi_app(site_root=HelloUI)

    @scenario
    def hello_apache(self):
        self.wsgi_app = self.new_wsgi_app(site_root=helloapache.HelloUI)

    @scenario
    def hello_nginx(self):
        self.wsgi_app = self.new_wsgi_app(site_root=hellonginx.HelloUI)

    @scenario
    def tabbed_panel(self):
        self.wsgi_app = self.new_wsgi_app(site_root=TabbedPanelUI, enable_js=True)

    @scenario
    def validation(self):
        self.wsgi_app = self.new_wsgi_app(site_root=ValidationUI, enable_js=True)

    @scenario
    def layout(self):
        self.wsgi_app = self.new_wsgi_app(site_root=LayoutUI, enable_js=True)

    @scenario
    def pageflow(self):
        self.wsgi_app = self.new_wsgi_app(site_root=PageFlowUI, enable_js=True)

    @scenario
    def persistence(self):
        self.wsgi_app = self.new_wsgi_app(site_root=PersistenceUI, enable_js=True)

    @scenario
    def access_control(self):
        self.wsgi_app = self.new_wsgi_app(site_root=AccessUI, enable_js=True)

    @scenario
    def i18n(self):
        self.wsgi_app = self.new_wsgi_app(site_root=TranslatedUI, enable_js=True)

    @scenario
    def basichtmlinputs(self):
        self.wsgi_app = self.new_wsgi_app(site_root=BasicHTMLInputsUI, enable_js=True)

    @scenario
    def basichtmlwidgets(self):
        self.wsgi_app = self.new_wsgi_app(site_root=BasicHTMLWidgetsUI, enable_js=True)

    @scenario
    def fileupload(self):
        self.wsgi_app = self.new_wsgi_app(site_root=FileUploadUI, enable_js=True)
#        self.wsgi_app = self.new_wsgi_app(site_root=FileUploadUI, enable_js=False)

    @scenario
    def slots(self):
        self.wsgi_app = self.new_wsgi_app(site_root=SlotsUI, enable_js=True)

    @scenario
    def addressbook1(self):
        self.wsgi_app = self.new_wsgi_app(site_root=addressbook1.AddressBookUI)

    @scenario
    def addressbook2(self):
        self.wsgi_app = self.new_wsgi_app(site_root=addressbook2.AddressBookUI)

    @scenario
    def pageflow1(self):
        self.wsgi_app = self.new_wsgi_app(site_root=pageflow1.AddressBookUI)

    @scenario
    def pageflow2(self):
        self.wsgi_app = self.new_wsgi_app(site_root=pageflow2.AddressBookUI)

    @scenario
    def parameterised1(self):
        self.wsgi_app = self.new_wsgi_app(site_root=parameterised1.AddressBookUI)


@test(ExampleFixture)
def hit_home_page(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')

@test(ExampleFixture.tabbed_panel)
def widgets(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'Tab 1') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, 'A paragraph to give content to the first tab.') )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('tabbedpanel1.png'))

    fixture.driver_browser.click(XPath.link_with_text('Tab 2'))
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'Tab 2') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, 'And another ...  to give content to the second tab.') )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('tabbedpanel2.png'))

@test(ExampleFixture.validation)
def validation(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')
    vassert( fixture.driver_browser.wait_for_not(fixture.error_is_visible) )
    vassert( fixture.driver_browser.is_element_present('//input') )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('validation1.png'))
    
    fixture.driver_browser.type('//input', 'johndoe')
    fixture.driver_browser.press_tab('//input')
    vassert( fixture.driver_browser.wait_for(fixture.error_is_visible) )
    vassert( fixture.is_error_text('Email address should be a valid email address') )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('validation2.png'))

    fixture.driver_browser.type('//input', '')
    fixture.driver_browser.press_tab('//input')
    vassert( fixture.driver_browser.wait_for(fixture.error_is_visible) )
    vassert( fixture.is_error_text('Email address is required') )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('validation3.png'))

    fixture.driver_browser.type('//input', 'johndoe@some.org')
    fixture.driver_browser.press_tab('//input')
    vassert( fixture.driver_browser.wait_for_not(fixture.error_is_visible) )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('validation4.png'))

@test(ExampleFixture.layout)
def layout(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')
    fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe')
    fixture.driver_browser.press_tab('//input')
    vassert( fixture.driver_browser.wait_for(fixture.error_is_visible) )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('layout.png'))

@test(ExampleFixture.pageflow)
def pageflow(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')
    fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe@some.org')
    fixture.driver_browser.type(XPath.input_labelled('Comment'), '')
    with SystemOutStub() as output:
        fixture.driver_browser.click(XPath.button_labelled('Submit'))
        
        vassert( output.captured_output == 'johndoe@some.org submitted a comment:\nNone\n' )
        vassert( fixture.driver_browser.current_url.path == '/none' )
        output.capture_console_screenshot(fixture.new_screenshot_path('pageflow1.txt'))

        fixture.driver_browser.open('/')
        fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe@some.org')
        fixture.driver_browser.type(XPath.input_labelled('Comment'), 'some comment text')
        with SystemOutStub() as output:
            fixture.driver_browser.click(XPath.button_labelled('Submit'))

        vassert( output.captured_output == 'johndoe@some.org submitted a comment:\nsome comment text\n' )
        vassert( fixture.driver_browser.current_url.path == '/thanks' )
        output.capture_console_screenshot(fixture.new_screenshot_path('pageflow2.txt'))


@test(ExampleFixture.persistence)
def persistence(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')

    vassert( not fixture.driver_browser.is_element_present('//h1') )
    vassert( fixture.driver_browser.is_element_present('//form') )

    fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe@some.org')
    fixture.driver_browser.type(XPath.input_labelled('Comment'), 'some comment text')
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('persistence1.png'))

    fixture.driver_browser.click(XPath.button_labelled('Submit'))

    vassert( fixture.driver_browser.is_element_present('//form') )
    vassert( fixture.driver_browser.is_element_present('//form/following-sibling::div/p') )
    comment_text = fixture.driver_browser.get_text('//form/following-sibling::div/p')
    vassert( comment_text == 'By johndoe@some.org: some comment text' )

    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('persistence2.png'))

@test(ExampleFixture.access_control)
def access(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')
    vassert( fixture.driver_browser.is_element_present(XPath.input_labelled('Greyed out') ))
    vassert( not fixture.driver_browser.is_editable(XPath.input_labelled('Greyed out')) )
    vassert( fixture.driver_browser.is_element_present(XPath.button_labelled('Greyed out button')) )
    vassert( not fixture.driver_browser.is_editable(XPath.button_labelled('Greyed out button')) )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('access.png'))

    from reahl.doc.examples.features.access.access import Comment
    from reahl.component.exceptions import AccessRestricted
    comment = Comment()
    with expected(AccessRestricted):
        comment.do_something()

@test(ExampleFixture.i18n)
def i18n(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/some_page')
    vassert( fixture.get_main_slot_contents() == 'This is a translated string. The current URL is "/some_page".' )
    vassert( fixture.driver_browser.title == 'Translated example' )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('i18n1.png'))

    fixture.driver_browser.click(XPath.link_with_text('Afrikaans'))
    vassert( fixture.get_main_slot_contents() == 'Hierdie is \'n vertaalde string. Die huidige URL is "/af/some_page".' )
    vassert( fixture.driver_browser.title == 'Vertaalde voorbeeld' )
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('i18n2.png'))

@test(ExampleFixture.basichtmlwidgets)
def basichtmlwidgets(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')

@test(ExampleFixture.fileupload)
def fileupload(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')

    file1 = temp_file_with('some content in a file', 'file1.txt')
    file2 = temp_file_with('different content', 'file2.txt')
    file3 = temp_file_with('even more content', 'file3.txt')

    # Upload a file
    fixture.driver_browser.type('//input[@type="file"]', file1.name)
    vassert( fixture.uploaded_file_is_listed(file1.name) )

    # Upload a file
    fixture.driver_browser.type('//input[@type="file"]', file2.name)
    vassert( fixture.uploaded_file_is_listed(file2.name) )

    # Upload a file
    fixture.driver_browser.type('//input[@type="file"]', file3.name)
    vassert( fixture.uploaded_file_is_listed(file3.name) )

    # Delete file2 from uploaded files
    fixture.driver_browser.click(XPath.button_labelled('Remove', filename=os.path.basename(file2.name)))
    vassert( not fixture.uploaded_file_is_listed(file2.name) )

    # Submit the form
    fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe@some.org')
    fixture.driver_browser.type(XPath.input_labelled('Comment'), 'some comment text')
    fixture.driver_browser.click(XPath.button_labelled('Submit'))

    attached_file1 = AttachedFile.query.filter_by(filename=os.path.basename(file1.name)).one()
    attached_file3 = AttachedFile.query.filter_by(filename=os.path.basename(file3.name)).one()
    vassert( AttachedFile.query.count() == 2 )
    vassert( attached_file1.contents == 'some content in a file' )
    vassert( attached_file3.contents == 'even more content' )

@test(ExampleFixture.slots)
def slots(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')

    expected_main_contents = 'In this slot will be some main content for the view on /'
    expected_secondary_contents = 'Some secondary content related to /'
    main_contents = fixture.get_main_slot_contents()
    vassert( main_contents == expected_main_contents )
    secondary_contents = fixture.get_secondary_slot_contents()
    vassert( secondary_contents == expected_secondary_contents )
    
    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('slots1.png'))

    fixture.driver_browser.click(XPath.link_with_text('Page 2'))
    expected_main_contents = 'This could, for example, be where a photo gallery shows a large photo.'
    expected_secondary_contents = 'Thumbnails will then sit on the side of the big photo.'
    main_contents = fixture.get_main_slot_contents()
    vassert( main_contents == expected_main_contents )
    secondary_contents = fixture.get_secondary_slot_contents()
    vassert( secondary_contents == expected_secondary_contents )

    fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('slots2.png'))

@test(ExampleFixture.basichtmlinputs)
def basichtmlinputs(fixture):
    fixture.start_example_app()
    fixture.driver_browser.open('/')
    
@test(Fixture)
def model_examples(fixture):
    # These examples are built to run outside of our infrastructure, hence have to be run like this:
    for example in ['modeltests1.py', 'modeltests2.py', 'modeltests3.py']:
        Executable('nosetests').check_call(['reahl/doc/examples/tutorial/%s' % example ])

@test(ExampleFixture.addressbook1)
def test_addressbook1(fixture):
    john = addressbook1.Address(name='John', email_address='johndoe@some.org')
    john.save()

    browser = Browser(fixture.wsgi_app)
    browser.open('/')
    
    vassert( browser.is_element_present(XPath.paragraph_containing('John: johndoe@some.org')) )


@test(ExampleFixture.addressbook2)
def test_addressbook2(fixture):
    browser = Browser(fixture.wsgi_app)
    browser.open('/')
    
    browser.type(XPath.input_labelled('Name'), 'John') 
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    browser.click(XPath.button_labelled('Save'))
    
    vassert( browser.is_element_present(XPath.paragraph_containing('John: johndoe@some.org')) )


@test(ExampleFixture.pageflow1)
def test_pageflow1(fixture):
    browser = Browser(fixture.wsgi_app)
    browser.open('/')

    vassert( browser.is_element_present('//ul[contains(@class,"reahl-menu")]') )

    browser.click(XPath.link_with_text('Add an address'))
    vassert( browser.location_path == '/add' )
    
    browser.type(XPath.input_labelled('Name'), 'John') 
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    browser.click(XPath.button_labelled('Save'))
    
    vassert( browser.location_path == '/add' )

    browser.click(XPath.link_with_text('Addresses'))
    vassert( browser.location_path == '/' )
    vassert( browser.is_element_present(XPath.paragraph_containing('John: johndoe@some.org')) )


@test(ExampleFixture.pageflow2)
def test_pageflow2(fixture):
    browser = Browser(fixture.wsgi_app)
    browser.open('/')

    vassert( browser.is_element_present('//ul[contains(@class,"reahl-menu")]') )

    browser.click(XPath.link_with_text('Add an address'))
    vassert( browser.location_path == '/add' )
    
    browser.type(XPath.input_labelled('Name'), 'John') 
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    browser.click(XPath.button_labelled('Save'))
    
    vassert( browser.location_path == '/' )
    vassert( browser.is_element_present(XPath.paragraph_containing('John: johndoe@some.org')) )


@test(ExampleFixture.parameterised1)
def test_parameterised1(fixture):
    browser = Browser(fixture.wsgi_app)
    browser.open('/')

    browser.click(XPath.link_with_text('Add an address'))
    browser.type(XPath.input_labelled('Name'), 'John') 
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    browser.click(XPath.button_labelled('Save'))
    
    vassert( browser.location_path == '/' )
    browser.click(XPath.link_with_text('edit'))

    john = parameterised1.Address.query.one()
    vassert( browser.location_path == '/edit/%s' % john.id )
    browser.type(XPath.input_labelled('Name'), 'Johnny') 
    browser.type(XPath.input_labelled('Email'), 'johnny@walker.org')
    browser.click(XPath.button_labelled('Update'))
    
    vassert( browser.location_path == '/' )
    vassert( browser.is_element_present(XPath.paragraph_containing('Johnny: johnny@walker.org')) )


