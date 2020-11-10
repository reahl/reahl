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

"""Utility classes for sending simple email messages.

Run 'reahl componentinfo reahl-mailutil' for configuration information.

""" 


import re
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from reahl.component.context import ExecutionContext
from reahl.mailutil.rst import RestructuredText


class InvalidEmailAddressException(Exception):
    pass
    

class MailMessage:
    """Represents an email message, with one part containing plain text (presumed to be ReST), and the other
       an HTML representation of the same message.
       
       :param from_address: The "from" email address
       :param to_addresses: A list of "to" email addresses
       :param subject: The subject line
       :param rst_message: A message, expressed as a string containing ReStructured Text
       :keyword charset: The charset of `rst_message`
    """
    EMAIL_RE = re.compile("^[^\s]+@[^\s]+\.[^\s]{2,4}$")
    def __init__(self, from_address, to_addresses, subject, rst_message, charset='utf-8'):
            self.validate_email_addresses(to_addresses+[from_address])
            self.from_address = from_address
            self.to_addresses = to_addresses
            self.subject = subject
            self.rst_text = rst_message
            self.message_root = MIMEMultipart('related')
            self.message_root['Subject'] = subject
            self.message_root['From'] = from_address
            self.message_root['To'] = ", ".join(to_addresses)
            self.message_root.preamble = 'This is a multi-part message in MIME format.'

            # Encapsulate the plain and HTML versions of the message body in an
            # 'alternative' part, so message agents can decide which they want to display.
            self.message_alternative = MIMEMultipart('alternative')
            self.message_root.attach(self.message_alternative)

            message_text = MIMEText(rst_message.encode(charset), 'plain', charset)
            self.message_alternative.attach(message_text)

            rst = RestructuredText(rst_message)
            message_text = MIMEText(rst.as_HTML_fragment().encode(charset), 'html', charset)
            self.message_alternative.attach(message_text)

    def as_string(self):
        """Returns the message as ASCII-encoded string for sending."""
        return self.message_root.as_string()

    def validate_email_addresses(self, list_of_addresses):
        for address in list_of_addresses:
            if self.EMAIL_RE.search(address) is None:
                raise InvalidEmailAddressException(address)


class Mailer:
    """A proxy for a remote SMTP server.
    
       :keyword smtp_host: The host to connect to.
       :keyword smtp_port: The port to connect to.
       :keyword smtp_user: The username to use (if specified) for authentication.
       :keyword smtp_password: The password to authenticate with the smtp host.
       :keyword smtp_use_initial_encrypted_connection: If True, connect to the server using a secure connection (use with smtps)
       :keyword smtp_upgrade_initial_connection_to_encrypted: If True, connects to the server unencrypted, but then upgrade to a secure connection using STARTTLS (use with submission or smtp)
       :keyword smtp_keyfile: Keyfile to use for identifying the local end of the connection.
       :keyword smtp_certfile: Certfile to use for identifying the local end of the connection.
    """
    @classmethod
    def from_context(cls):
        """Returns a Mailer, using the system configuration."""
        config = ExecutionContext.get_context().config
        smtp_host = config.mail.smtp_host
        smtp_port = config.mail.smtp_port
        smtp_user = config.mail.smtp_user
        smtp_password = config.mail.smtp_password
        smtp_use_initial_encrypted_connection = config.mail.smtp_use_initial_encrypted_connection
        smtp_upgrade_initial_connection_to_encrypted = config.mail.smtp_upgrade_initial_connection_to_encrypted
        smtp_keyfile = config.mail.smtp_keyfile
        smtp_certfile = config.mail.smtp_certfile
        return cls(smtp_host=smtp_host, smtp_port=smtp_port, smtp_user=smtp_user, smtp_password=smtp_password,
                   smtp_use_initial_encrypted_connection=smtp_use_initial_encrypted_connection,
                   smtp_upgrade_initial_connection_to_encrypted=smtp_upgrade_initial_connection_to_encrypted,
                   smtp_keyfile=smtp_keyfile, smtp_certfile=smtp_certfile)


    def __init__(self, smtp_host='localhost', smtp_port=8025, smtp_user=None, smtp_password=None,
                 smtp_use_initial_encrypted_connection=False, 
                 smtp_upgrade_initial_connection_to_encrypted=False,
                 smtp_keyfile=None, smtp_certfile=None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_use_initial_encrypted_connection = smtp_use_initial_encrypted_connection
        self.smtp_upgrade_initial_connection_to_encrypted = smtp_upgrade_initial_connection_to_encrypted
        self.smtp_keyfile = smtp_keyfile
        self.smtp_certfile = smtp_certfile

        self.smtp_server = None
        self.connected = False

    def connect(self):
        if self.smtp_use_initial_encrypted_connection:
            self.smtp_server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port,
                                                keyfile=self.smtp_keyfile, certfile=self.smtp_certfile)
        else:
            self.smtp_server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.smtp_upgrade_initial_connection_to_encrypted:
                self.smtp_server.ehlo()
                self.smtp_server.starttls(keyfile=self.smtp_keyfile, certfile=self.smtp_certfile)
                self.smtp_server.ehlo()
        if self.smtp_user:
            self.smtp_server.login(self.smtp_user, self.smtp_password)
        self.connected = True
        logging.debug('connected to server')

    def send_message(self, message):
        """Sends `message` (a :class:`MailMessage`) to the connected SMTP server."""
        try:
            self.connect()
            self.smtp_server.sendmail(message.from_address, message.to_addresses, message.as_string())
        finally:
            self.disconnect()

    def disconnect(self):
        if self.connected:
            try:
                self.smtp_server.quit()
            except smtplib.SMTPServerDisconnected as e:
                pass

        self.connected = False
        self.smtp_server = None


