
from reahl.tofu.pytestsupport import with_fixtures
from reahl.tofu import Fixture, uses

from reahl.web_dev.fixtures import WebFixture
from reahl.browsertools.browsertools import XPath

from reahl.doc.examples.howtos.optimisticconcurrency.optimisticconcurrency import OptimisticConcurrencyUI

@uses(web_fixture=WebFixture)
class OptimisticConcurrencyExampleFixture(Fixture):
    def new_browser(self):
        return self.web_fixture.driver_browser

    def check_counter_value_is(self, counter_value):
        assert self.browser.is_element_present(XPath.paragraph().with_text('Counter: %s' % counter_value))

    def link_opens_new_tab(self):
        return XPath.link().with_text('Open another tab...')

    def increment_button(self):
        return XPath.button_labelled('Increment')

    def submit_button(self):
        return XPath.button_labelled('Submit')

    def check_concurrency_error_is_displayed(self):
        alert = XPath.div().including_class('alert')
        assert 'Some data changed since you opened this page' in self.browser.get_text(alert)


@with_fixtures(WebFixture, OptimisticConcurrencyExampleFixture)
def test_example(web_fixture, optimistic_concurrency_example_fixture):
    fixture = optimistic_concurrency_example_fixture

    wsgi_application = web_fixture.new_wsgi_app(site_root=OptimisticConcurrencyUI, enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_application)

    browser = fixture.browser

    browser.open('/')

    with browser.new_tab_closed():
        browser.click(fixture.link_opens_new_tab())
        browser.switch_to_different_tab()
        browser.click(fixture.increment_button())
        fixture.check_counter_value_is(1)

    # Back in the original tab, Cause the concurrency error
    fixture.check_counter_value_is(0) #The other tab just made this 1
    browser.click(fixture.submit_button())
    fixture.check_concurrency_error_is_displayed()



