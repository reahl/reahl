# Copyright 2009, 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from reahl.component.config import Configuration, ConfigSetting


class MailConfig(Configuration):
    filename = 'mailutil.config.py'
    config_key = 'mail'
    smtp_host = ConfigSetting(default='localhost', description='The hostname used for sending SMTP email')
    smtp_port = ConfigSetting(default=25, description='The port used for sending SMTP email')

