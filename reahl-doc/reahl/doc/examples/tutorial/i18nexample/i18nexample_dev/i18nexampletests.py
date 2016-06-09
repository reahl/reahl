from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import test, vassert

from reahl.web_dev.fixtures import WebFixture

from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.i18nexample.i18nexample import AddressBookUI, Address

class TranslationExampleFixture(WebFixture):

    def new_browser(self):
        return Browser(self.new_wsgi_app(site_root=AddressBookUI))

    def new_addresses(self):
        addresses = [Address(name='friend %s' % i, email_address='friend%s@some.org' % i) for i in list(range(1, 5))]
        for address in addresses:
            address.save()
        return addresses


class DemoSetup(TranslationExampleFixture):
    commit = True
    def set_up(self):
        super(DemoSetup, self).set_up()
        self.addresses
        self.system_control.commit()


@test(TranslationExampleFixture)
def translations(fixture):
    """The user can choose between languages. The text for which translations exist change accordingly."""

    fixture.browser.open('/')
    vassert( fixture.browser.is_element_present(XPath.heading_with_text(1, "Addresses")) )
    vassert( fixture.browser.is_element_present(XPath.label_with_text("Name")) )

    #go to the the translated page
    fixture.browser.click(XPath.link_with_text('Afrikaans'))
    vassert( fixture.browser.is_element_present(XPath.heading_with_text(1, "Adresse")) )
    vassert( fixture.browser.is_element_present(XPath.label_with_text("Naam")) )
