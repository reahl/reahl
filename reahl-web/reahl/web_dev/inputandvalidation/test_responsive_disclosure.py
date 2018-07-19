# Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import Fixture, expected, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath
from reahl.web.fw import Widget
from reahl.web.ui import A, Form, Div, SelectInput, Label, P
from reahl.component.modelinterface import  ChoiceField, Choice, exposed, IntegerField
from reahl.web_dev.inputandvalidation.test_widgetqueryargs import QueryStringFixture


@with_fixtures(WebFixture, QueryStringFixture)
def test_input_values_can_be_widget_arguments(web_fixture, query_string_fixture):
    """Widget query arguments can be linked to the value of an input, which means the Widget will be re-rendered if the input value changes."""

    fixture = query_string_fixture

    class ModelObject(object):
        @exposed
        def fields(self, fields):
           fields.choice = ChoiceField([Choice(1, IntegerField(label='One')), 
                                        Choice(2, IntegerField(label='Two')), 
                                        Choice(3, IntegerField(label='Three'))], 
                                        default=1,
                                        label='Choice')

    class MyChangingWidget(Div):
        def __init__(self, view, trigger_input, model_object):
            self.trigger_input = trigger_input
            self.model_object = model_object
            super(MyChangingWidget, self).__init__(view, css_id='dave')
            self.enable_refresh()
            trigger_input.enable_notify_change(self.query_fields.fancy_state)
            self.add_child(P(self.view, text='My state is now %s' % self.fancy_state))
            fixture.widget = self

        @property
        def fancy_state(self):
            return self.model_object.choice

        @exposed
        def query_fields(self, fields):
            fields.fancy_state = self.model_object.fields.choice


    class MyForm(Form):
        def __init__(self, view, an_object):
            super(MyForm, self).__init__(view, 'myform')
            self.select_input = SelectInput(self, an_object.fields.choice)
            self.add_child(Label(view, for_input=self.select_input))
            self.add_child(self.select_input)

    class MainWidget(Widget):
        def __init__(self, view):
            super(MainWidget, self).__init__(view)
            an_object = ModelObject()
            form = self.add_child(MyForm(view, an_object))
            self.add_child(MyChangingWidget(view, form.select_input, an_object))

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.wait_for(fixture.is_state_now, 1)
    browser.select(XPath.select_labelled('Choice'), 'Three')
    assert browser.wait_for(fixture.is_state_now, 3)


# What about funny types of input, such as checkboxes/radiobuttons/text vs select....?
# Overriding other things on the hash?
# Naming of notifier.
# Clashing names of things on the hash (larger issue)

