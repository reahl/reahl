from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import Fixture

from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.i18nexamplebootstrap.i18nexamplebootstrap import AddressBookUI, Address

from reahl.web_dev.fixtures import web_fixture
from reahl.sqlalchemysupport_dev.fixtures import sql_alchemy_fixture
from reahl.domain_dev.fixtures import party_account_fixture


class TranslationExampleFixture(Fixture):
    def __init__(self, web_fixture):
        super(TranslationExampleFixture, self).__init__()
        self.web_fixture = web_fixture

    def new_browser(self):
        return Browser(self.web_fixture.new_wsgi_app(site_root=AddressBookUI))

    def create_addresses(self):
        addresses = [Address(name='friend %s' % i, email_address='friend%s@some.org' % i) for i in list(range(1, 5))]
        for address in addresses:
            address.save()
        return addresses

translation_example_fixture = TranslationExampleFixture.as_pytest_fixture()


def demo_setup(sql_alchemy_fixture, data_table_example_fixture):
    sql_alchemy_fixture.commit = True
    with sql_alchemy_fixture.context:
        data_table_example_fixture.create_addresses()


def test_translations(web_fixture, translation_example_fixture):
    """The user can choose between languages. The text for which translations exist change accordingly."""

    with web_fixture.context:
        browser = translation_example_fixture.browser
        browser.open('/')
        assert browser.is_element_present(XPath.heading_with_text(1, "Addresses"))
        assert browser.is_element_present(XPath.label_with_text("Name"))

        #go to the the translated page
        browser.click(XPath.link_with_text('Afrikaans'))
        assert browser.is_element_present(XPath.heading_with_text(1, "Adresse"))
        assert browser.is_element_present(XPath.label_with_text("Naam"))
