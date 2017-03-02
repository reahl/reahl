# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import os

from reahl.tofu import Fixture, set_up
from reahl.stubble import stubclass, exempt
from reahl.mailutil.mail import Mailer

from reahl.sqlalchemysupport import Session
# noinspection PyUnresolvedReferences
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyTestMixin, sql_alchemy_fixture
from reahl.domain.partymodel import Party
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount, AccountManagementInterface
from reahl.domain.systemaccountmodel import SystemAccountConfig
from reahl.webdeclarative.webdeclarative import UserSession, PersistedException, PersistedFile, UserInput
from reahl.web.egg import WebConfig
from reahl.web.fw import UserInterface


@stubclass(Mailer)
class MailerStub(object):
    instance = None
    
    @classmethod 
    def from_context(cls):
        if not cls.instance:
            cls.instance = cls()
        return cls.instance

    def __init__(self, smtpHost='localhost', smtpPort=8025, smtpUser=None, smtpPassword=None):
        self.reset()
        
    def send_message(self, message):
        self.mail_sent = True
        self.mail_recipients = message.to_addresses
        self.mail_sender = message.from_address
        self.mail_subject = message.subject
        self.mail_message = message.rst_text
        
    @exempt
    def reset(self):
        self.mail_sent = False
        self.mail_recipients = None
        self.mail_subject = None
        self.mail_message = None
        self.mail_sender = None


class BasicModelZooMixin(SqlAlchemyTestMixin):
    def new_accounts(self):
        accounts = SystemAccountConfig()
        accounts.admin_email = 'pietiskoning@home.org'
        accounts.mailer_class = MailerStub
        return accounts
    
    def new_webconfig(self):
        web = WebConfig()
        web.site_root = UserInterface
        web.static_root = os.path.join(os.getcwd(), 'static')
        web.session_class = UserSession
        web.persisted_exception_class = PersistedException
        web.persisted_file_class = PersistedFile
        web.persisted_userinput_class = UserInput
        return web

    def new_config(self, reahlsystem=None, accounts=None, web=None):
        config = super(BasicModelZooMixin, self).new_config(reahlsystem=reahlsystem)
        config.web = web or self.new_webconfig()
        config.accounts = accounts or self.accounts
        return config

    def new_session(self, system_account=None):
        return UserSession()

    
class PartyModelZooMixin(BasicModelZooMixin):
    def new_system_account(self, party=None, email='johndoe@home.org', activated=True):
        password = 'topsecret'
        system_account = EmailAndPasswordSystemAccount(owner=party or self.party, email=email)
        system_account.set_new_password(email, password)
        system_account.password = password  # The unencrypted version for use in tests
        if activated:
            system_account.activate()
        Session.add(system_account)
        Session.flush()
        return system_account

    def new_party(self):
        party = Party()
        Session.add(party)
        Session.flush()
        return party

    def new_mailer(self):
        return MailerStub.from_context()


class DemoSetup(Fixture, PartyModelZooMixin):
    commit = True
    def set_up(self):
        super(DemoSetup, self).set_up()
        self.party
        self.system_account
        self.system_control.commit()


class DeclarativeImplementationFixture(Fixture):
    def new_session(self, system_account=None):
        return UserSession()


class PartyAccountFixture(Fixture):
    def __init__(self, sql_alchemy_fixture):
        super(PartyAccountFixture, self).__init__()
        self.sql_alchemy_fixture = sql_alchemy_fixture

    @property
    def context(self):
        return self.sql_alchemy_fixture.context

    @set_up
    def add_system_account_config(self):
        self.sql_alchemy_fixture.config.accounts = self.system_account_config
        self.sql_alchemy_fixture.context.set_session(self.session)

    def new_system_account_config(self):
        accounts = SystemAccountConfig()
        accounts.admin_email = 'pietiskoning@home.org'
        accounts.mailer_class = MailerStub
        return accounts

    def new_system_account(self, party=None, email='johndoe@home.org', activated=True):
        password = 'topsecret'
        system_account = EmailAndPasswordSystemAccount(owner=party or self.party, email=email)
        system_account.set_new_password(email, password)
        system_account.password = password  # The unencrypted version for use in tests
        if activated:
            system_account.activate()
        Session.add(system_account)
        Session.flush()
        return system_account

    def new_party(self):
        party = Party()
        Session.add(party)
        Session.flush()
        return party

    def new_mailer(self):
        return MailerStub.from_context()

    def new_account_management_interface(self, system_account=None):
        system_account = system_account or self.system_account
        account_management_interface = AccountManagementInterface()
        account_management_interface.password = system_account.password
        account_management_interface.email = system_account.email
        Session.add(account_management_interface)
        Session.flush()
        return account_management_interface

    def new_session(self, system_account=None):
        return UserSession()

party_account_fixture = PartyAccountFixture.as_pytest_fixture()
