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


from reahl.tofu import test, scenario
from reahl.tofu import vassert

from reahl.web.bootstrap.ui import Table, TableLayout
from reahl.web_dev.fixtures import WebFixture




class LayoutScenarios(WebFixture):
    @scenario
    def header_inverse(self):
        self.layout_kwargs = dict(inverse=True)
        self.expected_css_class = 'table-inverse'

    @scenario
    def border(self):
        self.layout_kwargs = dict(border=True)
        self.expected_css_class = 'table-bordered'

    @scenario
    def striped_rows(self):
        self.layout_kwargs = dict(striped=True)
        self.expected_css_class = 'table-striped'

    @scenario
    def hovered_rows(self):
        self.layout_kwargs = dict(highlight_hovered=True)
        self.expected_css_class = 'table-hover'

    @scenario
    def compacted_cells(self):
        self.layout_kwargs = dict(compact=True)
        self.expected_css_class = 'table-sm'

    @scenario
    def transposed(self):
        self.layout_kwargs = dict(transposed=True)
        self.expected_css_class = 'table-reflow'

    @scenario
    def transposed(self):
        self.layout_kwargs = dict(responsive=True)
        self.expected_css_class = 'table-responsive'


@test(LayoutScenarios)
def table_layout_options(fixture):
    """TableLayout uses Bootstrap to implement many table layout options."""

    for switched_on in [True, False]:
        layout = TableLayout(**fixture.layout_kwargs)
        Table(fixture.view).use_layout(layout)
        vassert( layout.widget.get_attribute('class') == 'table %s' % fixture.expected_css_class )


