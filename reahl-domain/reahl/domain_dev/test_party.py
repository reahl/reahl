# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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



import passlib.hash
from string import Template
from datetime import datetime, timedelta

from sqlalchemy import Column, ForeignKey, Integer

from reahl.sqlalchemysupport import Session
from reahl.tofu import assert_recent, expected, NoException
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import stubclass

from reahl.component.eggs import ReahlEgg
from reahl.component.context import ExecutionContext
from reahl.domain.partymodel import Party
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount, VerificationRequest, VerifyEmailRequest, \
    NewPasswordRequest, ChangeAccountEmail, NotUniqueException, InvalidPasswordException, KeyException, \
    InvalidEmailException, AccountNotActiveException, NoSuchAccountException, AccountActive, AccountDisabled, \
    AccountNotActivated, AccountManagementInterface,  ActivateAccount, LoginSession

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.domain_dev.fixtures import PartyAccountFixture
from reahl.dev.fixtures import ReahlSystemFixture
from reahl.web_dev.fixtures import WebFixture

def assert_not_set_to_commit(e):
    assert not e.commit
def assert_is_set_to_commit(e):
    assert e.commit

    
@with_fixtures(ReahlSystemFixture, PartyAccountFixture)
def test_create_account(reahl_system_fixture, party_account_fixture):
    fixture = party_account_fixture

    login_email = 'piet@home.org'
    mailer_stub = fixture.mailer
    # EmailAndPasswordSystemAccount.mailer = mailer_stub
    account_management_interface = fixture.account_management_interface
    account_management_interface.email = login_email

    # Case where the email does not exist as system_account, but as pending new email
    mailer_stub.reset()
    other_system_account = fixture.system_account
    new_email = 'koos@home.org'
    Session.add(ChangeAccountEmail(other_system_account, new_email))

    with expected(NotUniqueException):
        account_management_interface.email = new_email
        account_management_interface.register()

    assert not mailer_stub.mail_sent
    reahl_system_fixture.system_control.rollback()

    # Case where it all works
    assert Session.query(ActivateAccount).count() == 0
    account_management_interface.email = login_email
    system_account = account_management_interface.register()
    [activation_action] = Session.query(ActivateAccount).filter_by(system_account=system_account).all()
    activation_request = activation_action.requirements[0]

    assert mailer_stub.mail_sent
    assert system_account.email == account_management_interface.email
    assert_recent( activation_action.deadline - timedelta(days=10) )
    assert not system_account.registration_activated
    assert not system_account.account_enabled
    assert not system_account.registration_date

    assert isinstance(system_account, EmailAndPasswordSystemAccount)
    assert system_account.owner is None
    assert system_account.id

    # Case where the email name exists
    mailer_stub.reset()
    with expected(NotUniqueException):
        account_management_interface.register()
    assert not mailer_stub.mail_sent


@with_fixtures(PartyAccountFixture)
def test_registration_application_help(party_account_fixture):
    fixture = party_account_fixture

    # Case: there is already an active account by that email
    account_management_interface = fixture.account_management_interface
    assert account_management_interface.is_login_active()

    # Case: there is already an active account with pending_new_email the same as the new email
    fixture.account_management_interface.new_email = 'new_email@home.org'
    fixture.account_management_interface.request_email_change()

    fixture.account_management_interface.email = fixture.account_management_interface.new_email
    assert account_management_interface.is_login_active()

    # Case: there is no account by this email at all
    fixture.account_management_interface.email = 'non-existant@email.com'
    assert account_management_interface.is_login_available()

    # Case: there is a pending registration
    fixture.account_management_interface.email = 'new_account@home.org'
    fixture.account_management_interface.register()
    assert account_management_interface.is_login_pending()


