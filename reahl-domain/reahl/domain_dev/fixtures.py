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




from reahl.tofu import Fixture, set_up, uses
from reahl.stubble import stubclass, exempt
from reahl.mailutil.mail import Mailer

from reahl.sqlalchemysupport import Session
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.domain.partymodel import Party
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount, AccountManagementInterface
from reahl.domain.systemaccountmodel import SystemAccountConfig
from reahl.webdeclarative.webdeclarative import UserSession, PersistedException, PersistedFile, UserInput
from reahl.web.egg import WebConfig
from reahl.web.fw import UserInterface

from reahl.dev.fixtures import ReahlSystemFixture


@stubclass(Mailer)
class MailerStub:
    instance = None
    
    @classmethod 
    def from_context(cls):
        if not cls.instance:
            cls.instance = cls()
        return cls.instance

    def __init__(self, smtp_host='localhost', smtp_port=8025, smtp_user=None, smtp_password=None):
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


@uses(reahl_system_fixture=ReahlSystemFixture, sql_alchemy_fixture=SqlAlchemyFixture)
class PartyAccountFixture(Fixture):

    @set_up
    def add_system_account_config(self):
        self.reahl_system_fixture.config.accounts = self.system_account_config
        self.reahl_system_fixture.context.session = self.session

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
        user_session = UserSession()
        Session.add(user_session)
        Session.flush()
        return user_session

