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

from sqlalchemy import Column, String, Integer

from reahl.tofu import scenario, Fixture, uses, expected
from reahl.tofu.pytestsupport import with_fixtures
from reahl.browsertools.browsertools import XPath, Browser
from reahl.web_dev.fixtures import WebFixture
from reahl.web.ui import Div, Form, FormLayout, SelectInput, exposed, ChoiceField, Choice
from reahl.component.modelinterface import IntegerField
from reahl.web.plotly.charts import Chart

import plotly.graph_objects as go

@with_fixtures(WebFixture)
def test_plotly_basics(web_fixture):
    """How to add a Chart widget to a page."""

    fixture = web_fixture

    fig = go.Figure()
    class ChartPanel(Div):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(Chart(view, fig))

    fixture = web_fixture

    wsgi_app = web_fixture.new_wsgi_app(child_factory=ChartPanel.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # The Chart appears
    chart = XPath.div().including_class('plotly-graph-div js-plotly-plot')
    assert browser.is_element_present(chart)


@with_fixtures(WebFixture)
def test_javascript_only_included_once(web_fixture):
    """If there are more than one Chart on the page, the plotly.js src should only be included once for the whole page."""
    fixture = web_fixture

    class ChartPanel(Div):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(Chart(view, go.Figure()))
            self.add_child(Chart(view, go.Figure()))

    fixture = web_fixture

    wsgi_app = web_fixture.new_wsgi_app(child_factory=ChartPanel.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    plotly_js_src = XPath('//script[contains(@src,"plotly")]')
    assert browser.get_xpath_count(plotly_js_src) == 1
    plotly_js_src_in_head = XPath('//head/script[contains(@src,"plotly")]')
    assert browser.get_xpath_count(plotly_js_src_in_head) == 1


@with_fixtures(WebFixture)
def test_no_javascript_when_no_chart_on_page(web_fixture):
    """When there aren't any Charts on the page, the plotly.js src should not be present."""

    fixture = web_fixture

    wsgi_app = web_fixture.new_wsgi_app(child_factory=Div.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    plotly_js = XPath('//script[contains(@src,"plotly")]')
    assert browser.get_xpath_count(plotly_js) == 0


@with_fixtures(WebFixture)
def test_adding_chart_with_ajax(web_fixture):
    """ """

    fixture = web_fixture

    class MyForm(Form):
        def __init__(self, view):
            self.choice = 1
            super().__init__(view, 'my_form')

            self.enable_refresh()

            self.use_layout(FormLayout())
            self.layout.add_input(SelectInput(self, self.fields.choice, refresh_widget=self))

            if self.choice == 2:
                self.add_child(Chart(view, go.Figure()))

        @exposed
        def fields(self, fields):
            fields.choice = ChoiceField([Choice(1, IntegerField(label='Hide chart')),
                                         Choice(2, IntegerField(label='Show chart'))],
                                        label='Choice')


    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # import pdb;pdb.set_trace()
    # fixture.reahl_server.serve_until(lambda: False)

    #Case: no chart
    chart = XPath.div().including_class('plotly-graph-div js-plotly-plot')
    plotly_js = XPath('//script[contains(@src,"plotly")]')
    assert not browser.is_element_present(chart)
    assert browser.get_xpath_count(plotly_js) == 0

    select_input = XPath.select_labelled('Choice')
    browser.select(select_input, 'Show chart')


    #Case: chart appears
    assert browser.is_element_present(chart)
    assert browser.get_xpath_count(plotly_js) == 1

