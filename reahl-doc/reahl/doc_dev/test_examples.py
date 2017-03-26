# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import os
import os.path

from reahl.tofu import Fixture
from reahl.tofu import scenario, expected, temp_file_with
from reahl.stubble import SystemOutStub
from reahl.component.shelltools import Executable

from reahl.sqlalchemysupport import Session
from reahl.webdev.tools import XPath, Browser

from reahl.doc.examples.tutorial.hello.hello import HelloUI
from reahl.doc.examples.tutorial.helloapache import helloapache
from reahl.doc.examples.tutorial.hellonginx import hellonginx
from reahl.doc.examples.tutorial.slotsbootstrap.slotsbootstrap import SlotsUI
from reahl.doc.examples.features.tabbedpanel.tabbedpanel import TabbedPanelUI
from reahl.doc.examples.features.carousel.carousel import CarouselUI
from reahl.doc.examples.features.validation.validation import ValidationUI
from reahl.doc.examples.features.layout.layout import LayoutUI
from reahl.doc.examples.features.pageflow.pageflow import PageFlowUI
from reahl.doc.examples.features.persistence.persistence import PersistenceUI
from reahl.doc.examples.features.access.access import AccessUI
from reahl.doc.examples.features.i18nexample.i18nexample import TranslatedUI

from reahl.doc.examples.web.fileupload.fileupload import FileUploadUI, AttachedFile

from reahl.doc.examples.web.basichtmlwidgets.basichtmlwidgets import BasicHTMLWidgetsUI
from reahl.doc.examples.web.basichtmlinputs.basichtmlinputs import BasicHTMLInputsUI

from reahl.doc.examples.tutorial.addressbook1 import addressbook1
from reahl.doc.examples.tutorial.addressbook2 import addressbook2
from reahl.doc.examples.tutorial.addressbook2bootstrap import addressbook2bootstrap
from reahl.doc.examples.tutorial.bootstrapgrids import bootstrapgrids
from reahl.doc.examples.tutorial.pageflow1bootstrap import pageflow1bootstrap
from reahl.doc.examples.tutorial.pageflow2bootstrap import pageflow2bootstrap
from reahl.doc.examples.tutorial.parameterised1bootstrap import parameterised1bootstrap

# noinspection PyUnresolvedReferences
from reahl.web_dev.fixtures import web_fixture
# noinspection PyUnresolvedReferences
from reahl.sqlalchemysupport_dev.fixtures import sql_alchemy_fixture
# noinspection PyUnresolvedReferences
from reahl.domain_dev.fixtures import party_account_fixture


