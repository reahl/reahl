# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import unicode_literals
from __future__ import print_function
import six

from nose.tools import istest
from reahl.tofu import Fixture
from reahl.tofu import test
from reahl.tofu import vassert

from reahl.web.ui import TwoColumnPage
from reahl.web.fw import Url
from reahl.web.fw import UserInterface
from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.webdev.tools import Browser
from reahl.domainui_dev.fixtures import BookmarkStub
from reahl.domain_dev.fixtures import PartyModelZooMixin
from reahl.domainui.accounts import AccountUI
from reahl.systemaccountmodel import VerifyEmailRequest, NewPasswordRequest, ActivateAccount

class AccountsWebFixture(Fixture, WebBasicsMixin, PartyModelZooMixin):
    def new_login_bookmark(self, request=None):
        self.context.request = request or self.request
        return self.account_user_interface_factory.get_bookmark(relative_path='/login')
    
    def new_MainUI(self):
        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                account_user_interface_factory = self.define_user_interface('/a_ui',  AccountUI,  {'main_slot': 'main'}, name='test_ui', 
                                                            bookmarks=fixture.bookmarks)
                fixture.account_user_interface_factory = account_user_interface_factory
        return MainUI
    
    def new_wsgi_app(self, enable_js=False):
        return super(AccountsWebFixture, self).new_wsgi_app(enable_js=enable_js,
                                                         site_root=self.MainUI)

    def new_browser(self):
        return Browser(self.wsgi_app)

    def new_bookmarks(self):
        class Bookmarks(object):
            terms_bookmark = BookmarkStub(Url('/#terms'), 'Terms')
            privacy_bookmark = BookmarkStub(Url('/#privacy'), 'Privacy Policy')
            disclaimer_bookmark = BookmarkStub(Url('/#disclaimer'), 'Disclaimer')
        return Bookmarks()

        
