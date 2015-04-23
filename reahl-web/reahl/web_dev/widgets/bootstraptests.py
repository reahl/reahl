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

from reahl.web.fw import UserInterface
from reahl.web.ui import Div, P, HTML5Page, Header, Footer

from reahl.component.exceptions import ProgrammerError, IsInstance
from reahl.web.bootstrap import ColumnLayout, ResponsiveSize



@test(WebFixture)
def column_layout_basics(fixture):
    """The bootstrap.ColumnLayout adds the correct classes for Bootstrap to lay out its Widget as a row with columns."""

    layout = ColumnLayout(('column_a', ResponsiveSize(lg=4)), ('column_b', ResponsiveSize(lg=8)))
    widget = Div(fixture.view)
    
    vassert( not widget.has_attribute('class') )
    
    widget.use_layout(layout)

    vassert( widget.get_attribute('class') == 'row' )
    column_a, column_b = widget.children

    vassert( 'col-lg-4' in column_a.get_attribute('class')  )
    vassert( 'col-lg-8' in column_b.get_attribute('class')  )


@test(WebFixture)
def column_layout_sizes(fixture):
    """Is is mandatory to specify sizes for all columns."""

    with expected(ProgrammerError):
        ColumnLayout('column_a')


@test(WebFixture)
def adding_columns(fixture):
    """You can add additional columns after construction."""

    widget = Div(fixture.view).use_layout(ColumnLayout())

    vassert( not widget.children )

    widget.layout.add_column(ResponsiveSize(lg=4))

    [added_column] = widget.children
    vassert( added_column.get_attribute('class') == 'col-lg-4' )


@test(WebFixture)
def allowed_sizes(fixture):
    """The device classes for which sizes can be specified."""
    size = ResponsiveSize(xs=1, sm=2, md=3, lg=4)

    vassert( size == {'xs':1, 'sm':2, 'md':3, 'lg':4} )


@test(WebFixture)
def column_offsets(fixture):
    """You can optionally specify space to leave empty (an offset) before a column at specific device sizes."""

    layout = ColumnLayout(('column_a', ResponsiveSize(lg=6).offset(xs=2, sm=4, md=6, lg=3)))
    widget = Div(fixture.view).use_layout(layout)

    [column_a] = layout.columns.values()

    vassert( 'col-lg-6' in column_a.get_attribute('class')  )
    vassert( 'col-lg-offset-3' in column_a.get_attribute('class')  )
    vassert( 'col-xs-offset-2' in column_a.get_attribute('class')  )
    vassert( 'col-sm-offset-4' in column_a.get_attribute('class')  )
    vassert( 'col-md-offset-6' in column_a.get_attribute('class')  )


@test(WebFixture)
def column_clearfix(fixture):
    """If a logical row spans more than one visual row for a device size, bootstrap clearfixes are
       automatically inserted to ensure cells in resultant visual rows are neatly arranged.
    """

    # Case: Adding a correct clearfix in the right place
    wrapping_layout = ColumnLayout(('column_a', ResponsiveSize(xs=8).offset(xs=2)),
                                   ('column_b', ResponsiveSize(xs=2).offset(xs=2))
    )
    widget = Div(fixture.view).use_layout(wrapping_layout)

    [column_a, clearfix, column_b] = widget.children           
    vassert( [column_a, column_b] == [i for i in wrapping_layout.columns.values()] )
    vassert( 'clearfix' in clearfix.get_attribute('class')  )
    vassert( 'visible-xs-block' in clearfix.get_attribute('class')  )

    # Case: When clearfix needs to take "implicit" sizes of smaller device classes into account
    wrapping_layout = ColumnLayout(('column_a', ResponsiveSize(xs=8).offset(xs=2)),
                                   ('column_b', ResponsiveSize(lg=2).offset(lg=2))
    )
    widget = Div(fixture.view).use_layout(wrapping_layout)

    [column_a, clearfix, column_b] = widget.children           
    vassert( [column_a, column_b] == [i for i in wrapping_layout.columns.values()] )
    vassert( 'clearfix' in clearfix.get_attribute('class')  )
    vassert( 'visible-lg-block' in clearfix.get_attribute('class')  )

    # Case: When no clearfix must be added
    non_wrapping_layout = ColumnLayout(('column_a', ResponsiveSize(xs=2).offset(xs=2)),
                                       ('column_b', ResponsiveSize(xs=2))
    )
    widget = Div(fixture.view).use_layout(non_wrapping_layout)

    [column_a, column_b] = widget.children
    vassert( [column_a, column_b] == [i for i in non_wrapping_layout.columns.values()] )  


@test(WebFixture)
def form(fixture):
    from reahl.web.ui import Layout, Form, DerivedInputAttributes, Span, Label, TextInput
    from reahl.component.modelinterface import EmailField, exposed
    from reahl.stubble import EmptyStub

    class HelpBlock(DerivedInputAttributes):
        def get_error_widget(self):
            widget = Span(self.view, text=self.validation_error_message)
            widget.append_class('help-block')
            return widget

    class FormGroup(Div):
        def __init__(self, view, input_widget, label_text):
            super(FormGroup, self).__init__(view)
            self.append_class('form-group')

            input_widget.html_input_attributes = HelpBlock(input_widget)
            input_widget.append_class('form-control')

            label = Label(view, text=label_text, for_input=input_widget)
            label.append_class('control-label')

            self.add_child(label)
            self.add_child(input_widget)



    class Horizontal(Layout):
         def customise_widget(self):
            self.widget.append_class('form-horizontal')


    field = EmailField()
    field.bind('field_name', EmptyStub())
    form = Form(fixture.view, 'boots').use_layout(Horizontal())
    text_input = TextInput(form, field)

    text_input.enter_value('not an email address')
    text_input.prepare_input()

    form.add_child(FormGroup(fixture.view, text_input, 'Email'))

    #import pdb;pdb.set_trace()
    print (form.render())

@test(WebFixture)
def form2(fixture):
    from reahl.web.ui import Layout, Form, DerivedInputAttributes, Span, Label, TextInput, Button
    from reahl.component.modelinterface import EmailField, exposed, Event, Action
    from reahl.stubble import EmptyStub

    class HelpBlock(DerivedInputAttributes):
        def get_error_widget(self, error_message):
            widget = Span(self.view, text=self.validation_error_message)
            widget.append_class('help-block')
            return widget

    class FormGroup(Div):
        def __init__(self, view, input_widget, label_text):
            super(FormGroup, self).__init__(view)
            self.append_class('form-group')

            input_widget.html_input_attributes = HelpBlock(input_widget)
            input_widget.append_class('form-control')

            label = Label(view, text=label_text, for_input=input_widget)
            label.append_class('control-label')

            self.add_child(label)
            self.add_child(input_widget)



    class Horizontal(Layout):
         def customise_widget(self):
            self.widget.append_class('form-horizontal')


    field = EmailField()
    field.bind('field_name', EmptyStub())

    class ModelObject(object):
        def handle_event(self):
            pass
        @exposed
        def events(self, events):
            events.an_event = Event(label='click me', action=Action(self.handle_event))
        @exposed
        def fields(self, fields):
            fields.an_attribute = field
    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)

            self.use_layout(Horizontal())
            text_input = TextInput(self, field)

            self.add_child(FormGroup(fixture.view, text_input, 'Email'))

            self.define_event_handler(model_object.events.an_event)
            self.add_child(Button(self, model_object.events.an_event))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    #import pdb;pdb.set_trace()

