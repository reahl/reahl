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

from reahl.tofu.pytest_support import with_fixtures

from reahl.web.bootstrap.ui import Alert

from reahl.web_dev.fixtures import WebFixture2


@with_fixtures(WebFixture2)
def test_alerts(web_fixture):
    """An alert is used to display a message with a specific severity"""

    with web_fixture.context:
        alert = Alert(web_fixture.view, 'Be careful', 'danger')

        assert alert.get_attribute('class') == 'alert alert-danger'
        assert alert.get_attribute('role') == 'alert'
        [message] = alert.children
        assert message.value == 'Be careful'
