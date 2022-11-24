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

from reahl.tofu import scenario, Fixture, uses, expected
from reahl.tofu.pytestsupport import with_fixtures
from reahl.browsertools.browsertools import XPath, Browser
from reahl.web_dev.fixtures import WebFixture
from reahl.web.ui import Div, Form, FormLayout, SelectInput, ExposedNames, ChoiceField, Choice
from reahl.component.modelinterface import Field, IntegerField
from reahl.web.plotly import Chart

import plotly.graph_objects as go

chart = XPath.div().including_class('js-plotly-plot')
plotly_js = XPath('//script[contains(@src,"static/plotly")]')


@with_fixtures(WebFixture)
def test_plotly_basics(web_fixture):
    """How to add a Chart widget to a page."""

    fig = go.Figure()

    wsgi_app = web_fixture.new_wsgi_app(child_factory=Chart.factory(fig, 'unique_id'), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.is_element_present(chart)


@with_fixtures(WebFixture)
def test_no_javascript_when_no_chart_on_page(web_fixture):
    """When there aren't any Charts on the page, the plotly.js src should not be present."""

    wsgi_app = web_fixture.new_wsgi_app(child_factory=Div.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.get_xpath_count(plotly_js) == 0


@with_fixtures(WebFixture)
def test_adding_chart_with_ajax(web_fixture):
    """If a page is first rendered without any Charts, and a Chart appears via refresh, the necessary library code is activated"""

    class MyForm(Form):
        def __init__(self, view):
            self.choice = 1
            super().__init__(view, 'my_form')
            self.enable_refresh()

            self.use_layout(FormLayout())
            self.layout.add_input(SelectInput(self, self.fields.choice, refresh_widget=self))

            if self.choice == 2:
                self.add_child(Chart(view, go.Figure(), 'thechart'))

        fields = ExposedNames()
        fields.choice = lambda i: ChoiceField([Choice(1, IntegerField(label='Hide chart')),
                                               Choice(2, IntegerField(label='Show chart'))],
                                              label='Choice')


    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # Case: no chart
    assert not browser.is_element_present(chart)
    assert not browser.is_element_present(plotly_js)

    select_input = XPath.select_labelled('Choice')
    browser.select(select_input, 'Show chart')

    #Case: chart appears
    assert browser.is_element_present(chart)
    assert browser.is_element_present(plotly_js)


@with_fixtures(WebFixture)
def test_refreshing_chart_data_only(web_fixture):
    """You can update the chart without refreshing the whole Chart"""

    class MyForm(Form):
        def __init__(self, view):
            super().__init__(view, 'my_form')
            self.choice = 'one title'
            self.use_layout(FormLayout())
            select = self.layout.add_input(SelectInput(self, self.fields.choice))
            fig = go.Figure()
            fig.update_layout(title=self.choice)
            chart = self.add_child(Chart(view, fig, 'thechart'))
            select.set_refresh_widgets([chart.contents])

        fields = ExposedNames()
        fields.choice = lambda i: ChoiceField([Choice('one title', Field(label='One')),
                                               Choice('another title', Field(label='Two'))],
                                              label='Choice')


    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.is_element_present(chart)
    with browser.refresh_expected_for('#thechart', False), \
         browser.refresh_expected_for('#thechart-data', True):
        select_input = XPath.select_labelled('Choice')
        browser.select(select_input, 'Two')