class ExampleFixture(Fixture):
    def __init__(self, web_fixture):
        super(ExampleFixture, self).__init__()
        self.web_fixture = web_fixture

    def start_example_app(self):
        self.web_fixture.reahl_server.set_app(self.wsgi_app)

    def new_screenshot_directory(self):
        relative_path = 'doc/_build/screenshots'
        if not os.path.isdir(relative_path):
            os.makedirs(relative_path)
        return relative_path

    def new_screenshot_path(self, filename='screenshot.png'):
        return os.path.join(os.getcwd(), self.screenshot_directory, filename)

    def tab_is_active(self, tab_name):
        return self.web_fixture.driver_browser.execute_script('return window.jQuery("a:contains(\'%s\')").hasClass("active")' % tab_name)

    def tab_contents_equals(self, expected_contents):
        return self.web_fixture.driver_browser.execute_script('return window.jQuery("div.tab-content div.active p").html() == "%s"' % expected_contents)

    def carousel_caption_equals(self, expected_contents):
        return self.web_fixture.driver_browser.execute_script('return window.jQuery("div.carousel-caption:visible p").html() == "%s"' % expected_contents)

    def error_is_visible(self):
        return self.web_fixture.driver_browser.execute_script('return window.jQuery(".reahl-form span.has-danger").is(":visible")')

    def is_error_text(self, text):
        return text == self.web_fixture.driver_browser.get_text("//form//span[contains(@class,'has-danger')]")

    def get_text_in_p(self):
        return self.web_fixture.driver_browser.get_text('//p')

    def get_main_slot_contents(self):
        return self.web_fixture.driver_browser.get_text('//div[contains(@class, "column-main")]/*')

    def get_secondary_slot_contents(self):
        return self.web_fixture.driver_browser.get_text('//div[contains(@class, "column-secondary")]/*')

    def uploaded_file_is_listed(self, filename):
        return self.web_fixture.driver_browser.is_element_present('//ul/li/span[text()="%s"]' % os.path.basename(filename))

    @scenario
    def hello(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=HelloUI)

    @scenario
    def hello_apache(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=helloapache.HelloUI)

    @scenario
    def hello_nginx(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=hellonginx.HelloUI)

    @scenario
    def tabbed_panel(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=TabbedPanelUI, enable_js=True)

    @scenario
    def carousel_panel(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=CarouselUI, enable_js=True)

    @scenario
    def validation(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=ValidationUI, enable_js=True)

    @scenario
    def layout(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=LayoutUI, enable_js=True)

    @scenario
    def pageflow(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=PageFlowUI, enable_js=True)

    @scenario
    def persistence(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=PersistenceUI, enable_js=True)

    @scenario
    def access_control(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=AccessUI, enable_js=True)

    @scenario
    def i18n(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=TranslatedUI, enable_js=True)

    @scenario
    def basichtmlinputs(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=BasicHTMLInputsUI, enable_js=True)

    @scenario
    def basichtmlwidgets(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=BasicHTMLWidgetsUI, enable_js=True)

    @scenario
    def fileupload(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=FileUploadUI, enable_js=True)

    @scenario
    def slots(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=SlotsUI, enable_js=True)

    @scenario
    def addressbook1(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=addressbook1.AddressBookUI)

    @scenario
    def addressbook2(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=addressbook2.AddressBookUI)

    @scenario
    def pageflow1(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=pageflow1bootstrap.AddressBookUI)

    @scenario
    def pageflow2(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=pageflow2bootstrap.AddressBookUI)

    @scenario
    def parameterised1(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=parameterised1bootstrap.AddressBookUI)

    @scenario
    def addressbook2bootstrap(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=addressbook2bootstrap.AddressBookUI, enable_js=True)

    @scenario
    def bootstrapgrids(self):
        self.wsgi_app = self.web_fixture.new_wsgi_app(site_root=bootstrapgrids.BootstrapGridsUI, enable_js=True)


example_fixture = ExampleFixture.as_pytest_fixture()

def test_hit_home_page(web_fixture, example_fixture):
    example_fixture.start_example_app()
    web_fixture.driver_browser.open('/')


tabbed_panel_scenario = ExampleFixture.tabbed_panel.as_pytest_fixture()

def test_widgets_using_factories(web_fixture, tabbed_panel_scenario):
    fixture = tabbed_panel_scenario
    fixture.start_example_app()
    web_fixture.driver_browser.open('/')
    assert web_fixture.driver_browser.wait_for(fixture.tab_is_active, 'Tab 1')
    assert web_fixture.driver_browser.wait_for(fixture.tab_contents_equals, 'A paragraph to give content to the first tab.')
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('tabbedpanel1.png'))

    web_fixture.driver_browser.click(XPath.link_with_text('Tab 2'))
    assert web_fixture.driver_browser.wait_for(fixture.tab_is_active, 'Tab 2')
    assert web_fixture.driver_browser.wait_for(fixture.tab_contents_equals, 'And another ...  to give content to the second tab.')
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('tabbedpanel2.png'))


carousel_panel_scenario = ExampleFixture.carousel_panel.as_pytest_fixture()

def test_widgets(web_fixture, carousel_panel_scenario):
    fixture = carousel_panel_scenario
    fixture.start_example_app()
    web_fixture.driver_browser.open('/')
    assert web_fixture.driver_browser.wait_for(fixture.carousel_caption_equals, 'a paragraph with text')
    web_fixture.driver_browser.click(XPath.link_with_text('Next'))
    assert web_fixture.driver_browser.wait_for(fixture.carousel_caption_equals, 'a different paragraph')


validation_scenario = ExampleFixture.validation.as_pytest_fixture()

