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
"""
Support for including `plotly.py <https://github.com/plotly/plotly.py/>`_ figures on a web page.
"""


import json

from reahl.web.ui import HTMLWidget, Div, LiteralHTML
from reahl.web.libraries import PlotlyJS


class RefreshedJS(Div):
    def __init__(self, chart):
        super().__init__(chart.view, css_id='%s-data-container' % chart.css_id)
        self.chart = chart

    def get_js(self, context=None):
        options = { 'chart_id': self.chart.css_id,
                    'json': json.loads(self.chart.figure.to_json())}
        return super().get_js(context=context) + ['$(%s).plotlychartdata(%s);' % (self.jquery_selector,
                                                                                  json.dumps(options))]

class ChartContents(Div):
    def __init__(self, chart):
        super().__init__(chart.view, css_id='%s-data' % chart.css_id)
        self.div = self.add_child(RefreshedJS(chart))
        self.enable_refresh()


class Chart(HTMLWidget):
    """A Widget displays a plotly Figure.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param figure: A fully constructed plotly Figure.
    :param css_id: A unique id for this Chart
    :keyword read_check: (See :class:`reahl.web.fw.Widget`)
    :keyword write_check: (See :class:`reahl.web.fw.Widget`)

    """
    def __init__(self, view, figure, css_id, read_check=None, write_check=None):
        super().__init__(view, read_check=read_check, write_check=write_check)
        self.figure = figure
        containing_div = self.add_child(Div(view, css_id=css_id))
        containing_div.append_class('reahl-plotlychart')
        self.set_html_representation(containing_div)
        self.enable_refresh()
        containing_div.add_child(LiteralHTML(view, PlotlyJS.get_instance().inline_material()))
        self.contents = containing_div.add_child(ChartContents(self)) #: The contents of the graph. You can use this as
                                                                      #: refresh_widget on an Input to refresh only the
                                                                      #: contents of the Chart, and not the entire Chart.

    def get_js(self, context=None):
        options = {'json': json.loads(self.figure.to_json())}
        return super().get_js(context=context) + ['$(%s).plotlychart(%s);' % (self.html_representation.jquery_selector,
                                                                              json.dumps(options))]
