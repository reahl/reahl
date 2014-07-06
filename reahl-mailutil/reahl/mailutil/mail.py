# Copyright 2009, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Utility classes for sending simple email messages.""" 


from __future__ import unicode_literals
from __future__ import print_function
import re
import smtplib
import logging
import email.MIMEMultipart
import email.MIMEText

from reahl.component.context import ExecutionContext
from reahl.mailutil.rst import RestructuredText


class InvalidEmailAddressException(Exception):
    pass
    

class MailMessage(object):
    """Represents an email message, with one part containing plain text (presumed to be ReST), and the other
       an HTML representation of the same message.
       
       :param from_address: The "from" email address
       :param to_addresses: A list of "to" email addresses
       :param subject: The subject line
       :param rst_message: A message, expressed as a string containing ReStructured Text
       :param charset: The charset of `rst_message`
    """
    EMAIL_RE = re.compile("^[^\s]+@[^\s]+\.[^\s]{2,4}$")
    def __init__(self, from_address, to_addresses, subject, rst_message, charset='utf-8'):
            self.validate_email_addresses(to_addresses+[from_address])
            self.from_address = from_address
            self.to_addresses = to_addresses
            self.subject = subject
            self.rst_text = rst_message
            self.message_root = email.MIMEMultipart.MIMEMultipart('related')
            self.message_root['Subject'] = subject
            self.message_root['From'] = from_address
            self.message_root['To'] = ", ".join(to_addresses)
            self.message_root.preamble = 'This is a multi-part message in MIME format.'

            # Encapsulate the plain and HTML versions of the message body in an
            # 'alternative' part, so message agents can decide which they want to display.
            self.message_alternative = email.MIMEMultipart.MIMEMultipart('alternative')
            self.message_root.attach(self.message_alternative)

            message_text = email.MIMEText.MIMEText(rst_message.encode(charset), 'plain', charset)
            self.message_alternative.attach(message_text)

            rst = RestructuredText(rst_message)
            message_text = email.MIMEText.MIMEText(rst.as_HTML_fragment().encode(charset), 'html', charset)
            self.message_alternative.attach(message_text)

    def as_string(self):
        """Returns the message as ASCII-encoded string for sending."""
        return self.message_root.as_string()

    def validate_email_addresses(self, list_of_addresses):
        result = []
        for address in list_of_addresses:
            if self.EMAIL_RE.search(address) == None:
                raise InvalidEmailAddressException(address)


class Mailer(object):
    """A proxy for a remote SMTP server.
    
       :param smtp_host: The host to connect to.
       :param smtp_port: The port to connect to.
       :param smtp_user: The username to use (if specified) for authentication.
       :param smtp_password: The password to authenticate with the smtp host
    """
    @classmethod 
    def from_context(cls):
        """Returns a Mailer, using the host and port of the system configuration."""
        config = ExecutionContext.get_context().config
        smtp_host = config.mail.smtp_host
        smtp_port = config.mail.smtp_port
        
        return cls(smtp_host=smtp_host, smtp_port=smtp_port)

    def __init__(self, smtp_host='localhost', smtp_port=8025, smtp_user=None, smtp_password=None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_server = None
        self.connected = False
     
    def connect(self):    
        self.smtp_server = smtplib.SMTP(self.smtp_host, self.smtp_port)
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

