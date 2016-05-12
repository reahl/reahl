
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import test, set_up

from reahl.sqlalchemysupport import Session
from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath

from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount

from reahl.doc.examples.tutorial.login1bootstrap.login1bootstrap import LoginUI


class LoginFixture(WebFixture):
    def new_browser(self):
        return Browser(self.new_wsgi_app(site_root=LoginUI))

    def new_webconfig(self):
        webconfig = super(LoginFixture, self).new_webconfig()
        webconfig.frontend_libraries.enable_experimental_bootstrap()
        return webconfig

    password = 'topsecret'

    def new_account(self):
        account = EmailAndPasswordSystemAccount(email='johndoe@some.org')
        Session.add(account)
        account.set_new_password(account.email, self.password)
        account.activate()
        return account


class DemoFixture(LoginFixture):
    commit=True
    @set_up
    def do_demo_setup(self):
        self.account
        Session.commit()


@test(LoginFixture)
def logging_in(fixture):
    """A user can log in by going to the Log in page.
       The name of the currently logged in user is displayed on the home page."""

    browser = fixture.browser
    account = fixture.account

    browser.open('/')
    browser.click(XPath.link_with_text('Log in'))

    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    browser.type(XPath.input_labelled('Password'), 'topsecret')
    browser.click(XPath.button_labelled('Log in'))

    browser.click(XPath.link_with_text('Home'))
    assert browser.is_element_present(XPath.paragraph_containing('Welcome johndoe@some.org'))
        

@test(LoginFixture)
def domain_exception(fixture):
    """Typing the wrong password results in an error message being shown to the user."""

    browser = fixture.browser
    account = fixture.account

    browser.open('/')
    browser.click(XPath.link_with_text('Log in'))

    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    browser.type(XPath.input_labelled('Password'), 'wrong password')
    browser.click(XPath.button_labelled('Log in'))

    assert browser.is_element_present(XPath.div_containing('Invalid login credentials'))
