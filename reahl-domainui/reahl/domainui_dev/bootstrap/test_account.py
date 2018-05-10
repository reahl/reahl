# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals, absolute_import, division
import six

from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.sqlalchemysupport import Session
from reahl.web.fw import Url, UserInterface
from reahl.web.layout import PageLayout
from reahl.webdev.tools import Browser
from reahl.web.bootstrap.ui import HTML5Page
from reahl.web.bootstrap.grid import ResponsiveSize, ColumnLayout, ColumnOptions, Container
from reahl.domain.systemaccountmodel import VerifyEmailRequest, NewPasswordRequest, ActivateAccount
from reahl.domainui.bootstrap.accounts import AccountUI
from reahl.domainui_dev.fixtures import BookmarkStub


from reahl.domain_dev.fixtures import PartyAccountFixture
from reahl.dev.fixtures import ReahlSystemFixture
from reahl.web_dev.fixtures import WebFixture


@uses(reahl_system_fixture=ReahlSystemFixture, web_fixture=WebFixture)
class AccountsWebFixture(Fixture):

    def new_login_bookmark(self, request=None):
        self.reahl_system_fixture.context.request = request or self.request
        return self.account_user_interface_factory.get_bookmark(relative_path='/login')

    def new_MainUI(self):
        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                page_layout = PageLayout(document_layout=Container(),
                                         contents_layout=ColumnLayout(ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots())
                self.define_page(HTML5Page).use_layout(page_layout)
                account_user_interface_factory = self.define_user_interface('/a_ui',  AccountUI,  {'main_slot': 'main'}, name='test_ui',
                                                            bookmarks=fixture.bookmarks)
                fixture.account_user_interface_factory = account_user_interface_factory
        return MainUI

    def new_wsgi_app(self, enable_js=False):
        return self.web_fixture.new_wsgi_app(enable_js=enable_js, site_root=self.MainUI)

    def new_browser(self):
        return Browser(self.wsgi_app)

    def new_bookmarks(self):
        class Bookmarks(object):
            terms_bookmark = BookmarkStub(Url('/#terms'), 'Terms')
            privacy_bookmark = BookmarkStub(Url('/#privacy'), 'Privacy Policy')
            disclaimer_bookmark = BookmarkStub(Url('/#disclaimer'), 'Disclaimer')
        return Bookmarks()


@with_fixtures(WebFixture, PartyAccountFixture, AccountsWebFixture)
def test_login_with_detour(web_fixture, party_account_fixture, accounts_web_fixture):
    fixture = accounts_web_fixture

    account = party_account_fixture.system_account

    fixture.browser.open('/a_ui/register?a=b&name=kitty')
    assert fixture.browser.location_path == '/a_ui/register'
    assert fixture.browser.location_query_string == 'a=b&name=kitty'

    fixture.browser.open(six.text_type(fixture.new_login_bookmark(request=fixture.browser.last_request).href))
    fixture.browser.click('//a[text()="Forgot your password?"]')
    fixture.browser.go_back()
    fixture.browser.type('//input[@name="email"]', account.email)
    fixture.browser.type('//input[@name="password"]', account.password)
    fixture.browser.click('//input[@value="Log in"]')

    assert fixture.browser.location_path == '/a_ui/register'
    assert fixture.browser.location_query_string == 'a=b&name=kitty'


@with_fixtures(WebFixture, AccountsWebFixture)
def test_register(web_fixture, accounts_web_fixture):
    fixture = accounts_web_fixture

    verification_requests = Session.query(VerifyEmailRequest)
    fixture.browser.open('/a_ui/register')

    fixture.browser.type('//form[@id="register"]//*[@name="email"]', 'a@b.org')
    fixture.browser.type('//form[@id="register"]//*[@name="password"]', '111111')
    fixture.browser.type('//form[@id="register"]//*[@name="repeat_password"]', '111111')
    fixture.browser.click('//form[@id="register"]//*[@name="accept_terms"]')

    assert verification_requests.count() == 0
    # This will not work in selenium, see:
    #  http://forum.jquery.com/topic/validate-possible-bug-for-corner-case-usage-of-remote
    fixture.browser.click('//form[@id="register"]//*[@value="Register"]')
    assert verification_requests.count() == 1


@with_fixtures(WebFixture, PartyAccountFixture, AccountsWebFixture)
def test_register_help_duplicate(web_fixture, party_account_fixture, accounts_web_fixture):
    fixture = accounts_web_fixture
    fixture.browser.open('/a_ui/registerHelp')

    fixture.browser.type('//input[@name="email"]', party_account_fixture.system_account.email)
    fixture.browser.click('//input[@value="Investigate"]')

    assert fixture.browser.location_path == '/a_ui/registerHelp/duplicate'
    fixture.browser.click('//a[text()=" password reset procedure"]')

    assert fixture.browser.location_path == '/a_ui/resetPassword'


@with_fixtures(WebFixture, PartyAccountFixture, AccountsWebFixture)
def test_register_help_not_found(web_fixture, party_account_fixture, accounts_web_fixture):
    fixture = accounts_web_fixture

    fixture.browser.open('/a_ui/registerHelp')

    fixture.browser.type('//input[@name="email"]', 'another_%s' % party_account_fixture.system_account.email)
    fixture.browser.click('//input[@value="Investigate"]')

    assert fixture.browser.location_path == '/a_ui/registerHelp/reregister'
    fixture.browser.click('//a[text()="register again"]')

    assert fixture.browser.location_path == '/a_ui/register'


@with_fixtures(WebFixture, PartyAccountFixture, AccountsWebFixture)
def test_register_help_pending(web_fixture, party_account_fixture, accounts_web_fixture):
    fixture = accounts_web_fixture

    verification_requests = Session.query(VerifyEmailRequest)
    unactivated_account = party_account_fixture.new_system_account(email='unactivated_johndoe@home.org', activated=False)
    activation_request = VerifyEmailRequest(email=unactivated_account.email,
                                            subject_config='accounts.activation_subject',
                                            email_config='accounts.activation_email')
    Session.add(activation_request)
    deferred_activation = ActivateAccount(system_account=unactivated_account, requirements=[activation_request])
    Session.add(deferred_activation)

    fixture.browser.open('/a_ui/registerHelp')
    fixture.browser.type('//input[@name="email"]', unactivated_account.email)
    fixture.browser.click('//input[@value="Investigate"]')

    assert fixture.browser.location_path == '/a_ui/registerHelp/pending'
    assert verification_requests.count() == 1
    party_account_fixture.mailer.reset()
    fixture.browser.click('//input[@value="Send"]')

    assert verification_requests.count() == 1
    assert party_account_fixture.mailer.mail_sent
    assert fixture.browser.location_path == '/a_ui/registerHelp/pending/sent'


@with_fixtures(WebFixture, PartyAccountFixture, AccountsWebFixture)
def test_verify_from_menu(web_fixture, party_account_fixture, accounts_web_fixture):
    fixture = accounts_web_fixture

    account = party_account_fixture.new_system_account(activated=False)
    activation_request = VerifyEmailRequest(email=account.email,
                                            subject_config='accounts.activation_subject',
                                            email_config='accounts.activation_email')
    Session.add(activation_request)
    deferred_activation = ActivateAccount(system_account=account, requirements=[activation_request])
    Session.add(deferred_activation)
    secret_key = activation_request.as_secret_key()

    assert not account.status.is_active()
    fixture.browser.open('/a_ui/verify')

    fixture.browser.type('//form[@id="verify"]//*[@name="email"]', account.email)
    fixture.browser.type('//form[@id="verify"]//*[@name="secret"]', secret_key)
    fixture.browser.type('//form[@id="verify"]//*[@name="password"]', account.password)
    fixture.browser.click('//form[@id="verify"]//*[@value="Verify"]')

    assert fixture.browser.location_path == '/a_ui/thanks'
    assert account.status.is_active()

    # Case needed for when you supply invalid stuff???


@with_fixtures(WebFixture, PartyAccountFixture, AccountsWebFixture)
def test_reset_password(web_fixture, party_account_fixture, accounts_web_fixture):
    fixture = accounts_web_fixture
    account = party_account_fixture.system_account

    fixture.browser.open('/a_ui/resetPassword')
    fixture.browser.type('//input[@name="email"]', account.email)
    fixture.browser.click('//input[@value="Reset password"]')
    assert fixture.browser.location_path == '/a_ui/choosePassword'

    reset_request = Session.query(NewPasswordRequest).filter_by(system_account=party_account_fixture.system_account).one()
    fixture.browser.open('/a_ui/choosePassword')
    fixture.browser.type('//input[@name="email"]', account.email )
    fixture.browser.type('//input[@name="secret"]', reset_request.as_secret_key() )
    new_password = '111111'
    fixture.browser.type('//input[@name="password"]', new_password )
    fixture.browser.type('//input[@name="repeat_password"]', new_password )
    fixture.browser.click('//input[@value="Set new password"]')

    assert fixture.browser.location_path == '/a_ui/passwordChanged'


@with_fixtures(WebFixture, PartyAccountFixture, AccountsWebFixture)
def test_reset_password_from_url(web_fixture, party_account_fixture, accounts_web_fixture):
    fixture = accounts_web_fixture
    account = party_account_fixture.system_account
    new_password_request = NewPasswordRequest(system_account=account)
    Session.add(new_password_request)

    fixture.browser.open('/a_ui/choosePassword?email=%s&secret=%s' % \
                         (account.email, new_password_request.as_secret_key()))
    new_password = '111111'
    fixture.browser.type('//input[@name="password"]', new_password )
    fixture.browser.type('//input[@name="repeat_password"]', new_password )
    fixture.browser.click('//input[@value="Set new password"]')

    assert fixture.browser.location_path == '/a_ui/passwordChanged'

