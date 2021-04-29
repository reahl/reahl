

from reahl.tofu.pytestsupport import with_fixtures
from reahl.tofu import Fixture, uses

from reahl.web_dev.fixtures import WebFixture
from reahl.browsertools.browsertools import XPath

from reahl.doc.examples.howtos.responsivedisclosure.responsivedisclosure import ResponsiveUI

@uses(web_fixture=WebFixture)
class ResponsiveExampleFixture(Fixture):
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

    def new_investment_allocation_details(self):
        return XPath.fieldset_with_legend('Investment allocation')

    def new_investor_information(self):
        return XPath.fieldset_with_legend('Investor information')

    def new_new_investor_specific_information(self):
        return XPath.fieldset_with_legend('New investor information')


@with_fixtures(WebFixture, ResponsiveExampleFixture)
def test_example(web_fixture, responsive_example_fixture):
    fixture = responsive_example_fixture

    wsgi_application = web_fixture.new_wsgi_app(site_root=ResponsiveUI, enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_application)

    browser = fixture.browser

    browser.open('/')
    
    # Reveal sections for new investors    
    assert not browser.is_visible(fixture.investor_information)  
    browser.set_selected(XPath.input_labelled('New'))

    browser.wait_for_element_visible(fixture.investor_information)  
    browser.wait_for_element_visible(fixture.new_investor_specific_information)  

    # Reveal and complete sections for existing investors
    browser.set_selected(XPath.input_labelled('Existing'))

    browser.wait_for_element_visible(fixture.investor_information)  
    browser.wait_for_element_not_visible(fixture.new_investor_specific_information)  

    browser.type(XPath.input_labelled('Existing account number'), '1234')

    # Reveal sections for Investment allocation details
    assert not browser.is_visible(fixture.investment_allocation_details)  

    browser.click(XPath.label().with_text('I agree to the terms and conditions'))
    browser.wait_for_element_visible(fixture.investment_allocation_details)  
    
    browser.type(XPath.input_labelled('Total amount'), '10000')

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