def test_validation(web_fixture, validation_scenario):
    fixture = validation_scenario
    
    fixture.start_example_app()
    web_fixture.driver_browser.open('/')
    assert web_fixture.driver_browser.wait_for_not(fixture.error_is_visible) 
    assert web_fixture.driver_browser.is_element_present('//input') 
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('validation1.png'))
    
    web_fixture.driver_browser.type('//input', 'johndoe')
    web_fixture.driver_browser.press_tab('//input')
    assert web_fixture.driver_browser.wait_for(fixture.error_is_visible) 
    assert fixture.is_error_text('Email address should be a valid email address') 
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('validation2.png'))

    web_fixture.driver_browser.type('//input', '')
    web_fixture.driver_browser.press_tab('//input')
    assert web_fixture.driver_browser.wait_for(fixture.error_is_visible) 
    assert fixture.is_error_text('Email address is required') 
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('validation3.png'))

    web_fixture.driver_browser.type('//input', 'johndoe@some.org')
    web_fixture.driver_browser.press_tab('//input')
    assert web_fixture.driver_browser.wait_for_not(fixture.error_is_visible) 
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('validation4.png'))


layout_scenario = ExampleFixture.layout.as_pytest_fixture()

def test_layout(web_fixture, layout_scenario):
    fixture = layout_scenario

    fixture.start_example_app()
    web_fixture.driver_browser.open('/')
    web_fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe')
    web_fixture.driver_browser.press_tab('//input')
    assert web_fixture.driver_browser.wait_for(fixture.error_is_visible) 
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('layout.png'))


pageflow_scenario = ExampleFixture.pageflow.as_pytest_fixture()

def test_pageflow(web_fixture, pageflow_scenario):
    fixture = pageflow_scenario
    
    fixture.start_example_app()
    web_fixture.driver_browser.open('/')
    web_fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe@some.org')
    web_fixture.driver_browser.type(XPath.input_labelled('Comment'), '')
    with SystemOutStub() as output:
        web_fixture.driver_browser.click(XPath.button_labelled('Submit'))
        
        assert output.captured_output == 'johndoe@some.org submitted a comment:\nNone\n' 
        assert web_fixture.driver_browser.current_url.path == '/none' 
        output.capture_console_screenshot(fixture.new_screenshot_path('pageflow1.txt'))

        web_fixture.driver_browser.open('/')
        web_fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe@some.org')
        web_fixture.driver_browser.type(XPath.input_labelled('Comment'), 'some comment text')
        with SystemOutStub() as output:
            web_fixture.driver_browser.click(XPath.button_labelled('Submit'))

        assert output.captured_output == 'johndoe@some.org submitted a comment:\nsome comment text\n' 
        assert web_fixture.driver_browser.current_url.path == '/thanks' 
        output.capture_console_screenshot(fixture.new_screenshot_path('pageflow2.txt'))


persistence_scenario = ExampleFixture.persistence.as_pytest_fixture()

def test_persistence(web_fixture, persistence_scenario):
    fixture = persistence_scenario

    fixture.start_example_app()
    web_fixture.driver_browser.open('/')

    assert not web_fixture.driver_browser.is_element_present('//h1') 
    assert web_fixture.driver_browser.is_element_present('//form') 

    web_fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe@some.org')
    web_fixture.driver_browser.type(XPath.input_labelled('Comment'), 'some comment text')
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('persistence1.png'))

    web_fixture.driver_browser.click(XPath.button_labelled('Submit'))

    assert web_fixture.driver_browser.is_element_present('//form') 
    assert web_fixture.driver_browser.is_element_present('//form/following-sibling::div/p') 
    comment_text = web_fixture.driver_browser.get_text('//form/following-sibling::div/p')
    assert comment_text == 'By johndoe@some.org: some comment text' 

    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('persistence2.png'))


access_control_scenario = ExampleFixture.access_control.as_pytest_fixture()

def test_access(web_fixture, access_control_scenario):
    fixture = access_control_scenario
    fixture.start_example_app()
    web_fixture.driver_browser.open('/')
    assert web_fixture.driver_browser.is_element_present(XPath.input_labelled('Greyed out') )
    assert not web_fixture.driver_browser.is_editable(XPath.input_labelled('Greyed out')) 
    assert web_fixture.driver_browser.is_element_present(XPath.button_labelled('Greyed out button')) 
    assert not web_fixture.driver_browser.is_editable(XPath.button_labelled('Greyed out button')) 
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('access.png'))

    from reahl.doc.examples.features.access.access import Comment
    from reahl.component.exceptions import AccessRestricted
    comment = Comment()
    with expected(AccessRestricted):
        comment.do_something()

i18n_scenario = ExampleFixture.i18n.as_pytest_fixture()

