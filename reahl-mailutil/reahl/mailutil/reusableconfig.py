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


from reahl.component.config import Configuration, ConfigSetting


class MailConfig(Configuration):
    filename = 'mailutil.config.py'
    config_key = 'mail'
    smtp_host = ConfigSetting(default='localhost', description='The hostname used for sending SMTP email')
    smtp_port = ConfigSetting(default=8025, description='The port used for sending SMTP email', dangerous=True)
    smtp_user = ConfigSetting(default=None, description='The user name to connect to SMTP server')
    smtp_password = ConfigSetting(default=None, description='The password for the user to connect to the SMTP server')
    smtp_use_initial_encrypted_connection = ConfigSetting(default=False, description='If True, connect to the server using a secure connection (use with smtps)')
    smtp_upgrade_initial_connection_to_encrypted = ConfigSetting(default=False, description='If True, connects to the server unencrypted, but then upgrade to a secure connection using STARTTLS (use with submission or smtp)')
    smtp_keyfile = ConfigSetting(default=None, description='Keyfile to use for identifying the local end of the connection')
    smtp_certfile = ConfigSetting(default=None, description='Certfile to use for identifying the local end of the connection')
