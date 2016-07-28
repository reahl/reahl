# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
#-*- encoding: utf-8 -*-
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

from __future__ import print_function, unicode_literals, absolute_import, division

import six

from reahl.tofu import vassert, scenario, expected, test

from reahl.web_dev.fixtures import WebFixture

from reahl.web.bootstrap.ui import Alert



@test(WebFixture)
def alerts(fixture):
    """An alert is used to display a message with a specific severity"""

    alert = Alert(fixture.view, 'Be careful', 'danger')

    vassert( alert.get_attribute('class') == 'alert alert-danger' )
    vassert( alert.get_attribute('role') == 'alert' )
    [message] = alert.children
    vassert( message.value == 'Be careful' )