@with_fixtures(ReahlSystemFixture, PartyAccountFixture)
def test_send_activation_mail(reahl_system_fixture, party_account_fixture):
    fixture = party_account_fixture

    system_account = fixture.new_system_account(email='someone@home.org', activated=False)
    activation_request = VerifyEmailRequest(email=system_account.email,
                                            subject_config='accounts.activation_subject',
                                            email_config='accounts.activation_email')
    Session.add(activation_request)
    activation_action = ActivateAccount(system_account=system_account, requirements=[activation_request])
    Session.add(activation_action)
    mailer_stub = fixture.mailer
    fixture.account_management_interface.email = system_account.email
    fixture.account_management_interface.password = system_account.password

    # Case: the first send
    fixture.account_management_interface.send_activation_notification()

    assert mailer_stub.mail_recipients == [system_account.email]
    assert mailer_stub.mail_sender == reahl_system_fixture.config.accounts.admin_email
    substitutions = { 'email': system_account.email,
                      'secret_key': activation_request.as_secret_key()
                    }
    expected_subject = Template(reahl_system_fixture.config.accounts.activation_subject).substitute(substitutions)
    assert mailer_stub.mail_subject == expected_subject
    expected_message = Template(reahl_system_fixture.config.accounts.activation_email).substitute(substitutions)
    assert mailer_stub.mail_message == expected_message


@with_fixtures(SqlAlchemyFixture, PartyAccountFixture)
def test_uniqueness_of_request_keys(sql_alchemy_fixture, party_account_fixture):
    fixture = party_account_fixture

    system_account = fixture.new_system_account(activated=False)

    @stubclass(VerificationRequest)
    class VerificationRequestStub(VerificationRequest):
        __tablename__ = 'verificationrequeststub'
        __mapper_args__ = {'polymorphic_identity': 'verificationrequeststub'}
        id = Column(Integer, ForeignKey(VerificationRequest.id), primary_key=True)

        def generate_salt(self):
            self.salt = 'not unique'

    with sql_alchemy_fixture.persistent_test_classes(VerificationRequestStub):
        request1 = VerificationRequestStub()
        Session.add(request1)
        request2 = VerificationRequestStub()
        Session.add(request2)
        clashing_request = VerificationRequestStub()
        Session.add(clashing_request)
        assert request1.as_secret_key() != clashing_request.as_secret_key()
        assert request2.as_secret_key() != clashing_request.as_secret_key()

    
@with_fixtures(PartyAccountFixture)
def test_activate_via_key(party_account_fixture):
    fixture = party_account_fixture

    system_account = fixture.new_system_account(email='someone@home.org', activated=False)
    activation_request = VerifyEmailRequest(email=system_account.email,
                                            subject_config='accounts.activation_subject',
                                            email_config='accounts.activation_email')
    Session.add(activation_request)
    deferred_activation = ActivateAccount(system_account=system_account, requirements=[activation_request])
    Session.add(deferred_activation)
    account_management_interface = fixture.account_management_interface

    # Case where there is an email mismatch
    account_management_interface.email = 'bad@email.com'
    account_management_interface.secret = activation_request.as_secret_key()
    with expected(InvalidEmailException, test=assert_is_set_to_commit):
        account_management_interface.verify_email()
    assert not system_account.registration_activated

    # Case where there is a key mismatch
    account_management_interface.email = system_account.email
    account_management_interface.secret = 'a key that is invalid'
    with expected(KeyException):
        account_management_interface.verify_email()
    assert not system_account.registration_activated

    # Case where it works
    assert not system_account.registration_activated
    assert not system_account.account_enabled
    assert not system_account.registration_date
    account_management_interface.email = system_account.email
    account_management_interface.secret = activation_request.as_secret_key()
    account_management_interface.verify_email()
    assert system_account.registration_activated
    assert system_account.account_enabled
    assert_recent( system_account.registration_date )
    assert Session.query(VerifyEmailRequest).filter_by(id=activation_request.id).count() == 0


