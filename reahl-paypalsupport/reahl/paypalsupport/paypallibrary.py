# Copyright 2021, 2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from reahl.web.libraries import Library
from reahl.component.exceptions import ProgrammerError

class PayPalJS(Library):
    """Reahl javascript code for integrating with PayPal as well as a CDN link to PayPal's own js library
    """
    def __init__(self):
        super().__init__('reahl-paypal')
        self.egg_name = 'reahl-paypalsupport'
        self.shipped_in_package = 'reahl.paypalsupport'
        self.files = [
            'reahl-paypalbuttonspanel.js'
        ]

    def inline_material(self, credentials, currency):
        paypal_script_cdn = ''
        for cdn_link in ['https://www.paypal.com/sdk/js?client-id=%s&currency=%s' % (credentials.client_id, currency)]:
            paypal_script_cdn += '\n<script type="text/javascript" src="%s"></script>' % cdn_link

        return paypal_script_cdn