# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import unicode_literals
from __future__ import print_function
import six
from nose.tools import istest
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import vassert

from reahl.web.fw import Url
from reahl.web.ui import Form, TextInput
from reahl.component.modelinterface import EmailField, exposed

from reahl.web_dev.inputandvalidation.eventhandling import FormFixture
from reahl.webdev.tools import Browser


class Scenarios(FormFixture):
    @scenario
    def valid_field(self):
        # - a field that passes validation
        self.url = Url('/__some_form_validate_method?field_name=valid@email.org')
        self.expected_body = 'true'
        self.expected_status = '200 OK' 
        self.expected_content_type = 'application/json'
        self.expected_charset = 'utf-8'

    @scenario
    def failing_field(self):
        # - a field that fails one or more? constraints
        self.url = Url('/__some_form_validate_method?field_name=invalidaddress')
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

    
@istest
class FieldValidatorTests(object):
    @test(Scenarios)
    def remote_field_validator_handles_GET(self, fixture):
        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.field_name = EmailField()

        model_object = ModelObject()

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                self.add_child(TextInput(self, model_object.fields.field_name))

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory(name='some_form'))
        fixture.reahl_server.set_app(wsgi_app)
        browser = Browser(wsgi_app)

        browser.open(six.text_type(fixture.url))
        response = browser.last_response

        vassert( response.body == fixture.expected_body )
        vassert( response.status == fixture.expected_status )
        vassert( response.content_type == fixture.expected_content_type )
        vassert( response.charset == fixture.expected_charset )

