# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.tofu import scenario, Fixture
from reahl.tofu.pytestsupport import with_fixtures

from reahl.web.fw import Url
from reahl.web.ui import Form, TextInput
from reahl.component.modelinterface import EmailField, ExposedNames

from reahl.browsertools.browsertools import Browser, XPath

from reahl.web_dev.fixtures import WebFixture


class ValidationScenarios(Fixture):
    @scenario
    def valid_field(self):
        # - a field that passes validation
        self.url = Url('/__some_form_validate_method?some_form-field_name=valid@email.org')
        self.expected_body = 'true'
        self.expected_status = '200 OK' 
        self.expected_content_type = 'application/json'
        self.expected_charset = 'utf-8'

    @scenario
    def failing_field(self):
        # - a field that fails one or more? constraints
        self.url = Url('/__some_form_validate_method?some_form-field_name=invalidaddress')
        self.expected_body = '"field_name should be a valid email address"'
        self.expected_status = '200 OK' 
        self.expected_content_type = 'application/json'
        self.expected_charset = 'utf-8'

    @scenario
    def non_existent_field(self):
        # - a field that does not exist
        self.url = Url('/__some_form_validate_method?nonexistantfield=value')
        self.expected_body = 'false'
        self.expected_status = '200 OK' 
        self.expected_content_type = 'application/json'
        self.expected_charset = 'utf-8'

    @scenario
    def empty_querystring(self):
        # - an empty querystring
        self.url = Url('/__some_form_validate_method')
        self.expected_body = 'false'
        self.expected_status = '200 OK' 
        self.expected_content_type = 'application/json'
        self.expected_charset = 'utf-8'


@with_fixtures(WebFixture, ValidationScenarios)
def test_remote_field_validator_handles_GET(web_fixture, validation_scenarios):
    fixture = validation_scenarios


    class ModelObject:
        fields = ExposedNames()
        fields.field_name = lambda i: EmailField()

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.add_child(TextInput(self, model_object.fields.field_name))

    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory(name='some_form'))
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = Browser(wsgi_app)

    browser.open('/')
    csrf_token_string = web_fixture.get_csrf_token_string(browser=browser)
    browser.open(str(fixture.url), headers={'X-CSRF-TOKEN':csrf_token_string})
    response = browser.last_response

    assert response.unicode_body == fixture.expected_body 
    assert response.status == fixture.expected_status 
    assert response.content_type == fixture.expected_content_type 
    assert response.charset == fixture.expected_charset 

