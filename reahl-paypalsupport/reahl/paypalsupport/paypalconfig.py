# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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
""".. versionadded:: 5.2
"""

from reahl.paypalsupport.paypallibrary import PayPalJS
from reahl.component.config import Configuration

class PayPalSiteConfig(Configuration):
    filename = 'paypalsupport.config.py'
    config_key = 'paypalsupport'

    def do_injections(self, config):
        config.web.frontend_libraries.add(PayPalJS())

