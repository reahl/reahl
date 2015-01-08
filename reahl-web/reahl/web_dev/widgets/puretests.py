# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import test
from reahl.tofu import vassert

from reahl.webdev.tools import XPath

from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture

from reahl.web.ui import Panel, P

from reahl.web.pure import PureGridLayout

#    def add_unit(self, widget, default=None, sm=None, md=None, lg=None, xl=None):


@test(WebFixture)
def grid_layout_basics(fixture):
    """A PureGridLayout turns its Widget into a Pure Grid to which children can be added as Pure Units."""

    widget = Panel(fixture.view, layout=PureGridLayout())

    widget.layout.add_unit(P(fixture.view))

    widget_tester = WidgetTester(widget)
    actual = widget_tester.render_html()
    
    vassert( actual == '<div class="pure-g"><div class="pure-u"><p></p></div></div>' )


@test(WebFixture)
def grid_layout_fractions(fixture):
    """When adding a unit, you can specify the default size (a fraction) of the unit, and sizes for different media sizes."""

    widget = Panel(fixture.view, layout=PureGridLayout())

    widget.layout.add_unit(P(fixture.view), default='1/2', sm='1/3', md='2/3', lg='1/4', xl='3/4')

    widget_tester = WidgetTester(widget)
    actual = widget_tester.render_html()
    
    vassert( actual == '<div class="pure-g"><div class="pure-u-1-2 pure-u-lg-1-4 pure-u-md-2-3 pure-u-sm-1-3 pure-u-xl-3-4"><p></p></div></div>' )




