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


from reahl.tofu import Fixture
from reahl.tofu import expected
from reahl.tofu.pytestsupport import with_fixtures

from reahl.mailutil.mail import Mailer, MailMessage, InvalidEmailAddressException
from reahl.dev.mailtest import MailTester


# noinspection PyAttributeOutsideInit
class MailerFixture(Fixture):
    def set_up(self):
        super().set_up()

        self.valid_email_addresses = ['someone@home.co.za', 'something@somewhere.com', 'j@j.ca']
        self.invalid_email_addresses = ['somethingWithoutTheAt', '@somethingThatBeginsWithTheAT',
                                        'somethingThatEndsWithTheAt@', '@', None]

        self.mail_checker_started = False
        self.mail_recipients = None
        self.mail_message = None

        self.mailer = Mailer()

    def start_mail_checker(self):
        self.mail_tester = MailTester(self.mail_checker)
        self.mail_tester.start()
        self.mail_checker_started = True

    def mail_checker(self, email_message, mailfrom, rcpttos):
        self.mail_sender = email_message['From']
        self.mail_recipients = email_message['To'].split(', ')
        self.mail_subject = email_message['Subject']
        self.mail_message = email_message.get_payload()[0].get_payload()[0].get_payload()

    def tear_down(self):
        super().tear_down()
        if self.mail_checker_started:
            self.mail_tester.stop()


@with_fixtures(MailerFixture)
def test_validation(mailer_fixture):
    fixture = mailer_fixture
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


@with_fixtures(MailerFixture)
def test_sending(mailer_fixture):
    fixture = mailer_fixture

    fixture.start_mail_checker()

    mail_message = MailMessage(fixture.valid_email_addresses[0],
                               fixture.valid_email_addresses,
                               'Hi',
                               'Some Message',
                               charset='ascii')
    fixture.mailer.send_message(mail_message)
    assert fixture.mail_sender == fixture.valid_email_addresses[0]
    assert fixture.mail_recipients == fixture.valid_email_addresses
    assert fixture.mail_subject == 'Hi'
    assert fixture.mail_message == 'Some Message'
