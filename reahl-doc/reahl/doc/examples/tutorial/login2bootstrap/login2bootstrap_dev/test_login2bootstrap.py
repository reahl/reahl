
from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser, XPath

from reahl.sqlalchemysupport import Session
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount

from reahl.doc.examples.tutorial.login2bootstrap.login2bootstrap import LoginUI

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
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
    login_fixture.new_account()


@with_fixtures(WebFixture, LoginFixture)
def test_logging_in(web_fixture, login_fixture):
    """A user can log in by going to the Log in page.
       The name of the currently logged in user is displayed on the home page."""

    browser = login_fixture.browser
    login_fixture.new_account()

    browser.open('/')
    browser.click(XPath.link().with_text('Log in with email and password'))

    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    browser.type(XPath.input_labelled('Password'), 'topsecret')
    browser.click(XPath.button_labelled('Log in'))

    browser.click(XPath.link().with_text('Home'))
    assert browser.is_element_present(XPath.paragraph().including_text('Welcome johndoe@some.org'))

        

