

from reahl.tofu.pytestsupport import with_fixtures
from reahl.tofu import Fixture, uses, scenario

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath

from reahl.doc.examples.howtos.customisingerrorpages.customisingerrorpages import BreakingUIWithBuiltInErrorPage, BreakingUIWithCustomErrorPage

@uses(web_fixture=WebFixture)
class ErrorPageFixture(Fixture):
    def new_browser(self):
        return self.web_fixture.driver_browser

    def get_button_xpath(self):
        return XPath.button_labelled('Submit')

    def check_error_page_contents(self, browser):
        self.check_error_heading_is_displayed(browser)

    @scenario
    def with_builtin_error_page(self):
        self.root_ui = BreakingUIWithBuiltInErrorPage
        def check(browser):
            alert = XPath.div().including_class('alert')
            assert browser.get_text(alert) == 'An error occurred:\nThis error is thrown intentionally\nOk'
        self.check_error_heading_is_displayed = check


    @scenario
    def with_custom_error_page(self):
        self.root_ui = BreakingUIWithCustomErrorPage
        self.error_heading_text = 'Oops, something broke'
        def check(browser):
            assert browser.is_element_present(XPath.heading(1).with_text(self.error_heading_text))
        self.check_error_heading_is_displayed = check


@with_fixtures(WebFixture, ErrorPageFixture)
def test_example(web_fixture, error_page_fixture):
    fixture = error_page_fixture

    wsgi_application = web_fixture.new_wsgi_app(site_root=fixture.root_ui, enable_js=True)
    wsgi_application.config.reahlsystem.debug = False

    web_fixture.reahl_server.set_app(wsgi_application)
    browser = fixture.browser

    browser.open('/')

    # Check that the error displays
    browser.click(fixture.get_button_xpath())
    error_page_fixture.check_error_page_contents(browser)