@with_fixtures(ReahlSystemFixture, PartyAccountFixture)
def test_expire_stale_requests(reahl_system_fixture, party_account_fixture):
    fixture = party_account_fixture

    old_email = 'old@home.org'
    recent_email = 'recent@home.org'
    password = 'pw'
    mailer_stub = fixture.mailer
    EmailAndPasswordSystemAccount.mailer = mailer_stub
    longago = datetime.now() - timedelta(reahl_system_fixture.config.accounts.request_verification_timeout)

    old_account_management_interface = AccountManagementInterface()
    old_account_management_interface.email = old_email
    old_account_management_interface.password = password
    old_account_management_interface.register()
    old_system_account = EmailAndPasswordSystemAccount.by_email(old_email)
    old_activation_request = Session.query(VerifyEmailRequest).one()
    old_activation_request.deferred_actions[0].deadline = longago

    new_account_management_interface = AccountManagementInterface()
    new_account_management_interface.email = recent_email
    new_account_management_interface.password = password
    new_account_management_interface.register()
    recent_system_account = EmailAndPasswordSystemAccount.by_email(recent_email)

    ReahlEgg.do_daily_maintenance_for_egg('reahl-domain')
    assert Session.query(EmailAndPasswordSystemAccount).filter_by(id=old_system_account.id).count() == 0
    assert Session.query(EmailAndPasswordSystemAccount).filter_by(id=recent_system_account.id).count() == 1


@with_fixtures(ReahlSystemFixture, PartyAccountFixture)
def test_request_new_password(reahl_system_fixture, party_account_fixture):
    fixture = party_account_fixture


    system_account = fixture.new_system_account(activated=False)
    account_management_interface = fixture.new_account_management_interface(system_account=system_account)
    mailer_stub = fixture.mailer

    # Case where an password reset is requested for an email that does not exist
    account_management_interface.email = 'another.%s' % system_account.email
    with expected(NoSuchAccountException):
        account_management_interface.request_password_reset()

    # Case where the user account has not been activated
    assert isinstance(system_account.status, AccountNotActivated)
    account_management_interface.email = system_account.email

    def exception_matches_system_account_status(ex):
        assert ex.account_status.as_user_message() == system_account.status.as_user_message()

    with expected(AccountNotActiveException, test=exception_matches_system_account_status):
        account_management_interface.request_password_reset()

    system_account.activate()
    system_account.disable()
    # Case where the user account is disabled for another reason
    account_management_interface.email = system_account.email
    assert isinstance(system_account.status, AccountDisabled)
    with expected(AccountNotActiveException, test=exception_matches_system_account_status):
        account_management_interface.request_password_reset()

    system_account.enable()
    # Case where the user account is active and enabled
    assert isinstance(system_account.status, AccountActive)
    assert Session.query(NewPasswordRequest).count() == 0
    account_management_interface.email = system_account.email
    account_management_interface.request_password_reset()
    [new_password_request] = Session.query(NewPasswordRequest).filter_by(system_account=system_account).all()

    assert mailer_stub.mail_recipients == [system_account.email]
    assert mailer_stub.mail_sender == reahl_system_fixture.config.accounts.admin_email
    substitutions = { 'email': system_account.email,
                      'secret_key': new_password_request.as_secret_key()
                    }
    expected_subject = Template(reahl_system_fixture.config.accounts.new_password_subject).substitute(substitutions)
    assert mailer_stub.mail_subject == expected_subject
    expected_message = Template(reahl_system_fixture.config.accounts.new_password_email).substitute(substitutions)
    assert mailer_stub.mail_message == expected_message

    # Case where a new password is requested multiple times
    assert isinstance(system_account.status, AccountActive)
    assert Session.query(NewPasswordRequest).count() == 1
    mailer_stub.reset()
    account_management_interface.request_password_reset()
    assert Session.query(NewPasswordRequest).count() == 1
    [new_password_request] = Session.query(NewPasswordRequest).filter_by(system_account=system_account).all()

    assert mailer_stub.mail_recipients == [system_account.email]
    assert mailer_stub.mail_sender == reahl_system_fixture.config.accounts.admin_email
    substitutions = { 'email': system_account.email,
                      'secret_key': new_password_request.as_secret_key()
                    }
    expected_subject = Template(reahl_system_fixture.config.accounts.new_password_subject).substitute(substitutions)
    assert mailer_stub.mail_subject == expected_subject
    expected_message = Template(reahl_system_fixture.config.accounts.new_password_email).substitute(substitutions)
    assert mailer_stub.mail_message == expected_message


