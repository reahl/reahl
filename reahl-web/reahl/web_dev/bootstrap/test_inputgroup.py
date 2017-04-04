# Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import scenario, Fixture, uses
from reahl.tofu.pytest_support import with_fixtures

from reahl.webdev.tools import WidgetTester

from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.forms import TextInput, InputGroup

from reahl.web_dev.fixtures import WebFixture2
from reahl.web_dev.inputandvalidation.test_input import SimpleInputFixture

@uses(web_fixture=WebFixture2, simple_input_fixture=SimpleInputFixture)
class InputGroupFixture(Fixture):

    @property
    def context(self):
        return self.web_fixture.context

    def new_an_input(self):
        return TextInput(self.simple_input_fixture.form, self.simple_input_fixture.field)

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
        self.input_group = InputGroup(P(self.web_fixture.view, text='before widget'),
                                      self.an_input, 
                                      P(self.web_fixture.view, text='after widget'))
        self.expects_before_html = '<span class="input-group-addon"><p>before widget</p></span>'
        self.expects_after_html = '<span class="input-group-addon"><p>after widget</p></span>'


@with_fixtures(WebFixture2, InputGroupFixture)
def test_input_group(web_fixture, input_group_fixture):
    """An InputGroup is a composition of an input with some text or Widget before and/or after an input."""
    fixture = input_group_fixture

    with web_fixture.context:
        tester = WidgetTester(fixture.input_group)
    
        [outer_div] = tester.xpath('//div')
        assert outer_div.attrib['class'] == 'input-group'

        if fixture.expects_before_html:
            rendered_html = tester.get_html_for('//div/input/preceding-sibling::span')
            assert rendered_html == fixture.expects_before_html
        else:
            assert not tester.is_element_present('//div/input/preceding-sibling::span')

        children = outer_div.getchildren()
        the_input = children[1] if fixture.expects_before_html else children[0]
        assert the_input.tag == 'input'
        assert the_input.name == 'an_attribute'

        if fixture.expects_after_html:
            rendered_html = tester.get_html_for('//div/input/following-sibling::span')
            assert rendered_html == fixture.expects_after_html
        else:
            assert not tester.is_element_present('//div/input/following-sibling::span')