@istest
class Tests(object):
    @test(AccountsWebFixture)
    def login_with_detour(self, fixture):
        account = fixture.system_account

        fixture.browser.open('/a_ui/register?a=b&name=kitty')
        vassert( fixture.browser.location_path == '/a_ui/register' )
        vassert( fixture.browser.location_query_string == 'a=b&name=kitty' )

        fixture.browser.open(six.text_type(fixture.new_login_bookmark(request=fixture.browser.last_request).href))
        fixture.browser.click('//a[text()="Forgot your password?"]')
        fixture.browser.go_back()
        fixture.browser.type('//input[@name="email"]', account.email)
        fixture.browser.type('//input[@name="password"]', account.password)
        fixture.browser.click('//input[@value="Log in"]')

        vassert( fixture.browser.location_path == '/a_ui/register' )
        vassert( fixture.browser.location_query_string == 'a=b&name=kitty' )

    @test(AccountsWebFixture)
    def register(self, fixture):
        verification_requests = VerifyEmailRequest.query
        fixture.browser.open('/a_ui/register')

        fixture.browser.type('//form[@id="register"]//*[@name="email"]', 'a@b.org')
        fixture.browser.type('//form[@id="register"]//*[@name="password"]', '111111')
        fixture.browser.type('//form[@id="register"]//*[@name="repeat_password"]', '111111')
        fixture.browser.click('//form[@id="register"]//*[@name="accept_terms"]')

        vassert( verification_requests.count() == 0 )
        # This will not work in selenium, see:
        #  http://forum.jquery.com/topic/validate-possible-bug-for-corner-case-usage-of-remote
        fixture.browser.click('//form[@id="register"]//*[@value="Register"]')
        vassert( verification_requests.count() == 1 )

    @test(AccountsWebFixture)
    def register_help_duplicate(self, fixture):
        fixture.browser.open('/a_ui/registerHelp')

        fixture.browser.type('//input[@name="email"]', fixture.system_account.email)
        fixture.browser.click('//input[@value="Investigate"]')

        vassert( fixture.browser.location_path == '/a_ui/registerHelp/duplicate' )
        fixture.browser.click('//a[text()=" password reset procedure"]')

        vassert( fixture.browser.location_path == '/a_ui/resetPassword' )

    @test(AccountsWebFixture)
    def register_help_not_found(self, fixture):
        fixture.browser.open('/a_ui/registerHelp')

        fixture.browser.type('//input[@name="email"]', 'another_%s' % fixture.system_account.email)
        fixture.browser.click('//input[@value="Investigate"]')

        vassert( fixture.browser.location_path == '/a_ui/registerHelp/reregister' )
        fixture.browser.click('//a[text()="register again"]')

        vassert( fixture.browser.location_path == '/a_ui/register' )

    @test(AccountsWebFixture)
    def register_help_pending(self, fixture):
        verification_requests = VerifyEmailRequest.query
        unactivated_account = fixture.new_system_account(email='unactivated_johndoe@home.org', activated=False)
        activation_request = VerifyEmailRequest(email=unactivated_account.email,
                                                subject_config='accounts.activation_subject',
                                                email_config='accounts.activation_email')
        deferred_activation = ActivateAccount(system_account=unactivated_account, requirements=[activation_request])

        fixture.browser.open('/a_ui/registerHelp')
        fixture.browser.type('//input[@name="email"]', unactivated_account.email)
        fixture.browser.click('//input[@value="Investigate"]')

        vassert( fixture.browser.location_path == '/a_ui/registerHelp/pending' )
        vassert( verification_requests.count() == 1 )
        fixture.mailer.reset()
        fixture.browser.click('//input[@value="Send"]')

        vassert( verification_requests.count() == 1 )
        vassert( fixture.mailer.mail_sent )
        vassert( fixture.browser.location_path == '/a_ui/registerHelp/pending/sent' )

    @test(AccountsWebFixture)
    def verify_from_menu(self, fixture):
        account = fixture.new_system_account(activated=False)
        activation_request = VerifyEmailRequest(email=account.email,
                                                subject_config='accounts.activation_subject',
                                                email_config='accounts.activation_email')
        deferred_activation = ActivateAccount(system_account=account, requirements=[activation_request])
        secret_key = activation_request.as_secret_key()

        vassert( not account.status.is_active() )
        fixture.browser.open('/a_ui/verify')

        fixture.browser.type('//form[@id="verify"]//*[@name="email"]', account.email)
        fixture.browser.type('//form[@id="verify"]//*[@name="secret"]', secret_key)
        fixture.browser.type('//form[@id="verify"]//*[@name="password"]', account.password)
        fixture.browser.click('//form[@id="verify"]//*[@value="Verify"]')

        vassert( fixture.browser.location_path == '/a_ui/thanks' )
        vassert( account.status.is_active() )

        # Case needed for when you supply invalid stuff???

    @test(AccountsWebFixture)
    def reset_password(self, fixture):
        account = fixture.system_account

        fixture.browser.open('/a_ui/resetPassword')
        fixture.browser.type('//input[@name="email"]', account.email)
        fixture.browser.click('//input[@value="Reset password"]')
        vassert( fixture.browser.location_path == '/a_ui/choosePassword' )

        reset_request = NewPasswordRequest.query.filter_by(system_account=fixture.system_account).one()
        fixture.browser.open('/a_ui/choosePassword')
        fixture.browser.type('//input[@name="email"]', account.email )
        fixture.browser.type('//input[@name="secret"]', reset_request.as_secret_key() )
        new_password = '111111'
        fixture.browser.type('//input[@name="password"]', new_password )
        fixture.browser.type('//input[@name="repeat_password"]', new_password )
        fixture.browser.click('//input[@value="Set new password"]')

        vassert( fixture.browser.location_path == '/a_ui/passwordChanged' )

    @test(AccountsWebFixture)
    def reset_password_from_url(self, fixture):
        account = fixture.system_account
        new_password_request = NewPasswordRequest(system_account=account)

        fixture.browser.open('/a_ui/choosePassword?email=%s&secret=%s' % \
                             (account.email, new_password_request.as_secret_key()))
        new_password = '111111'
        fixture.browser.type('//input[@name="password"]', new_password )
        fixture.browser.type('//input[@name="repeat_password"]', new_password )
        fixture.browser.click('//input[@value="Set new password"]')

        vassert( fixture.browser.location_path == '/a_ui/passwordChanged' )