def test_i18n(web_fixture, i18n_scenario):
    fixture = i18n_scenario
    fixture.start_example_app()
    web_fixture.driver_browser.open('/some_page')
    assert fixture.get_text_in_p() == 'This is a translated string. The current URL is "/some_page".' 
    assert web_fixture.driver_browser.title == 'Translated example' 
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('i18n1.png'))

    web_fixture.driver_browser.click(XPath.link_with_text('Afrikaans'))
    assert fixture.get_text_in_p() == 'Hierdie is \'n vertaalde string. Die huidige URL is "/af/some_page".' 
    assert web_fixture.driver_browser.title == 'Vertaalde voorbeeld' 
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('i18n2.png'))


basichtmlwidgets_scenario = ExampleFixture.basichtmlwidgets.as_pytest_fixture()

def test_basichtmlwidgets(web_fixture, basichtmlwidgets_scenario):
    basichtmlwidgets_scenario.start_example_app()
    web_fixture.driver_browser.open('/')


fileupload_scenario = ExampleFixture.fileupload.as_pytest_fixture()

def test_fileupload(web_fixture, fileupload_scenario):
    fixture = fileupload_scenario
    with web_fixture.context:
        fixture.start_example_app()
        web_fixture.driver_browser.open('/')

        file1 = temp_file_with(b'some content in a file', 'file1.txt', mode='w+b')
        file2 = temp_file_with(b'different content', 'file2.txt', mode='w+b')
        file3 = temp_file_with(b'even more content', 'file3.txt', mode='w+b')

        # Upload a file
        web_fixture.driver_browser.type('//input[@type="file"]', file1.name)
        assert fixture.uploaded_file_is_listed(file1.name) 

        # Upload a file
        web_fixture.driver_browser.type('//input[@type="file"]', file2.name)
        assert fixture.uploaded_file_is_listed(file2.name) 

        # Upload a file
        web_fixture.driver_browser.type('//input[@type="file"]', file3.name)
        assert fixture.uploaded_file_is_listed(file3.name) 

        # Delete file2 from uploaded files
        web_fixture.driver_browser.click(XPath.button_labelled('Remove', filename=os.path.basename(file2.name)))
        assert not fixture.uploaded_file_is_listed(file2.name) 

        # Submit the form
        web_fixture.driver_browser.type(XPath.input_labelled('Email address'), 'johndoe@some.org')
        web_fixture.driver_browser.type(XPath.input_labelled('Comment'), 'some comment text')
        web_fixture.driver_browser.click(XPath.button_labelled('Submit'))

        attached_file1 = Session.query(AttachedFile).filter_by(filename=os.path.basename(file1.name)).one()
        attached_file3 = Session.query(AttachedFile).filter_by(filename=os.path.basename(file3.name)).one()
        assert Session.query(AttachedFile).count() == 2 
        assert attached_file1.contents == b'some content in a file' 
        assert attached_file3.contents == b'even more content' 


slots_scenario = ExampleFixture.slots.as_pytest_fixture()

def test_slots(web_fixture, slots_scenario):
    fixture = slots_scenario
    fixture.start_example_app()
    web_fixture.driver_browser.open('/')

    expected_main_contents = 'In this slot will be some main content for the view on /'
    expected_secondary_contents = 'Some secondary content related to /'
    main_contents = fixture.get_main_slot_contents()
    assert main_contents == expected_main_contents 
    secondary_contents = fixture.get_secondary_slot_contents()
    assert secondary_contents == expected_secondary_contents 
    
    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('slots1.png'))

    web_fixture.driver_browser.click(XPath.link_with_text('Page 2'))
    expected_main_contents = 'This could, for example, be where a photo gallery shows a large photo.'
    expected_secondary_contents = 'Thumbnails will then sit on the side of the big photo.'
    main_contents = fixture.get_main_slot_contents()
    assert main_contents == expected_main_contents 
    secondary_contents = fixture.get_secondary_slot_contents()
    assert secondary_contents == expected_secondary_contents 

    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('slots2.png'))

basichtmlinputs_scenario = ExampleFixture.basichtmlinputs.as_pytest_fixture()

def test_basichtmlinputs(web_fixture, basichtmlinputs_scenario):
    basichtmlinputs_scenario.start_example_app()
    web_fixture.driver_browser.open('/')


def test_model_examples():
    # These examples are built to run outside of our infrastructure, hence have to be run like this:
    for example in ['modeltests1.py', 'modeltests2.py', 'modeltests3.py']:
        Executable('nosetests').check_call(['--first-package-wins', 'reahl/doc/examples/tutorial/%s' % example ])