@with_fixtures(PartyAccountFixture)
def test_set_new_password(party_account_fixture):
    fixture = party_account_fixture

    system_account = fixture.system_account
    new_password_request = NewPasswordRequest(system_account=system_account)
    Session.add(new_password_request)
    new_password = system_account.password*2
    account_management_interface = AccountManagementInterface()
    Session.add(account_management_interface)

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


@with_fixtures(PartyAccountFixture)
def test_migrate_password_hash_scheme(party_account_fixture):
    fixture = party_account_fixture

    system_account = fixture.system_account
    md5_hash = passlib.hash.hex_md5.hash(system_account.password)
    system_account.password_hash = md5_hash

    system_account.authenticate(system_account.password)
    assert system_account.password_hash != md5_hash

    with expected(NoException):
        system_account.authenticate(system_account.password)


@with_fixtures(ReahlSystemFixture, PartyAccountFixture)
def test_request_email_change(reahl_system_fixture, party_account_fixture):
    fixture = party_account_fixture

    system_account = fixture.new_system_account(activated=False)
    mailer_stub = fixture.mailer
    new_email = 'new@home.org'
    account_management_interface = fixture.new_account_management_interface(system_account=system_account)

    # Case where the user account has not been activated
    assert isinstance(system_account.status, AccountNotActivated)
    account_management_interface.new_email = new_email
    with expected(AccountNotActiveException):
        account_management_interface.request_email_change()

    system_account.activate()
    system_account.disable()
    # Case where the user account is disabled for another reason
    assert isinstance(system_account.status, AccountDisabled)
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
    assert Session.query(ChangeAccountEmail).count() == 0
    account_management_interface.new_email = new_email
    account_management_interface.request_email_change()
    new_email_request = Session.query(ChangeAccountEmail).filter_by(system_account=system_account).one().verify_email_request

    assert mailer_stub.mail_recipients == [new_email]
    assert mailer_stub.mail_sender == reahl_system_fixture.config.accounts.admin_email
    substitutions = { 'email': new_email,
                      'secret_key': new_email_request.as_secret_key()
                    }
    expected_subject = Template(reahl_system_fixture.config.accounts.email_change_subject).substitute(substitutions)
    assert mailer_stub.mail_subject == expected_subject
    expected_message = Template(reahl_system_fixture.config.accounts.email_change_email).substitute(substitutions)
    assert mailer_stub.mail_message == expected_message

    # Case where a email name is requested which matches an already pending one
    account_management_interface.new_email = new_email
    with expected(NotUniqueException):
        account_management_interface.request_email_change()


@with_fixtures(PartyAccountFixture)
def test_verify_email_change(party_account_fixture):
    fixture = party_account_fixture

    system_account = fixture.system_account
    new_email = 'new@home.org'
    change_email_action = ChangeAccountEmail(system_account, new_email)
    Session.add(change_email_action)
    request = change_email_action.verify_email_request
    account_management_interface = fixture.account_management_interface

    # Case where there is a password mismatch
    account_management_interface.email = new_email
    account_management_interface.password = 'bad password'
    account_management_interface.secret = request.as_secret_key()
    with expected(InvalidPasswordException, test=assert_is_set_to_commit):
        account_management_interface.verify_email()
    assert system_account.email != new_email

    # Case where there is a key mismatch
    account_management_interface.email = new_email
    account_management_interface.password = system_account.password
    account_management_interface.secret = 'invalid key'
    with expected(KeyException):
        account_management_interface.verify_email()
    assert system_account.email != new_email

    # Case where it works
    assert system_account.email != new_email
    account_management_interface.email = new_email
    account_management_interface.password = system_account.password
    account_management_interface.secret = request.as_secret_key()
    account_management_interface.verify_email()
    assert Session.query(VerifyEmailRequest).filter_by(id=request.id).count() == 0
    assert system_account.email == new_email


