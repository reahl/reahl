
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import Fixture

from reahl.webdev.tools import Browser, XPath

from reahl.sqlalchemysupport import Session
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount

from reahl.doc.examples.tutorial.login2bootstrap.login2bootstrap import LoginUI

from reahl.web_dev.fixtures import web_fixture
from reahl.sqlalchemysupport_dev.fixtures import sql_alchemy_fixture
from reahl.domain_dev.fixtures import party_account_fixture


class LoginFixture(Fixture):
    def __init__(self, web_fixture):
        super(LoginFixture, self).__init__()
        self.web_fixture = web_fixture

    def new_browser(self):
        return Browser(self.web_fixture.new_wsgi_app(site_root=LoginUI))

    password = 'topsecret'

    def new_account(self):
        account = EmailAndPasswordSystemAccount(email='johndoe@some.org')
        Session.add(account)
        account.set_new_password(account.email, self.password)
        account.activate()
        return account

login_fixture = LoginFixture.as_pytest_fixture()

def demo_setup(sql_alchemy_fixture, login_fixture):
    sql_alchemy_fixture.commit = True
    with sql_alchemy_fixture.context:
        login_fixture.new_account()


def test_logging_in(web_fixture, login_fixture):
    """A user can log in by going to the Log in page.
       The name of the currently logged in user is displayed on the home page."""

    with web_fixture.context:
        browser = login_fixture.browser
        login_fixture.new_account()

        browser.open('/')
        browser.click(XPath.link_with_text('Log in with email and password'))

        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
        browser.type(XPath.input_labelled('Password'), 'topsecret')
        browser.click(XPath.button_labelled('Log in'))

        browser.click(XPath.link_with_text('Home'))
        assert browser.is_element_present(XPath.paragraph_containing('Welcome johndoe@some.org'))

        