addressbook1_scenario = ExampleFixture.addressbook1.as_pytest_fixture()

def test_addressbook1(web_fixture, addressbook1_scenario):
    with web_fixture.context:
        john = addressbook1.Address(name='John', email_address='johndoe@some.org')
        john.save()

        browser = Browser(addressbook1_scenario.wsgi_app)
        browser.open('/')

        assert browser.is_element_present(XPath.paragraph_containing('John: johndoe@some.org')) 


addressbook2_scenario = ExampleFixture.addressbook2.as_pytest_fixture()

def test_addressbook2(web_fixture, addressbook2_scenario):
    with web_fixture.context:
        browser = Browser(addressbook2_scenario.wsgi_app)
        browser.open('/')

        browser.type(XPath.input_labelled('Name'), 'John') 
        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.click(XPath.button_labelled('Save'))

        assert browser.is_element_present(XPath.paragraph_containing('John: johndoe@some.org')) 


addressbook2bootstrap_scenario = ExampleFixture.addressbook2bootstrap.as_pytest_fixture()

def test_addressbook2bootstrap(web_fixture, addressbook2bootstrap_scenario):
    fixture = addressbook2bootstrap_scenario
    fixture.start_example_app()
    web_fixture.driver_browser.open('/')

    web_fixture.driver_browser.type(XPath.input_labelled('Name'), 'John')
    web_fixture.driver_browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')

    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('bootstrapform.png'))

bootstrapgrids_scenario = ExampleFixture.bootstrapgrids.as_pytest_fixture()

def test_bootstrapgrids(web_fixture, bootstrapgrids_scenario):
    fixture = bootstrapgrids_scenario
    
    fixture.start_example_app()
    web_fixture.driver_browser.open('/gridBasics')

    web_fixture.driver_browser.capture_cropped_screenshot(fixture.new_screenshot_path('bootstrapgrids.png'))

pageflow1_scenario = ExampleFixture.pageflow1.as_pytest_fixture()

def test_pageflow1(web_fixture, pageflow1_scenario):
    with web_fixture.context:
        browser = Browser(pageflow1_scenario.wsgi_app)
        browser.open('/')

        assert browser.is_element_present('//ul[contains(@class,"nav")]') 

        browser.click(XPath.link_with_text('Add an address'))
        assert browser.location_path == '/add' 

        browser.type(XPath.input_labelled('Name'), 'John') 
        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.click(XPath.button_labelled('Save'))

        assert browser.location_path == '/add' 

        browser.click(XPath.link_with_text('Addresses'))
        assert browser.location_path == '/' 
        assert browser.is_element_present(XPath.paragraph_containing('John: johndoe@some.org')) 


pageflow2_scenario = ExampleFixture.pageflow2.as_pytest_fixture()

def test_pageflow2(web_fixture, pageflow2_scenario):
    with web_fixture.context:
        browser = Browser(pageflow2_scenario.wsgi_app)
        browser.open('/')

        assert browser.is_element_present('//ul[contains(@class,"nav")]') 

        browser.click(XPath.link_with_text('Add an address'))
        assert browser.location_path == '/add' 

        browser.type(XPath.input_labelled('Name'), 'John') 
        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.click(XPath.button_labelled('Save'))

        assert browser.location_path == '/' 
        assert browser.is_element_present(XPath.paragraph_containing('John: johndoe@some.org')) 


parameterised1_scenario = ExampleFixture.parameterised1.as_pytest_fixture()

def test_parameterised1(web_fixture, parameterised1_scenario):
    with web_fixture.context:
        browser = Browser(parameterised1_scenario.wsgi_app)
        browser.open('/')

        browser.click(XPath.link_with_text('Add an address'))
        browser.type(XPath.input_labelled('Name'), 'John') 
        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.click(XPath.button_labelled('Save'))

        assert browser.location_path == '/' 
        browser.click(XPath.link_with_text('edit'))

        john = Session.query(parameterised1bootstrap.Address).one()
        assert browser.location_path == '/edit/%s' % john.id 
        browser.type(XPath.input_labelled('Name'), 'Johnny') 
        browser.type(XPath.input_labelled('Email'), 'johnny@walker.org')
        browser.click(XPath.button_labelled('Update'))

        assert browser.location_path == '/' 
        assert browser.is_element_present(XPath.paragraph_containing('Johnny: johnny@walker.org')) 


