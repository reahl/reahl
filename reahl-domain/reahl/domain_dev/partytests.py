# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""A heading for this module
=========================

Copyright (C) 2009 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)

"""
from __future__ import unicode_literals
from __future__ import print_function

import hashlib
from string import Template
from datetime import datetime, timedelta

from elixir import using_options

from reahl.sqlalchemysupport import metadata, Session
from nose.tools import istest
from reahl.tofu import test, Fixture
from reahl.tofu import vassert, assert_recent, expected
from reahl.stubble import stubclass

from reahl.component.eggs import ReahlEgg
from reahl.partymodel import Party
from reahl.systemaccountmodel import EmailAndPasswordSystemAccount, VerificationRequest, VerifyEmailRequest, NewPasswordRequest, \
     ChangeAccountEmail, UserSession, PasswordException, NotUniqueException, InvalidPasswordException, KeyException, \
     InvalidEmailException, AccountNotActiveException, NoSuchAccountException, AccountActive, AccountDisabled, AccountNotActivated,\
     AccountManagementInterface,  ActivateAccount
from reahl.domain_dev.fixtures import PartyModelZooMixin


class PartyModelFixture(Fixture, PartyModelZooMixin):
    def new_account_management_interface(self, system_account=None):
        system_account = system_account or self.system_account
        account_management_interface = AccountManagementInterface()
        account_management_interface.password = system_account.password
        account_management_interface.email = system_account.email
        return account_management_interface


@istest
class RegistrationTests(object):
    @test(PartyModelFixture)
    def create_account(self,fixture):
        login_email = 'piet@home.org'
        mailer_stub = fixture.mailer
#        EmailAndPasswordSystemAccount.mailer = mailer_stub
        account_management_interface = fixture.account_management_interface
        account_management_interface.email = login_email

        # Case where the email does not exist as system_account, but as pending new email
        mailer_stub.reset()
        other_system_account = fixture.system_account
        new_email = 'koos@home.org'
        ChangeAccountEmail(other_system_account, new_email)

        with expected(NotUniqueException):
            account_management_interface.email = new_email
            account_management_interface.register()

        vassert( not mailer_stub.mail_sent )
        fixture.system_control.rollback()

        # Case where it all works
        vassert( ActivateAccount.query.count() == 0 )
        account_management_interface.email = login_email
        system_account = account_management_interface.register()
        [activation_action] = ActivateAccount.query.filter_by(system_account=system_account).all()
        activation_request = activation_action.requirements[0]

        vassert( mailer_stub.mail_sent )
        vassert( system_account.email == account_management_interface.email )
        vassert( system_account.password_md5 == hashlib.md5(account_management_interface.password).hexdigest() )
        vassert( system_account.apache_digest == hashlib.md5('%s:%s:%s' %\
                                              (account_management_interface.email,'',account_management_interface.password)).hexdigest() )
        assert_recent( activation_action.deadline - timedelta(days=10) )
        vassert( not system_account.registration_activated )
        vassert( not system_account.account_enabled )
        vassert( not system_account.registration_date )
                 
        vassert( isinstance(system_account, EmailAndPasswordSystemAccount) )
        vassert( system_account.party is None ) 
        vassert( system_account.id )

        # Case where the email name exists
        mailer_stub.reset()
        with expected(NotUniqueException):
            account_management_interface.register()
        vassert( not mailer_stub.mail_sent )

    @test(PartyModelFixture)
    def registration_application_help(self,fixture):
        # Case: there is already an active account by that email
        account_management_interface = fixture.account_management_interface
        vassert( account_management_interface.is_login_active() )

        # Case: there is already an active account with pending_new_email the same as the new email
        fixture.account_management_interface.new_email = 'new_email@home.org'
        fixture.account_management_interface.request_email_change()

        fixture.account_management_interface.email = fixture.account_management_interface.new_email
        vassert( account_management_interface.is_login_active() )

        # Case: there is no account by this email at all
        fixture.account_management_interface.email = 'non-existant@email.com'
        vassert( account_management_interface.is_login_available() )

        # Case: there is a pending registration 
        fixture.account_management_interface.email = 'new_account@home.org'
        fixture.account_management_interface.register()
        vassert( account_management_interface.is_login_pending() )

    @test(PartyModelFixture)
    def send_activation_mail(self,fixture):
        system_account = fixture.new_system_account(email='someone@home.org', activated=False)
        activation_request = VerifyEmailRequest(email=system_account.email,
                                                subject_config='accounts.activation_subject',
                                                email_config='accounts.activation_email')
        activation_action = ActivateAccount(system_account=system_account, requirements=[activation_request])
        mailer_stub = fixture.mailer
        fixture.account_management_interface.email = system_account.email
        fixture.account_management_interface.password = system_account.password
        
        # Case: the first send
        fixture.account_management_interface.send_activation_notification()

        vassert( mailer_stub.mail_recipients == [system_account.email] )
        vassert( mailer_stub.mail_sender == fixture.config.accounts.admin_email )
        substitutions = { 'email': system_account.email,
                          'secret_key': activation_request.as_secret_key()
                        }
        expected_subject = Template(fixture.config.accounts.activation_subject).substitute(substitutions)
        vassert( mailer_stub.mail_subject == expected_subject )
        expected_message = Template(fixture.config.accounts.activation_email).substitute(substitutions)
        vassert( mailer_stub.mail_message == expected_message )
        
    @test(PartyModelFixture)
    def uniqueness_of_request_keys(self,fixture):
        system_account = fixture.new_system_account(activated=False)

        @stubclass(VerificationRequest)
        class VerificationRequestStub(VerificationRequest):
            using_options(metadata=metadata, session=Session, shortnames=True, inheritance='multi')
            def generate_salt(self):
                self.salt = 'not unique'

        with fixture.persistent_test_classes(VerificationRequestStub):
            request1 = VerificationRequestStub(system_account=system_account)
            request2 = VerificationRequestStub(system_account=system_account)
            clashing_request = VerificationRequestStub(system_account=system_account)
            vassert( request1.as_secret_key() != clashing_request.as_secret_key() )
            vassert( request2.as_secret_key() != clashing_request.as_secret_key() )

    @test(PartyModelFixture)
    def activate_via_key(self,fixture):
        system_account = fixture.new_system_account(email='someone@home.org', activated=False)
        activation_request = VerifyEmailRequest(email=system_account.email,
                                                subject_config='accounts.activation_subject',
                                                email_config='accounts.activation_email')
        deferred_activation = ActivateAccount(system_account=system_account, requirements=[activation_request])
        account_management_interface = fixture.account_management_interface
        
        # Case where there is an email mismatch
        account_management_interface.email = 'bad@email.com'
        account_management_interface.secret = activation_request.as_secret_key()
        with expected(InvalidEmailException, test=lambda e: vassert(e.commit)):
            account_management_interface.verify_email()
        vassert( not system_account.registration_activated )

        # Case where there is a key mismatch
        account_management_interface.email = system_account.email
        account_management_interface.secret = 'a key that is invalid'
        with expected(KeyException):
            account_management_interface.verify_email()
        vassert( not system_account.registration_activated )

        # Case where it works
        vassert( not system_account.registration_activated )
        vassert( not system_account.account_enabled )
        vassert( not system_account.registration_date )
        account_management_interface.email = system_account.email
        account_management_interface.secret = activation_request.as_secret_key()
        account_management_interface.verify_email()
        vassert( system_account.registration_activated )
        vassert( system_account.account_enabled )
        assert_recent( system_account.registration_date )
        vassert( activation_request.query.filter_by(id=activation_request.id).count() == 0 )

    @test(PartyModelFixture)
    def expire_stale_requests(self,fixture):
        old_email = 'old@home.org'
        recent_email = 'recent@home.org'
        password = 'pw'
        mailer_stub = fixture.mailer
        EmailAndPasswordSystemAccount.mailer = mailer_stub
        longago = datetime.now() - timedelta(fixture.config.accounts.request_verification_timeout)

        old_account_management_interface = AccountManagementInterface()
        old_account_management_interface.email = old_email
        old_account_management_interface.password = password        
        old_account_management_interface.register()
        old_system_account = EmailAndPasswordSystemAccount.by_email(old_email)
        old_activation_request = VerifyEmailRequest.query.one()
        old_activation_request.deferred_actions[0].deadline = longago

        new_account_management_interface = AccountManagementInterface()
        new_account_management_interface.email = recent_email
        new_account_management_interface.password = password        
        new_account_management_interface.register()
        recent_system_account = EmailAndPasswordSystemAccount.by_email(recent_email)

        ReahlEgg.do_daily_maintenance_for_egg('reahl-domain')
        vassert( EmailAndPasswordSystemAccount.query.filter_by(id=old_system_account.id).count() == 0 )
        vassert( EmailAndPasswordSystemAccount.query.filter_by(id=recent_system_account.id).count() == 1 )

    @test(PartyModelFixture)
    def request_new_password(self,fixture):
        system_account = fixture.new_system_account(activated=False)
        account_management_interface = fixture.new_account_management_interface(system_account=system_account)
        mailer_stub = fixture.mailer

        # Case where an password reset is requested for an email that does not exist
        account_management_interface.email = 'another.%s' % system_account.email
        with expected(NoSuchAccountException):
            account_management_interface.request_password_reset()

        # Case where the user account has not been activated
        vassert( isinstance(system_account.status, AccountNotActivated) )
        account_management_interface.email = system_account.email
        with expected(AccountNotActiveException, test=lambda ex: ex.account_status == system_account.status):
            account_management_interface.request_password_reset()

        system_account.activate()
        system_account.disable()
        # Case where the user account is disabled for another reason
        account_management_interface.email = system_account.email
        vassert( isinstance(system_account.status, AccountDisabled) )
        with expected(AccountNotActiveException, test=lambda ex: ex.account_status == system_account.status):
            account_management_interface.request_password_reset()

        system_account.enable()
        # Case where the user account is active and enabled
        vassert( isinstance(system_account.status, AccountActive) )
        vassert( NewPasswordRequest.query.count() == 0 )
        account_management_interface.email = system_account.email
        account_management_interface.request_password_reset()
        [new_password_request] = NewPasswordRequest.query.filter_by(system_account=system_account).all()

        vassert( mailer_stub.mail_recipients == [system_account.email] )
        vassert( mailer_stub.mail_sender == fixture.config.accounts.admin_email )
        substitutions = { 'email': system_account.email,
                          'secret_key': new_password_request.as_secret_key()
                        }
        expected_subject = Template(fixture.config.accounts.new_password_subject).substitute(substitutions)
        vassert( mailer_stub.mail_subject == expected_subject )
        expected_message = Template(fixture.config.accounts.new_password_email).substitute(substitutions)
        vassert( mailer_stub.mail_message == expected_message )

        # Case where a new password is requested multiple times
        vassert( isinstance(system_account.status, AccountActive) )
        vassert( NewPasswordRequest.query.count() == 1 )
        mailer_stub.reset()
        account_management_interface.request_password_reset()
        vassert( NewPasswordRequest.query.count() == 1 )
        [new_password_request] = NewPasswordRequest.query.filter_by(system_account=system_account).all()

        vassert( mailer_stub.mail_recipients == [system_account.email] )
        vassert( mailer_stub.mail_sender == fixture.config.accounts.admin_email )
        substitutions = { 'email': system_account.email,
                          'secret_key': new_password_request.as_secret_key()
                        }
        expected_subject = Template(fixture.config.accounts.new_password_subject).substitute(substitutions)
        vassert( mailer_stub.mail_subject == expected_subject )
        expected_message = Template(fixture.config.accounts.new_password_email).substitute(substitutions)
        vassert( mailer_stub.mail_message == expected_message )

    @test(PartyModelFixture)
    def set_new_password(self,fixture):
        system_account = fixture.system_account
        new_password_request = NewPasswordRequest(system_account=system_account)
        new_password = system_account.password*2
        account_management_interface = AccountManagementInterface()

        # Case: the key is invalid
        invalid_key = 'in va lid key which is also too long and contains spaces'
        account_management_interface.email = system_account.email
        account_management_interface.secret = invalid_key
        account_management_interface.password = new_password
        with expected(KeyException):
            account_management_interface.choose_new_password()

        # Case: the email is invalid
        invalid_email = 'i am not a valid email'
        account_management_interface.email = invalid_email
        account_management_interface.secret = new_password_request.as_secret_key()
        account_management_interface.password = new_password
        with expected(InvalidEmailException):
            account_management_interface.choose_new_password()

        # Case: the key is valid
        account_management_interface.email = system_account.email
        account_management_interface.secret = new_password_request.as_secret_key()
        account_management_interface.password = new_password
        account_management_interface.choose_new_password()
        system_account.authenticate(new_password) # Should not raise exception

    @test(PartyModelFixture)
    def request_email_change(self,fixture):
        system_account = fixture.new_system_account(activated=False)
        mailer_stub = fixture.mailer
        new_email = 'new@home.org'
        account_management_interface = fixture.new_account_management_interface(system_account=system_account)

        # Case where the user account has not been activated
        vassert( isinstance(system_account.status, AccountNotActivated) )
        account_management_interface.new_email = new_email
        with expected(AccountNotActiveException):
            account_management_interface.request_email_change()

        system_account.activate()
        system_account.disable()
        # Case where the user account is disabled for another reason
        vassert( isinstance(system_account.status, AccountDisabled) )
        account_management_interface.new_email = new_email
        with expected(AccountNotActiveException):
            account_management_interface.request_email_change()

        system_account.enable()
        # Case where the user account is active and enabled, but a clashing email name is requested
        other_party = Party()
        clashing_new_email = 'piet@home.org'
        clashing_system_account = fixture.new_system_account(party=other_party, email=clashing_new_email, activated=True)

        account_management_interface.new_email = clashing_new_email
        with expected(NotUniqueException):
            account_management_interface.request_email_change()

        # Case where the user account is active and enabled, and a new unique email name is requested
        vassert( ChangeAccountEmail.query.count() == 0 )
        account_management_interface.new_email = new_email
        account_management_interface.request_email_change()
        new_email_request = ChangeAccountEmail.query.filter_by(system_account=system_account).one().verify_email_request

        vassert( mailer_stub.mail_recipients == [new_email] )
        vassert( mailer_stub.mail_sender == fixture.config.accounts.admin_email )
        substitutions = { 'email': new_email,
                          'secret_key': new_email_request.as_secret_key()
                        }
        expected_subject = Template(fixture.config.accounts.email_change_subject).substitute(substitutions)
        vassert( mailer_stub.mail_subject == expected_subject )
        expected_message = Template(fixture.config.accounts.email_change_email).substitute(substitutions)
        vassert( mailer_stub.mail_message == expected_message )

        # Case where a email name is requested which matches an already pending one
        account_management_interface.new_email = new_email
        with expected(NotUniqueException):
            account_management_interface.request_email_change()

    @test(PartyModelFixture)
    def verify_email_change(self,fixture):
        system_account = fixture.system_account
        new_email = 'new@home.org'
        change_email_action = ChangeAccountEmail(system_account, new_email)
        request = change_email_action.verify_email_request
        account_management_interface = fixture.account_management_interface

        # Case where there is a password mismatch
        account_management_interface.email = new_email
        account_management_interface.password = 'bad password'
        account_management_interface.secret = request.as_secret_key()
        with expected(InvalidPasswordException, test=lambda e: vassert(e.commit)):
            account_management_interface.verify_email()
        vassert( system_account.email != new_email )

        # Case where there is a key mismatch
        account_management_interface.email = new_email
        account_management_interface.password = system_account.password
        account_management_interface.secret = 'invalid key'
        with expected(KeyException):
            account_management_interface.verify_email()        
        vassert( system_account.email != new_email )

        # Case where it works
        vassert( system_account.email != new_email )
        account_management_interface.email = new_email
        account_management_interface.password = system_account.password
        account_management_interface.secret = request.as_secret_key()
        account_management_interface.verify_email()        
        vassert( VerifyEmailRequest.query.filter_by(id=request.id).count() == 0 )
        vassert( system_account.email == new_email )

    @test(PartyModelFixture)
    def logging_in(self,fixture):
        system_account = fixture.system_account
        session = fixture.context.session
        account_management_interface = fixture.account_management_interface
        account_management_interface.stay_logged_in = False

        # Case: successful email attempt
        vassert( session.account is not system_account )
        account_management_interface.log_in()
        vassert( session.account is system_account )

        # Case: failed email attempts disable the account
        session.account = None
        vassert( system_account.account_enabled )

        account_management_interface.email = system_account.email
        account_management_interface.password = 'gobbledegook'
        for i in range(3):
            with expected(InvalidPasswordException, test=lambda e: vassert(e.commit)):
                account_management_interface.log_in()
            vassert( system_account.failed_logins == i+1 )

        vassert( session.account is None )
        vassert( not system_account.account_enabled )

        # Case: Account is locked
        system_account.disable()
        vassert( isinstance(system_account.status, AccountDisabled) )
        with expected(AccountNotActiveException):
            account_management_interface.log_in()
        vassert( session.account is None )

        # Case: Account is not activated yet
        session.account = None
        system_account = fixture.new_system_account(email='other@email.com', activated=False)

        vassert( isinstance(system_account.status, AccountNotActivated) )
        with expected(AccountNotActiveException):
            account_management_interface.log_in()
        vassert( session.account is None )

        # Case: Login for nonexistant email name
        account_management_interface.email = 'i@do not exist'
        account_management_interface.password = 'gobbledegook'
        with expected(InvalidPasswordException, test=lambda e: vassert(not e.commit)):
            account_management_interface.log_in()
        vassert( session.account is None )



@istest
class UserSessionTests(object):
    @test(PartyModelFixture)
    def login_queries(self, fixture):
        """"""
        
        session = fixture.context.session
        real_user = fixture.party
        config = fixture.context.config
        context = fixture.context
        vassert( config.accounts.idle_secure_lifetime < config.accounts.idle_lifetime )
        vassert( config.accounts.idle_lifetime < config.accounts.idle_lifetime_max )

        # Case: user logs in
        session.last_activity = None
        session.set_as_logged_in(real_user, False)
        vassert( session.is_logged_in() )
        vassert( session.is_secure() )

        # Case: user logs out
        session.log_out()
        vassert( not session.is_logged_in() )
        vassert( not session.is_secure() )

        # Case: user activity is older than secure lifetime
        vassert( (config.accounts.idle_lifetime - config.accounts.idle_secure_lifetime) > 50 )
        session.set_as_logged_in(real_user, False)
        session.last_activity = datetime.now() - timedelta(seconds=config.accounts.idle_secure_lifetime+50)
        vassert( session.is_logged_in() )
        vassert( not session.is_secure() )

        # Case: user activity is older than all lifetimes
        vassert( (config.accounts.idle_lifetime - config.accounts.idle_secure_lifetime) > 50 )
        session.set_as_logged_in(real_user, False)
        session.last_activity = datetime.now() - timedelta(seconds=config.accounts.idle_lifetime+50)
        vassert( not session.is_logged_in() )
        vassert( not session.is_secure() )

        # Case: user activity is older than non-secure lifetime, but keep_me_logged_in is set
        vassert( (config.accounts.idle_lifetime - config.accounts.idle_secure_lifetime) > 50 )
        vassert( (config.accounts.idle_lifetime_max - config.accounts.idle_lifetime) > 50 )
        session.set_as_logged_in(real_user, True)
        session.last_activity = datetime.now() - timedelta(seconds=config.accounts.idle_lifetime+50)
        vassert( session.is_logged_in() )
        vassert( not session.is_secure() )

        # Case: user activity is older than non-secure lifetime max, but keep_me_logged_in is set
        vassert( (config.accounts.idle_lifetime - config.accounts.idle_secure_lifetime) > 50 )
        vassert( (config.accounts.idle_lifetime_max - config.accounts.idle_lifetime) > 50 )
    	session.set_as_logged_in(real_user, True)
        session.last_activity = datetime.now() - timedelta(seconds=config.accounts.idle_lifetime_max+50)
        vassert( not session.is_logged_in() )
        vassert( not session.is_secure() )



