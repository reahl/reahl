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



from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import Fixture
from reahl.stubble import stubclass, exempt
from reahl.mailutil.mail import Mailer

from reahl.sqlalchemysupport import Session
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyTestMixin
from reahl.partymodel import Party
from reahl.systemaccountmodel import EmailAndPasswordSystemAccount
from reahl.systemaccountmodel import SystemAccountConfig
from reahl.systemaccountmodel import UserSession

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
    
    def new_config(self, reahlsystem=None, accounts=None):
        config = super(BasicModelZooMixin, self).new_config(reahlsystem=reahlsystem)
        config.accounts = accounts or self.accounts
        return config

    def new_session(self, system_account=None):
        return UserSession()

    
class PartyModelZooMixin(BasicModelZooMixin):
    def new_system_account(self, party=None, email='johndoe@home.org', activated=True):
        password = 'bobbejaan'
        system_account = EmailAndPasswordSystemAccount(party=party, email=email)
        system_account.set_new_password(email, password)
        system_account.password = password # The unencrypted version for use in tests
        if activated:
            system_account.activate()
        Session.flush()
        return system_account

    def new_party(self):
        return Party()

    def new_mailer(self):
        return MailerStub.from_context()


class DemoSetup(Fixture, PartyModelZooMixin):
    commit = True
    def set_up(self):
        super(DemoSetup, self).set_up()
        self.party
        self.system_account
        self.system_control.commit()
