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
from reahl.web.ui import A, Form, Div, SelectInput, Label, P, RadioButtonSelectInput, CheckboxSelectInput, CheckboxInput
from reahl.component.modelinterface import BooleanField, MultiChoiceField, ChoiceField, Choice, exposed, IntegerField
from reahl.web_dev.inputandvalidation.test_widgetqueryargs import QueryStringFixture

class ResponsiveDisclosureFixture(Fixture):
    def new_ModelObject(self):
        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = ChoiceField([Choice(1, IntegerField(label='One')), 
                                            Choice(2, IntegerField(label='Two')), 
                                            Choice(3, IntegerField(label='Three'))], 
                                            default=1,
                                            label='Choice')
        return ModelObject

    def new_MyChangingWidget(self):
        class MyChangingWidget(Div):
            def __init__(self, view, trigger_input, model_object):
                self.trigger_input = trigger_input
                self.model_object = model_object
                super(MyChangingWidget, self).__init__(view, css_id='dave')
                self.enable_refresh()
                trigger_input.enable_notify_change(self.query_fields.fancy_state)
                self.add_child(P(self.view, text='My state is now %s' % self.fancy_state))

            @property
            def fancy_state(self):
                return self.model_object.choice

            @exposed
            def query_fields(self, fields):
                fields.fancy_state = self.model_object.fields.choice

        return MyChangingWidget

    def new_MyForm(self):
        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.select_input = SelectInput(self, an_object.fields.choice)
                self.add_child(Label(view, for_input=self.select_input))
                self.add_child(self.select_input)

        return MyForm
    
    def new_MainWidget(self):
        fixture = self
        class MainWidget(Widget):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)
                an_object = fixture.ModelObject()
                form = self.add_child(fixture.MyForm(view, an_object))
                self.add_child(fixture.MyChangingWidget(view, form.select_input, an_object))

        return MainWidget


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_input_values_can_be_widget_arguments(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """Widget query arguments can be linked to the value of an input, which means the Widget will be re-rendered if the input value changes."""

    fixture = responsive_disclosure_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    #web_fixture.pdb()

    assert browser.wait_for(query_string_fixture.is_state_now, 1)
    browser.select(XPath.select_labelled('Choice'), 'Three')
    assert browser.wait_for(query_string_fixture.is_state_now, 3)


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_changing_values_do_not_disturb_other_hash_state(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """..."""

    fixture = responsive_disclosure_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    #web_fixture.pdb()

    assert browser.wait_for(query_string_fixture.is_state_now, 1)
    query_string_fixture.change_fragment('#choice=2&other_var=other_value')
    browser.select(XPath.select_labelled('Choice'), 'Three')
    assert query_string_fixture.get_fragment() == '#choice=3&other_var=other_value'


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_radio(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """..."""

    fixture = responsive_disclosure_fixture

    class MyForm(Form):
        def __init__(self, view, an_object):
            super(MyForm, self).__init__(view, 'myform')
            self.select_input = RadioButtonSelectInput(self, an_object.fields.choice)
            self.select_input.set_id('marvin')
            self.add_child(Label(view, for_input=self.select_input))
            self.add_child(self.select_input)

    fixture.MyForm = MyForm

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    web_fixture.pdb()

    assert browser.wait_for(query_string_fixture.is_state_now, 1)
    browser.click(XPath.radio_button_labelled('Three'))
    assert browser.wait_for(query_string_fixture.is_state_now, 3)


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_checkbox_single(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """..."""

    fixture = responsive_disclosure_fixture

    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.choice = BooleanField(default=False, label='Choice')
    fixture.ModelObject = ModelObject


    class MyForm(Form):
        def __init__(self, view, an_object):
            super(MyForm, self).__init__(view, 'myform')
            self.select_input = CheckboxInput(self, an_object.fields.choice)
            self.select_input.set_id('marvin')
            self.add_child(Label(view, for_input=self.select_input))
            self.add_child(self.select_input)

    fixture.MyForm = MyForm

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    web_fixture.pdb()

    assert browser.wait_for(query_string_fixture.is_state_now, 1)
    browser.click(XPath.checkbox_labelled('Three'))
    assert browser.wait_for(query_string_fixture.is_state_now, 3)


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_checkboxselect_multi(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """..."""

    fixture = responsive_disclosure_fixture
    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.choice = MultiChoiceField([Choice(1, IntegerField(label='One')), 
                                        Choice(2, IntegerField(label='Two')), 
                                        Choice(3, IntegerField(label='Three'))], 
                                        default=[1],
                                        label='Choice')
    fixture.ModelObject = ModelObject

    class MyForm(Form):
        def __init__(self, view, an_object):
            super(MyForm, self).__init__(view, 'myform')
            self.select_input = CheckboxSelectInput(self, an_object.fields.choice)
            self.select_input.set_id('marvin')
            self.add_child(Label(view, for_input=self.select_input))
            self.add_child(self.select_input)

    fixture.MyForm = MyForm

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    web_fixture.pdb()

    assert browser.wait_for(query_string_fixture.is_state_now, 1)
    browser.click(XPath.checkbox_labelled('Three'))
    assert browser.wait_for(query_string_fixture.is_state_now, 3)

# What about funny types of input, such as checkboxes/radiobuttons/text vs select....?
#   what to do with a list of values
# Overriding other things on the hash?
# Naming of notifier.
# Clashing names of things on the hash (larger issue)

# TODO: break if a user sends a ChoiceField to a CheckboxSelectInput

