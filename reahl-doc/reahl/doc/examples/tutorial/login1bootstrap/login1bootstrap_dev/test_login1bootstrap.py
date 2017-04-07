
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.webdev.tools import Browser, XPath

from reahl.sqlalchemysupport import Session
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount

from reahl.doc.examples.tutorial.login1bootstrap.login1bootstrap import LoginUI

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.web_dev.fixtures import WebFixture2


@uses(web_fixture=WebFixture2)
class LoginFixture(Fixture):

    def new_browser(self):
        return Browser(self.web_fixture.new_wsgi_app(site_root=LoginUI))

    password = 'topsecret'

    def new_account(self):
        account = EmailAndPasswordSystemAccount(email='johndoe@some.org')
        Session.add(account)
        account.set_new_password(account.email, self.password)
        account.activate()
        return account


@with_fixtures(SqlAlchemyFixture, LoginFixture)
def demo_setup(sql_alchemy_fixture, login_fixture):
    sql_alchemy_fixture.commit = True
    with sql_alchemy_fixture.context:
        login_fixture.new_account()


@with_fixtures(WebFixture2, LoginFixture)
def test_logging_in(web_fixture, login_fixture):
    """A user can log in by going to the Log in page.
       The name of the currently logged in user is displayed on the home page."""

    with web_fixture.context:
        browser = login_fixture.browser
        login_fixture.new_account()

        browser.open('/')
        browser.click(XPath.link_with_text('Log in'))

        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.type(XPath.input_labelled('Password'), 'topsecret')
        browser.click(XPath.button_labelled('Log in'))

        browser.click(XPath.link_with_text('Home'))
        assert browser.is_element_present(XPath.paragraph_containing('Welcome johndoe@some.org'))


@with_fixtures(WebFixture2, LoginFixture)
def test_domain_exception(web_fixture, login_fixture):
    """Typing the wrong password results in an error message being shown to the user."""

    with web_fixture.context:
        browser = login_fixture.browser
        login_fixture.new_account()

        browser.open('/')
        browser.click(XPath.link_with_text('Log in'))

        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.type(XPath.input_labelled('Password'), 'wrong password')
        browser.click(XPath.button_labelled('Log in'))

        assert browser.is_element_present(XPath.div_containing('Invalid login credentials'))
