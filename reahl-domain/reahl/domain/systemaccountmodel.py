# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""A collection of classes to deal with accounts for different parties on a system.


Run 'reahl componentinfo reahl-domain' for information on configuration.

"""

from datetime import datetime, timedelta
import passlib.context
import re
import random
from string import Template
import logging

from sqlalchemy import Column, Integer, ForeignKey, UnicodeText, String, DateTime, Boolean, Unicode
from sqlalchemy.orm import relationship, reconstructor

from reahl.sqlalchemysupport import Base, Session, session_scoped

from reahl.component.exceptions import DomainException, ProgrammerError

from reahl.mailutil.mail import Mailer, MailMessage
from reahl.component.config import Configuration, ConfigSetting
from reahl.component.i18n import Catalogue
from reahl.component.modelinterface import EmailField, PasswordField, BooleanField, EqualToConstraint, \
                                            Field, Event, ExposedNames, Action
from reahl.component.context import ExecutionContext
from reahl.domain.partymodel import Party
from reahl.domain.workflowmodel import DeferredAction, Requirement

_ = Catalogue('reahl-domain')

class SystemAccountConfig(Configuration):
    """Configuration containing general system information
    
    All templates in this configuration are PEP292 formatted strings that can use the following substitutions:

    $email  
        The email address to which the message applies

    $secret 
        The relevant secret key
    """

    filename = 'systemaccountmodel.config.py' 
    config_key = 'accounts'                   

    admin_email = ConfigSetting(default='admin@example.com', description='The email address from which automated emails are sent', dangerous=True) 
    request_verification_timeout = ConfigSetting(default=10, description='The time an unvalidated request is kept alive') 
    activation_subject = ConfigSetting(default='''Your registration for $email''', description='A Subject used for activation emails') 
    activation_email = ConfigSetting(default='''You, or someone on your behalf requested to be registered using $email.\n\n'''\
        '''If you have received this message in error, please ignore it.\n\n'''\
        '''Your secret key is: $secret_key\n\n''', description='Body of an activation email') 
    new_password_subject = ConfigSetting(default='''Your password for $email''', description='Subject used for password reset emails') 
    new_password_email = ConfigSetting(default='''You, or someone on your behalf requested to pick a new password for $email.\n\n'''\
        '''If you have received this message in error, please ignore it.\n\n'''\
        '''Your secret key is: $secret_key\n\n''', description='Body of a password reset email') 
    email_change_subject = ConfigSetting(default='''Your new email $email''', description='Subject used for email address change emails') 
    email_change_email = ConfigSetting(default='''You, or someone on your behalf requested to change your email to $email.\n\n'''\
        '''If you have received this message in error, please ignore it.\n\n'''\
        '''You need to accept this change before it will take effect.\n\n'''\
        '''Your secret key is: $secret_key\n\n''', description='Body of an email address changed email') 
    mailer_class = ConfigSetting(default=Mailer, description='The class to instantiate for sending email') 


class SystemAccount(Base):
    """The credentials for someone to be able to log into the system."""
    __tablename__ = 'systemaccount'

    id = Column(Integer, primary_key=True)
    discriminator = Column('row_type', String(40))
    __mapper_args__ = {
        'polymorphic_identity': 'systemaccount',
        'polymorphic_on': discriminator
    }

    owner_party_id = Column(Integer, ForeignKey(Party.id))
    owner = relationship(Party) #: The party to whom this account belongs.

    registration_date = Column(DateTime)  #: The date when this account was first registered.
    account_enabled = Column(Boolean, nullable=False, default=False) #: Whether this account is enabled or not

    failed_logins = Column(Integer, nullable=False, default=0) #: The number of failed login attempts using this account.

    @property
    def registration_activated(self):
        return self.registration_date is not None

    @property
    def status(self):
        if not self.registration_activated:
            return AccountNotActivated()
        if not self.account_enabled:
            return AccountDisabled()
        return AccountActive()

    def assert_account_live(self):
        if not self.status.is_active(): 
            raise AccountNotActiveException(self.status)
        
    def activate(self):
        self.registration_date = datetime.now()
        self.enable()

    def cancel_reservation(self):
        if self.account_enabled:
            raise ProgrammerError('attempted to cancel a reserved account which is already active')
        Session.delete(self)

    def enable(self):
        self.account_enabled = True

    def disable(self):
        self.account_enabled = False


class EmailAndPasswordSystemAccount(SystemAccount):
    """An EmailAndPasswordSystemAccount uses an email address to identify the account uniquely,
       and uses a password to authenticate login attempts.
    """
    __tablename__ = 'emailandpasswordsystemaccount'
    __mapper_args__ = {'polymorphic_identity': 'emailandpasswordsystemaccount'}
    id = Column(Integer, ForeignKey(SystemAccount.id, ondelete='CASCADE'), primary_key=True)

    password_hash = Column(Unicode(1024), nullable=False)  #: The hashed password
    email = Column(Unicode(254), nullable=False, unique=True, index=True) #: The email address of this account

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_on_load()

    @reconstructor
    def init_on_load(self):
        self.crypt_context = passlib.context.CryptContext(schemes=["pbkdf2_sha512", "hex_md5"],
                                                          deprecated="auto")

    @classmethod
    def by_email(cls, email):
        matches = Session.query(cls).filter_by(email=email)
        if matches.count() == 0:
            raise NoSuchAccountException()
        return matches.one()
    
    @classmethod
    def email_changes_are_pending_for(cls, email):
        all_pending_requests = Session.query(VerifyEmailRequest).join(VerifyEmailRequest.deferred_actions, ChangeAccountEmail)
        clashing_requests = all_pending_requests.filter(VerifyEmailRequest.email==email)
        return clashing_requests.count() > 0
    
    @classmethod
    def assert_email_unique(cls, email):
        not_unique = Session.query(cls).filter_by(email=email).count() > 0
        not_unique = not_unique or cls.email_changes_are_pending_for(email)
        if not_unique:
            raise NotUniqueException()

    @classmethod
    def is_login_active(cls, email):
        try:
            target_account = cls.by_email(email)
            return target_account.registration_activated
        except NoSuchAccountException:
            pass
        return cls.email_changes_are_pending_for(email)

    @classmethod
    def is_login_pending(cls, email):
        try:
            target_account = cls.by_email(email)
            return not target_account.registration_activated
        except NoSuchAccountException:
            return False
    
    @classmethod
    def is_login_available(cls, email):
        return not (cls.is_login_active(email) or cls.is_login_pending(email))

    @classmethod
    def register(cls, email, password):
        return EmailAndPasswordSystemAccount.reserve(email, password, None)

    @classmethod
    def reserve(cls, email, password, party):
        cls.assert_email_unique(email)
        system_account = cls(owner=party, email=email)
        Session.add(system_account)
        system_account.set_new_password(email, password)
        verification_request = VerifyEmailRequest(email=email,
                                                  subject_config='accounts.activation_subject',
                                                  email_config='accounts.activation_email')
        Session.add(verification_request)
        Session.flush()
        deferred_activation = ActivateAccount(system_account=system_account, 
                                              requirements=[verification_request])
        Session.add(deferred_activation)
        system_account.send_activation_notification()

        return system_account

    @classmethod
    def log_in(cls, email, password, stay_logged_in):
        try:
            target_account = EmailAndPasswordSystemAccount.by_email(email)
        except NoSuchAccountException:
            raise InvalidPasswordException()
        target_account.authenticate(password)
        login_session = LoginSession.for_current_session()
        login_session.log_out()
        login_session.set_as_logged_in(target_account, stay_logged_in)

    def authenticate(self, password):
        self.assert_account_live()

        valid, new_hash = self.crypt_context.verify_and_update(password, self.password_hash)
        if not valid:
            self.failed_logins += 1
            if self.failed_logins >= 3:
                self.disable()
            raise InvalidPasswordException(commit=True)
        if new_hash:
            self.password_hash = new_hash

    def send_activation_notification(self):
        verification_request = Session.query(VerifyEmailRequest).join(VerifyEmailRequest.deferred_actions, ActivateAccount)\
                               .filter(ActivateAccount.system_account==self).one()
        verification_request.send_notification()

    def request_new_password(self):
        self.assert_account_live()
        existing_requests = Session.query(NewPasswordRequest).filter_by(system_account=self)
        if existing_requests.count() == 0:
            Session.add(NewPasswordRequest(system_account=self))
        self.send_new_password_mail()

    def send_new_password_mail(self):
        request = Session.query(NewPasswordRequest).filter_by(system_account=self).one()
        request.send_notification()

    def set_new_password(self, email, password):
        if self.email != email:
            raise InvalidEmailException()

        new_hash = self.crypt_context.hash(password)
        self.password_hash = new_hash

    def request_email_change(self, new_email):
        self.assert_account_live()
        self.assert_email_unique(new_email)

        Session.add(ChangeAccountEmail(self, new_email))
        self.send_email_change_mail()

    def send_email_change_mail(self):
        change_email_action = Session.query(ChangeAccountEmail).filter_by(system_account=self).one()
        change_email_action.send_notification()

    def set_new_email(self, new_login, password):
        self.authenticate(password)
        self.email = new_login


@session_scoped
class AccountManagementInterface(Base):
    """A session scoped object that exposes a number of Fields and Events that user interface 
       Widgets can use to access the functionality of this module.
       
       Obtain an instance of AccountManagementInterface using AccountManagementInterface.for_current_session().

       **exposed fields:**
       
        - email: For input of any email address for use by Events.
        - new_email: For choosing a new email address (see events.change_email_event)
        - password: For typing a password for use by several Events.
        - repeat_password: For confirming a that fields.password was typed correctly.
        - stay_logged_in: Used when logging in to indicate that the user wishes to stay logged in for longer before the login times out.
        - secret: The secret key sent via email to verify the user's identity.
        - accept_terms: Used when registering to indicate whether the user accepts the terms of the application.

       **exposed events:**
       
        - verify_event = Ask the system to verify the fields.email address entered.
        - register_event = Register a new account.
        - change_email_event = Requests a given email address to be changed.
        - investigate_event = Investigates whether a given email address is registered.
        - choose_password_event = Selects a new password given in fields.new_password (fields.secret should also be supplied).
        - reset_password_event = Requests that a password change be initiated (this will send a secret key to the current registered email).
        - login_event = Logs into the system using fields.email and fields.password
        - resend_event = Resends a secret of an outstanding request (to fields.email).
        - log_out_event = Logs out the current account.
    """
    __tablename__ = 'accountmanagementinterface'
    id = Column(Integer, primary_key=True)
    email = Column(Unicode(254), default=None, index=True)

    stay_logged_in = False

    fields = ExposedNames()
    fields.email = lambda i: EmailField(required=True, label=_('Email'))
    fields.new_email = lambda i: EmailField(required=True, label=_('New email'))
    fields.password = lambda i: PasswordField(required=True, label=_('Password'))
    fields.stay_logged_in = lambda i: BooleanField(default=False, label=_('Remember me?'))
    fields.secret = lambda i: Field(required=True, label=_('Secret key'))
    fields.repeat_password = lambda i: RepeatPasswordField(i.fields.password, required=True, label=_('Re-type password'), required_message=_('Please type your password again.'))
    fields.accept_terms = lambda i: BooleanField(required=True,
                                                 required_message=_('Please accept the terms of service'),
                                                 default=False, label=_('I accept the terms of service'))
    
    events = ExposedNames()
    events.verify_event = lambda i: Event(label=_('Verify'), action=Action(i.verify_email))
    events.register_event = lambda i: Event(label=_('Register'), action=Action(i.register))
    events.change_email_event = lambda i: Event(label=_('Change email address'), action=Action(i.request_email_change))
    events.investigate_event = lambda i: Event(label=_('Investigate'))
    events.choose_password_event = lambda i: Event(label=_('Set new password'), action=Action(i.choose_new_password))
    events.reset_password_event = lambda i: Event(label=_('Reset password'), action=Action(i.request_password_reset))
    events.login_event = lambda i: Event(label=_('Log in'), action=Action(i.log_in))
    events.resend_event = lambda i: Event(label=_('Send'), action=Action(i.send_activation_notification))
    events.log_out_event = lambda i: Event(label=_('Log out'), action=Action(i.log_out))
    
    def log_in(self):
        EmailAndPasswordSystemAccount.log_in(self.email, self.password, self.stay_logged_in)
        
    def log_out(self):
        login_session = LoginSession.for_current_session()
        login_session.log_out()

    def request_password_reset(self):
        account = EmailAndPasswordSystemAccount.by_email(self.email)
        account.request_new_password()
    
    def choose_new_password(self):
        request = NewPasswordRequest.by_secret_key(self.secret)
        request.set_new_password(self.email, self.password)

    def verify_email(self):
        request = VerifyEmailRequest.by_secret_key(self.secret)
        request.verify(self.email, self.password)
        
    def request_email_change(self):
        account = EmailAndPasswordSystemAccount.by_email(self.email)
        account.request_email_change(self.new_email)

    def register(self):
        return EmailAndPasswordSystemAccount.register(self.email, self.password)

    def send_activation_notification(self):
        account = EmailAndPasswordSystemAccount.by_email(self.email)
        account.send_activation_notification()

    def is_login_active(self):
        return EmailAndPasswordSystemAccount.is_login_active(self.email)
        
    def is_login_pending(self):
        return EmailAndPasswordSystemAccount.is_login_pending(self.email)

    def is_login_available(self):
        return EmailAndPasswordSystemAccount.is_login_available(self.email)


class RepeatPasswordField(PasswordField):
    def __init__(self, other_field, default=None, required=False, required_message=None, label=None):
        label = label or _('')
        super().__init__(default, required, required_message, label)
        self.add_validation_constraint(EqualToConstraint(other_field))
        
        
class PasswordException(DomainException): 
    """Whenever a new password is chosen, it is input by a user into two separate fields
       to guard against typing errors. PasswordException is raised to indicate that the 
       two PasswordFields do not match."""
    def as_user_message(self):
        return _('Passwords do not match')


class InvalidPasswordException(DomainException):
    """Raised to indicate that a user supplied incorrect password or username."""
    def as_user_message(self):
        return _('Invalid login credentials')


class KeyException(DomainException):
    """Raised to indicate that the secret key given is not valid."""
    def as_user_message(self):
        return _('The secret key supplied is invalid.')


class InvalidEmailException(DomainException):
    """Raised to indicate that the given email address is not valid."""
    def as_user_message(self):
        return _('The email address supplied is invalid.')


class NoSuchAccountException(DomainException):
    """Raised to indicate that the account relating to a supplied email address does not exist."""
    def as_user_message(self):
        return _('Could not find an account matching the supplied email address.')


class NotUniqueException(DomainException):
    """Raised to indicate that an email address supplied for a new registration already is in
       use on the system."""
    def as_user_message(self):
        return _('The email address supplied is not unique.')


class AccountNotActiveException(DomainException):
    """Raised to indicate that the account related to the given email address is not active yet."""
    def __init__(self, account_status):
        DomainException.__init__(self, commit=False)
        self.account_status = account_status

    def __reduce__(self):
        return (AccountNotActiveException, (self.account_status,))

    def as_user_message(self):
        return self.account_status.as_user_message()


class VerificationRequest(Requirement):
    """Some action requested by someone which needs to be verified before it can be done.

    An VerificationRequest is linked to a SystemAccount, it sends out a verification notice
    to its system_account.  This notice contains a secret key which is unique to each
    VerificationRequest. 

    The notification is sent using a method specified by the SystemAccount. 
    To complete the verification process, the recipient of the notice needs to
    complete another action which cannot be done without the secret key which was sent.

    VerificationRequests may become 'stale' if no-one ever responds to the verification
    notices sent out. Hence, they are cleared periodically.  VerificationRequests older than
    the "accounts.request_verification_timeout" configuration setting are regarded as stale.
    """

    __tablename__ = 'verificationrequest'
    __mapper_args__ = {'polymorphic_identity': 'verificationrequest'}
    id = Column(Integer, ForeignKey(Requirement.id, ondelete='CASCADE'), primary_key=True)

    salt = Column(String(10), nullable=False)
    mailer = None

    @classmethod
    def by_secret_key(cls, secret_key):
        try:
            request_id, salt = re.match('([0-9]*)k(.*)', secret_key).groups()
        except:
            raise KeyException()

        requests = Session.query(cls).filter_by(id=request_id)
        if requests.count() == 1 and requests.one().salt == salt:
            return requests.one()
        raise KeyException()

    def __init__(self, **kwargs):
        self.generate_salt()
        super().__init__(**kwargs)

    def generate_salt(self):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZqwertyuiopasdfghjklzxcvbnm0123456789'
        self.salt = ''.join([random.choice(alphabet) for x in list(range(10))])

    def send_mail(self, destination, subject_config_key, mail_config_key):
        data = self.get_data_for_substitution()
        config = ExecutionContext.get_context().config
        admin_email = config.accounts.admin_email
        subject = Template(config.get_from_string(subject_config_key)).safe_substitute(data)
        message_text = Template(config.get_from_string(mail_config_key)).safe_substitute(data)
        message = MailMessage(admin_email, [destination], subject, message_text) 
        mailer = config.accounts.mailer_class.from_context()
        try:
            mailer.send_message(message)
        except ConnectionError as e:
            message = _('Could not send registration verification email message to %s: %s.') % (self.email, str(e))
            user_message = message + _(' Please contact the site administrator and try again later.')
            logging.getLogger(__name__).error(message)
            raise DomainException(message=user_message)

    def send_notification(self):
        pass

    def get_data_for_substitution(self):
        return {'email': self.email,
                'secret_key': self.as_secret_key() }

    def as_secret_key(self):
        Session.flush()
        return '%sk%s' % (self.id, self.salt)


class NewPasswordRequest(VerificationRequest):
    """A request to pick a new passowrd for a SystemAccount."""
    __tablename__ = 'newpasswordrequest'
    __mapper_args__ = {'polymorphic_identity': 'newpasswordrequest'}
    id = Column(Integer, ForeignKey(VerificationRequest.id, ondelete='CASCADE'), primary_key=True)

    system_account_id = Column(Integer, ForeignKey('systemaccount.id'),
                               nullable=False, primary_key=True, index=True)
    system_account = relationship(SystemAccount)


    @property
    def email(self):
        return self.system_account.email
    
    def send_notification(self):
        self.send_mail(self.system_account.email, 'accounts.new_password_subject', 'accounts.new_password_email')

    def set_new_password(self, email, password):
        self.system_account.set_new_password(email, password)
        Session.delete(self)


class VerifyEmailRequest(VerificationRequest):
    """A request to activate the account for a newly created SystemAccount."""
    __tablename__ = 'verifyemailrequest'
    __mapper_args__ = {'polymorphic_identity': 'verifyemailrequest'}

    id = Column(Integer, ForeignKey(VerificationRequest.id, ondelete='CASCADE'), primary_key=True)

    email = Column(Unicode(254), nullable=False, unique=True, index=True)
    subject_config = Column(UnicodeText, nullable=False)
    email_config = Column(UnicodeText, nullable=False)

    def verify(self, email, password):
        if not self.email == email:
            raise InvalidEmailException(email)
        self.password_used_to_verify = password
        self.set_fulfilled()

    def send_notification(self):
        self.send_mail(self.email, self.subject_config, self.email_config)


class ActivateAccount(DeferredAction):
    __tablename__ = 'activateaccount'
    __mapper_args__ = {'polymorphic_identity': 'activateaccount'}

    id = Column(Integer, ForeignKey(DeferredAction.id, ondelete='CASCADE'), primary_key=True)

    system_account_id = Column(Integer, ForeignKey('systemaccount.id'), index=True)
    system_account = relationship(SystemAccount)

    def __init__(self, system_account=None, **kwargs):
        config = ExecutionContext.get_context().config
        deadline = datetime.now() + timedelta(days=config.accounts.request_verification_timeout)
        self.system_account = system_account
        super().__init__(deadline=deadline, **kwargs)

    def success_action(self):
        self.system_account.activate()

    def deadline_action(self):
        Session.flush()
        self.system_account.cancel_reservation()


class ChangeAccountEmail(DeferredAction):
    __tablename__ = 'changeaccountemail'
    __mapper_args__ = {'polymorphic_identity': 'changeaccountemail'}

    id = Column(Integer, ForeignKey(DeferredAction.id, ondelete='CASCADE'), primary_key=True)

    system_account_id = Column(Integer, ForeignKey('systemaccount.id'), index=True)
    system_account = relationship(SystemAccount)

    def __init__(self, system_account, new_email):
        requirements = [VerifyEmailRequest(email=new_email,
                                           subject_config='accounts.email_change_subject',
                                           email_config='accounts.email_change_email')]
        config = ExecutionContext.get_context().config
        deadline = datetime.now() + timedelta(days=config.accounts.request_verification_timeout)
        self.system_account = system_account
        super().__init__(requirements=requirements,
                                                 deadline=deadline)

    @property
    def verify_email_request(self):
        return self.requirements.one()

    def success_action(self):
        self.system_account.set_new_email(self.verify_email_request.email, self.verify_email_request.password_used_to_verify)

    def send_notification(self):
        self.verify_email_request.send_notification()




@session_scoped
class LoginSession(Base):
    """A @session_scoped object that keeps track of logged in access to the system.

       (See :class:`AccountManagementInterface` for logging users into and out of the system.)

       .. versionadded:: 3.1
    """
    __tablename__ = 'loginsession'

    id = Column(Integer, primary_key=True)
    discriminator = Column('row_type', String(length=40))
    __mapper_args__ = {
        'polymorphic_identity': 'loginsession',
        'polymorphic_on': discriminator
    }

    account_id = Column(Integer, ForeignKey('systemaccount.id'), index=True)
    account = relationship(SystemAccount) #: The SystemAccount currently logged on

    def is_logged_in(self, secured=False):
        """Answers whether the user is logged in.

           :keyword secured: If True, ensures the login is done via secure means (such as an encrypted connection).

           .. versionchanged:: 3.1
              Moved here from the older UserSession, and the `secured` keyword argument was added.
        """
        logged_in = self.account is not None
        if secured:
            return logged_in and self.user_session.is_secured()
        else:
            return logged_in and self.user_session.is_active()

    def set_as_logged_in(self, account, stay_logged_in):
        self.account = account
        self.user_session.set_idle_lifetime(stay_logged_in)
        self.user_session.set_last_activity_time()

    def log_out(self):
        self.account = None


class SystemAccountStatus:
    def as_user_message(self):
        return _('Unknown status')
    def is_active(self):
        return False
        
        
class AccountNotActivated(SystemAccountStatus):
    def as_user_message(self):
        return _('Please verify your account before logging in')
    
    
class AccountDisabled(SystemAccountStatus):
    def as_user_message(self):
        return _('Account is locked: too many failed attempts')
    
    
class AccountActive(SystemAccountStatus):
    def as_user_message(self):
        return _('Account is active')
    def is_active(self):
        return True


