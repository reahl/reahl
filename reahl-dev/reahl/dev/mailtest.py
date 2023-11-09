# Copyright 2013-2023 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Classes for faking sending and receiving of mail
================================================

Copyright (C) 2006 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)

"""

import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink
import logging
import email

from reahl.dev.devshell import WorkspaceCommand


class EchoSMTPHandler(Sink):
    async def handle_DATA(self, server, session, envelope):

        #Parse the message into an email.Message instance
        logging.debug("Recieved Message")
        m = email.message_from_string(envelope.content.decode('utf8'))
        logging.debug("Parsed Message")

        self.current_id = m['Message-Id']
        self.process_simple_message(m, envelope.mail_from, envelope.rcpt_tos)
        return '250 Message accepted for delivery'

    def process_simple_message(self, message, mailfrom, rcpttos):
        print((self.message_as_text(message)))

    def message_as_text(self, message):
        text = "Processing Message: %s\n" % self.current_id
        text += "   From:%s \n" % message['From']
        text += "   To:%s \n" % message['To']
        text += "   Subject:%s \n" % message['Subject']
        if not message.is_multipart():
            text += "   Body:%s\n " % message.get_payload(decode=1)
        else:
            text += "   Body:\n"
            for part in message.walk():
                text += '%s \n' % part.get_payload(decode=1)
        return text


class ServeSMTP(WorkspaceCommand):
    """Runs an SMTP server on port 8025 for testing."""
    keyword = 'servesmtp'
    def execute(self, args):

        loop = asyncio.get_event_loop()
        controller = Controller(EchoSMTPHandler(), port=8025)

        controller.start()
        print("Running Echo SMTP Server on port 8025, type [ctrl-c] to exit.")
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            controller.stop()
        

class FakeSMTPServer(EchoSMTPHandler):

    def __init__(self, call_back_function=None):
        super().__init__()
        self.call_back_function = call_back_function

    def process_simple_message(self, message, mailfrom, rcpttos):
        logging.debug(self.message_as_text(message))

        if self.call_back_function:
            self.call_back_function(message, mailfrom, rcpttos)


class MailTester:

    def __init__(self, call_back_function=None):
        self.call_back_function = call_back_function
        self.loop = asyncio.get_event_loop()

    async def main_loop(self):
        fake_server = FakeSMTPServer(self.call_back_function)
        self.controller = Controller(fake_server, port=8025)
        self.controller.start()
        logging.debug("mainloop...")

    def start(self):
        asyncio.run(self.main_loop())

    def stop(self):
        logging.debug("stop called")
        self.controller.stop()