@with_fixtures(ReahlSystemFixture, PartyAccountFixture)
def test_logging_in(reahl_system_fixture, party_account_fixture):
    fixture = party_account_fixture

    system_account = fixture.system_account
    login_session = LoginSession.for_session(reahl_system_fixture.context.session)
    account_management_interface = fixture.account_management_interface
    account_management_interface.stay_logged_in = False

    # Case: successful email attempt
    assert login_session.account is not system_account
    account_management_interface.log_in()
    assert login_session.account is system_account

    # Case: failed email attempts disable the account
    login_session.account = None
    assert system_account.account_enabled

    account_management_interface.email = system_account.email
    account_management_interface.password = 'gobbledegook'
    for i in list(range(3)):
        with expected(InvalidPasswordException, test=assert_is_set_to_commit):
            account_management_interface.log_in()
        assert system_account.failed_logins == i+1

    assert login_session.account is None
    assert not system_account.account_enabled

    # Case: Account is locked
    system_account.disable()
    assert isinstance(system_account.status, AccountDisabled)
    with expected(AccountNotActiveException):
        account_management_interface.log_in()
    assert login_session.account is None

    # Case: Account is not activated yet
    login_session.account = None
    system_account = fixture.new_system_account(email='other@email.com', activated=False)

    assert isinstance(system_account.status, AccountNotActivated)
    with expected(AccountNotActiveException):
        account_management_interface.log_in()
    assert login_session.account is None

    # Case: Login for nonexistant email name
    account_management_interface.email = 'i@do not exist'
    account_management_interface.password = 'gobbledegook'
    with expected(InvalidPasswordException, test=assert_not_set_to_commit):
        account_management_interface.log_in()
    assert login_session.account is None


@with_fixtures(PartyAccountFixture, WebFixture)
def test_login_queries(party_account_fixture, web_fixture):
    """"""
    context = ExecutionContext.get_context()

    config = context.config
    user_session = context.session
    login_session = LoginSession.for_session(context.session)
    system_account = party_account_fixture.system_account

    web_fixture.request.scheme = 'https'
    context.request.cookies[config.web.secure_key_name] = user_session.secure_salt
    assert config.web.idle_secure_lifetime < config.web.idle_lifetime
    assert config.web.idle_lifetime < config.web.idle_lifetime_max

    # Case: user logs in
    user_session.last_activity = None
    login_session.set_as_logged_in(system_account, False)
    assert login_session.is_logged_in()
    assert login_session.is_logged_in(secured=True)

    # Case: user logs out
    login_session.log_out()
    assert not login_session.is_logged_in()
    assert not login_session.is_logged_in(secured=True)

    # Case: user activity is older than secure lifetime
    assert (config.web.idle_lifetime - config.web.idle_secure_lifetime) > 50
    login_session.set_as_logged_in(system_account, False)
    user_session.last_activity = datetime.now() - timedelta(seconds=config.web.idle_secure_lifetime+50)
    assert login_session.is_logged_in()
    assert not login_session.is_logged_in(secured=True)

    # Case: user activity is older than all lifetimes
    assert (config.web.idle_lifetime - config.web.idle_secure_lifetime) > 50
    login_session.set_as_logged_in(system_account, False)
    user_session.last_activity = datetime.now() - timedelta(seconds=config.web.idle_lifetime+50)
    assert not login_session.is_logged_in()
    assert not login_session.is_logged_in(secured=True)

    # Case: user activity is older than non-secure lifetime, but keep_me_logged_in is set
    assert (config.web.idle_lifetime - config.web.idle_secure_lifetime) > 50
    assert (config.web.idle_lifetime_max - config.web.idle_lifetime) > 50
    login_session.set_as_logged_in(system_account, True)
    user_session.last_activity = datetime.now() - timedelta(seconds=config.web.idle_lifetime+50)
    assert login_session.is_logged_in()
    assert not login_session.is_logged_in(secured=True)

    # Case: user activity is older than non-secure lifetime max, but keep_me_logged_in is set
    assert (config.web.idle_lifetime - config.web.idle_secure_lifetime) > 50
    assert (config.web.idle_lifetime_max - config.web.idle_lifetime) > 50
    login_session.set_as_logged_in(system_account, True)
    Session.flush()
    user_session.last_activity = datetime.now() - timedelta(seconds=config.web.idle_lifetime_max+50)
    assert not login_session.is_logged_in()
    assert not login_session.is_logged_in(secured=True)

