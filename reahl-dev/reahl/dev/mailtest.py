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

"""Classes for faking sending and receiving of mail
================================================

Copyright (C) 2006 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)

"""

import asyncore
import logging
from smtpd import DebuggingServer, SMTPServer
from threading import Thread
import email

from reahl.dev.devshell import WorkspaceCommand

#------------------------------------------------[ utilities ]


class EchoSMTPServer(DebuggingServer):
    def __init__(self):
        init_kwargs = dict(decode_data=True)
        DebuggingServer.__init__(self, ('localhost', 8025), (None, 0), **init_kwargs)
 
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        #Parse the message into an email.Message instance
        logging.debug("Recieved Message")
        m = email.message_from_string(data)
        logging.debug("Parsed Message")

        self.current_id = m['Message-Id']
        self.process_simple_message(m, mailfrom, rcpttos)

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
        server = EchoSMTPServer()
        print("Running Echo SMTP Server on port 8025, type [ctrl-c] to exit.")
        try:
            asyncore.loop()
        except KeyboardInterrupt:
            pass
        

class FakeSMTPServer(EchoSMTPServer):

    def __init__(self, call_back_function=None):
        EchoSMTPServer.__init__(self)
        self.call_back_function = call_back_function

    #A place to store the current ID of the message that we are processing.
    current_id = 0

    def handle_close(self):
        logging.debug("close called")

    def process_simple_message(self, message, mailfrom, rcpttos):
        logging.debug(self.message_as_text(message))

        if self.call_back_function:
            self.call_back_function(message, mailfrom, rcpttos)


class MailTester:

    def __init__(self, call_back_function=None):
        self.call_back_function = call_back_function
        self.running = False

    def main_loop(self):
        while self.running:
            logging.debug("mainloop...")
            asyncore.loop(timeout=1, count=1)
        self.fake_server.close()

    def start(self):
        self.fake_server = FakeSMTPServer(self.call_back_function)
        self.thread = Thread(target=self.main_loop)
        self.running = True
        self.thread.start()

    def stop(self):
        logging.debug("stop called")
        self.running = False
        self.thread.join()



