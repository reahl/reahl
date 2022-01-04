# Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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


class PayPalJS(Library):
    """
    """
    def __init__(self):
        super().__init__('reahl-paypal')
        self.egg_name = 'reahl-paypalsupport'
        self.shipped_in_directory = 'reahl/paypalsupport'
        self.files = [
            'reahl-paypalbuttonspanel.js'
        ]

    def footer_only_material(self, rendered_page):
        result = ''
        for cdn_link in ['https://www.paypal.com/sdk/js?client-id=test&currency=USD']:
            result += '\n<script type="text/javascript" src="%s"></script>' % cdn_link
        return result + super().footer_only_material(rendered_page)
