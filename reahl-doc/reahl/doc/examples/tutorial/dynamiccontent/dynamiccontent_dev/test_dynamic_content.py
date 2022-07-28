

from reahl.tofu.pytestsupport import with_fixtures
from reahl.tofu import Fixture, uses

from reahl.web_dev.fixtures import WebFixture
from reahl.browsertools.browsertools import XPath

from reahl.doc.examples.tutorial.dynamiccontent.dynamiccontent import DynamicUI

@uses(web_fixture=WebFixture)
class DynamicExampleFixture(Fixture):
    def new_browser(self):
        return self.web_fixture.driver_browser

    def percentage_total_is(self, percentage):
        return self.browser.get_text(self.percentage_cell_for('Totals').inside_of(XPath.table_footer())) == percentage

    def percentage_input_for(self, fund_name):
        return XPath.input().inside_of(self.percentage_cell_for(fund_name))

    def percentage_cell_for(self, fund_name):
        return XPath.table_cell_aligned_to('Percentage', 'Fund', fund_name)

    def new_domain_exception_alert(self):
        return XPath.div().including_class('alert').with_text('Please ensure allocation percentages add up to 100')


@with_fixtures(WebFixture, DynamicExampleFixture)
def test_example(web_fixture, dynamic_example_fixture):
    fixture = dynamic_example_fixture

    wsgi_application = web_fixture.new_wsgi_app(site_root=DynamicUI, enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_application)

    browser = fixture.browser

    browser.open('/')

    # Check calculating totals
    browser.type(fixture.percentage_input_for('Fund A'), '80')
    browser.wait_for(fixture.percentage_total_is, '80')

    browser.type(fixture.percentage_input_for('Fund B'), '80')
    browser.wait_for(fixture.percentage_total_is, '160')

    # Check DomainException upon submit with incorrect totals
    browser.click(XPath.button_labelled('Submit'))    
    browser.wait_for_element_visible(fixture.domain_exception_alert)  

    browser.type(fixture.percentage_input_for('Fund B'), '20')
    browser.wait_for(fixture.percentage_total_is, '100')

    # Check successful submit
    browser.click(XPath.button_labelled('Submit'))
    browser.wait_for_element_not_visible(fixture.domain_exception_alert)


