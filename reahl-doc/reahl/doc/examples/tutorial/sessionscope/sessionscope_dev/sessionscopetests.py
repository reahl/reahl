
from reahl.tofu import test, set_up

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.sessionscope.sessionscope import SessionScopeUI, User


class SessionScopeFixture(WebFixture):
    def new_browser(self):
        return Browser(self.new_wsgi_app(site_root=SessionScopeUI))
        
    password = u'bobbejaan'

    def new_user(self):
        user = User(name=u'John Doe', email_address=u'johndoe@some.org')
        user.set_password(self.password)
        return user


class DemoFixture(SessionScopeFixture):
    commit=True
    @set_up
    def make_stuff(self):
        self.user


@test(SessionScopeFixture)
def logging_in(fixture):
    """A user can log in by going to the Log in page.
       The name of the currently logged in user is displayed on the home page."""

    browser = fixture.browser
    user = fixture.user

    browser.open(u'/')
    browser.click(XPath.link_with_text(u'Log in'))

    browser.type(XPath.input_labelled(u'Email'), u'johndoe@some.org')
    browser.type(XPath.input_labelled(u'Password'), u'bobbejaan')
    browser.click(XPath.button_labelled(u'Log in'))

    browser.click(XPath.link_with_text(u'Home'))
    assert browser.is_element_present(XPath.paragraph_containing(u'Welcome John Doe'))
    
@test(SessionScopeFixture)
def email_retained(fixture):
    """The email address used when last logged in is always pre-populated on the Log in page."""

    browser = fixture.browser
    user = fixture.user

    browser.open(u'/')
    browser.click(XPath.link_with_text(u'Log in'))

    browser.type(XPath.input_labelled(u'Email'), u'johndoe@some.org')
    browser.type(XPath.input_labelled(u'Password'), u'bobbejaan')
    browser.click(XPath.button_labelled(u'Log in'))

    # Go away from the page, then back
    browser.click(XPath.link_with_text(u'Home'))
    browser.click(XPath.link_with_text(u'Log in'))

    # .. then the email is still pre-populated
    typed_value = browser.get_value(XPath.input_labelled(u'Email'))
    assert typed_value == u'johndoe@some.org'
    

@test(SessionScopeFixture)
def domain_exception(fixture):
    """Typing the wrong password results in an error message being shown to the user."""

    browser = fixture.browser
    user = fixture.user

    browser.open(u'/')
    browser.click(XPath.link_with_text(u'Log in'))

    browser.type(XPath.input_labelled(u'Email'), u'johndoe@some.org')
    browser.type(XPath.input_labelled(u'Password'), u'wrong password')
    browser.click(XPath.button_labelled(u'Log in'))

    assert browser.is_element_present(XPath.paragraph_containing(u'The email/password given do not match'))
