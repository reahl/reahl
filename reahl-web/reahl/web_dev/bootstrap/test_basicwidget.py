# Copyright 2014-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.tofu.pytestsupport import with_fixtures

from reahl.web.bootstrap.ui import Alert, Badge, P

from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
def test_alerts(web_fixture):
    """An alert is used to display a message with a specific severity"""


    alert = Alert(web_fixture.view, 'Be careful', 'danger')

    assert alert.get_attribute('class') == 'alert alert-danger'
    assert alert.get_attribute('role') == 'alert'
    [message] = alert.children
    assert message.value == 'Be careful'


@with_fixtures(WebFixture)
def test_alert_with_widget_as_message(web_fixture):
    """An alert can also be constructed with a widget as message"""

    widget_contained_in_alert = P(web_fixture.view, text='Consider yourself warned')
    alert = Alert(web_fixture.view, widget_contained_in_alert, 'warning')

    [paragraph] = alert.children
    [message] = paragraph.children
    assert message.value == 'Consider yourself warned'


@with_fixtures(WebFixture)
def test_badges(web_fixture):
    """A badge is used inside other widgets to draw the users attention"""

    badge = Badge(web_fixture.view, 'On sale', 'info')

    assert badge.get_attribute('class') == 'badge badge-info'
    [message] = badge.children
    assert message.value == 'On sale'


@with_fixtures(WebFixture)
def test_badge_as_pill(web_fixture):
    """A badge can be made to look like a pill"""

    badge = Badge(web_fixture.view, 'On sale', 'success', pill=True)

    assert badge.get_attribute('class') == 'badge badge-pill badge-success'
