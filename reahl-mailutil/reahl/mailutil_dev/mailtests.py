# Copyright 2009, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Tests for the reahl.dev.mailtest module
===========================================

Copyright (C) 2006 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)

""" 

from __future__ import unicode_literals
from __future__ import print_function

from reahl.tofu import Fixture, test
from reahl.tofu import expected, vassert

from reahl.mailutil.mail import Mailer, MailMessage, InvalidEmailAddressException
from reahl.dev.mailtest import MailTester

class EmailAddressFixture(Fixture):
    def set_up(self):
        self.valid_email_addresses = ['someone@home.co.za', 'something@somewhere.com', 'j@j.ca']
        self.invalid_email_addresses = ['somethingWithoutTheAt', '@somethingThatBeginsWithTheAT',
                                      'somethingThatEndsWithTheAt@', '@' ,None]


class MailerFixture(EmailAddressFixture):
    def set_up(self):
        super(MailerFixture, self).set_up()
        
        self.mail_checker_started = False
        self.mail_recipients = None
        self.mail_message = None
        
        self.mailer = Mailer()
        
    def start_mail_checker(self):
        self.mail_tester = MailTester(self.mail_checker)
        self.mail_tester.start()
        self.mail_checker_started = True

    def mail_checker(self, email_message):
        self.mail_sender = email_message['From']
        self.mail_recipients = email_message['To'].split(', ')
        self.mail_subject = email_message['Subject']
        self.mail_message = email_message.get_payload()[0].get_payload()[0].get_payload()
        
    def tear_down(self):
        super(MailerFixture, self).tear_down()
        if self.mail_checker_started:
            self.mail_tester.stop()
 


@test(MailerFixture)
def validation(fixture):
   
    with expected(InvalidEmailAddressException):
        MailMessage(fixture.invalid_email_addresses[0],
                   fixture.valid_email_addresses, 
                   'Hi', 
                   'Some Message')
    
    with expected(InvalidEmailAddressException):
        MailMessage(fixture.valid_email_addresses[0],
                   fixture.invalid_email_addresses, 
                   'Hi', 
                   'Some Message')
    

@test(MailerFixture)
def sending(fixture):

    fixture.start_mail_checker()

    mail_message = MailMessage(fixture.valid_email_addresses[0],
                               fixture.valid_email_addresses, 
                               'Hi', 
                               'Some Message', 
                               charset='ascii')
    fixture.mailer.send_message(mail_message)
    vassert( fixture.mail_sender == fixture.valid_email_addresses[0] )
    vassert( fixture.mail_recipients == fixture.valid_email_addresses )
    vassert( fixture.mail_subject == 'Hi' )
    vassert( fixture.mail_message == 'Some Message' )
    
