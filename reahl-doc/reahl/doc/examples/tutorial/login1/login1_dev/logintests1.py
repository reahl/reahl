
from reahl.tofu import test, set_up

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.login1.login1 import LoginUI
from reahl.systemaccountmodel import EmailAndPasswordSystemAccount


class LoginFixture(WebFixture):
    def new_browser(self):
        return Browser(self.new_wsgi_app(site_root=LoginUI))
        
    password = u'bobbejaan'

    def new_account(self):
        account = EmailAndPasswordSystemAccount(email=u'johndoe@some.org')
        account.set_new_password(account.email, self.password)
        account.activate()
        return account


class DemoFixture(LoginFixture):
    commit=True
    @set_up
    def do_demo_setup(self):
        self.account


@test(LoginFixture)
def logging_in(fixture):
    """A user can log in by going to the Log in page.
       The name of the currently logged in user is displayed on the home page."""

    browser = fixture.browser
    account = fixture.account

    browser.open(u'/')
    browser.click(XPath.link_with_text(u'Log in'))

    browser.type(XPath.input_labelled(u'Email'), u'johndoe@some.org')
    browser.type(XPath.input_labelled(u'Password'), u'bobbejaan')
    browser.click(XPath.button_labelled(u'Log in'))

    browser.click(XPath.link_with_text(u'Home'))
    assert browser.is_element_present(XPath.paragraph_containing(u'Welcome johndoe@some.org'))
        

@test(LoginFixture)
def domain_exception(fixture):
    """Typing the wrong password results in an error message being shown to the user."""

    browser = fixture.browser
    account = fixture.account

    browser.open(u'/')
    browser.click(XPath.link_with_text(u'Log in'))

    browser.type(XPath.input_labelled(u'Email'), u'johndoe@some.org')
    browser.type(XPath.input_labelled(u'Password'), u'wrong password')
    browser.click(XPath.button_labelled(u'Log in'))

    assert browser.is_element_present(XPath.paragraph_containing(u'Invalid login credentials'))
