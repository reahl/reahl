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

import six

from reahl.tofu import vassert, scenario, expected, test

from reahl.webdev.tools import XPath, Browser

from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture

from reahl.web.fw import UserInterface, Url

from reahl.web_dev.inputandvalidation.inputtests import InputMixin

from reahl.component.exceptions import ProgrammerError, IsInstance
from reahl.component.modelinterface import exposed, Field, BooleanField, Event, Choice, ChoiceField
from reahl.web.bootstrap.ui import A, Div, P, HTML5Page, Header, Footer
from reahl.web.bootstrap.forms import TextInput, InputGroup



class InputGroupFixture(WebFixture, InputMixin):
    def new_an_input(self):
        return TextInput(self.form, self.field)

    @scenario
    def plain_text(self):
        self.input_group = InputGroup('before text', self.an_input, 'after text')
        self.expects_before_html = '<span class="input-group-addon">before text</span>'
        self.expects_after_html = '<span class="input-group-addon">after text</span>'

    @scenario
    def none_specified(self):
        self.input_group = InputGroup(None, self.an_input, None)
        self.expects_before_html = ''
        self.expects_after_html = ''

    @scenario
    def widgets(self):
        self.input_group = InputGroup(P(self.view, text='before widget'), 
                                      self.an_input, 
                                      P(self.view, text='after widget'))
        self.expects_before_html = '<span class="input-group-addon"><p>before widget</p></span>'
        self.expects_after_html = '<span class="input-group-addon"><p>after widget</p></span>'


@test(InputGroupFixture)
def input_group(fixture):
    """An InputGroup is a composition of an input with some text or Widget before and/or after an input."""
    tester = WidgetTester(fixture.input_group)
    
    [outer_div] = tester.xpath('//div')
    vassert( outer_div.attrib['class'] == 'input-group' )
    
    if fixture.expects_before_html:
        rendered_html = tester.get_html_for('//div/input/preceding-sibling::span')
        vassert( rendered_html == fixture.expects_before_html )
    else:
        vassert( not tester.is_element_present('//div/input/preceding-sibling::span') )

    children = outer_div.getchildren()
    the_input = children[1] if fixture.expects_before_html else children[0]
    vassert( the_input.tag == 'input' )
    vassert( the_input.name == 'an_attribute' )

    if fixture.expects_after_html:
        rendered_html = tester.get_html_for('//div/input/following-sibling::span')
        vassert( rendered_html == fixture.expects_after_html )
    else:
        vassert( not tester.is_element_present('//div/input/following-sibling::span') )



