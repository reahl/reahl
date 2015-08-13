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

"""
Widgets and Layouts that provide an abstraction on top of Bootstrap (http://getbootstrap.com/)

.. versionadded:: 3.2

"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

from collections import OrderedDict
import copy

from reahl.web.fw import Layout, Widget
from reahl.web.ui import Form, Div, Header, Footer, Slot, HTML5Page, ValidationStateAttributes, AccessRightAttributes, \
                             Span, Input, TextInput, Label, TextNode, ButtonInput, P, WrappedInput

import reahl.web.layout
from reahl.component.exceptions import ProgrammerError, arg_checks, IsInstance
from reahl.web.ui import MenuItem


class Form(reahl.web.ui.Form):
    def get_js_options(self):
        return '''
        {
            errorElement: 'span',
            errorClass: 'has-error',
            validClass: 'has-success',
            onclick: function(element, event) {
			// click on selects, radiobuttons and checkboxes
			if ( element.name in this.submitted ) {
				this.element(element);
			}
			// or option elements, check parent select in that case
			else if (element.parentNode.name in this.submitted) {
				this.element(element.parentNode);
			}
            },
            highlight: function(element) {
                $(element).closest('.form-group').removeClass('has-success').addClass('has-error');
            },
            unhighlight: function(element) {
                $(element).closest('.form-group').removeClass('has-error').addClass('has-success');
            },
            errorPlacement: function (error, element) {
                error.addClass('help-block')
                if (element.parent('.input-group').length) {
                    error.insertAfter(element.parent());
                } else if (element.prop('type') === 'checkbox') {
                    error.insertAfter($(element).closest('.checkbox'));
                    error.insertAfter($(element).closest('.checkbox-inline'));
                } else if (element.prop('type') === 'radio') {
                    error.insertAfter($(element).closest('.radio').parent());
                    error.insertAfter($(element).closest('.radio-inline').parent());
                } else {
                    error.insertAfter(element);
                }
            }
         }
    '''

class TextInput(reahl.web.ui.TextInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field, fuzzy=False, placeholder=False):
        super(TextInput, self).__init__(form, bound_field, fuzzy=fuzzy, placeholder=placeholder)
        self.append_class('form-control')


class PasswordInput(reahl.web.ui.PasswordInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field):
        super(PasswordInput, self).__init__(form, bound_field)
        self.append_class('form-control')


class TextArea(reahl.web.ui.TextArea):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field, rows=None, columns=None):
        super(TextArea, self).__init__(form, bound_field, rows=rows, columns=rows)
        self.append_class('form-control')


class SelectInput(reahl.web.ui.SelectInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field):
        super(SelectInput, self).__init__(form, bound_field)
        self.append_class('form-control')


class CheckboxInput(reahl.web.ui.CheckboxInput):
    append_error = False
    add_default_attribute_source = False


class SingleRadioButton(reahl.web.ui.SingleRadioButton):
    append_error = False
    add_default_attribute_source = False

    def create_html_widget(self):
        return self.create_button_input()


class RadioButtonInput(reahl.web.ui.RadioButtonInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field, button_layout=None):
        self.button_layout = button_layout or ChoicesLayout()
        super(RadioButtonInput, self).__init__(form, bound_field)

    def create_main_element(self):
        return super(RadioButtonInput, self).create_main_element().use_layout(self.button_layout)

    def add_button_for_choice_to(self, widget, choice):
        button = SingleRadioButton(self, choice)
        widget.layout.add_choice(button)

class ButtonInput(reahl.web.ui.ButtonInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, event):
        super(ButtonInput, self).__init__(form, event)
        self.append_class('btn')

Button = ButtonInput


class SimpleFileInput(reahl.web.ui.SimpleFileInput):
    append_error = False
    add_default_attribute_source = False


class ButtonLayout(Layout):
    def __init__(self, style=None, size=None, active=False, wide=False):
        super(ButtonLayout, self).__init__()
        assert style in ['default', 'primary', 'success', 'info', 'warning', 'danger', 'link', None]
        assert size in ['lg', 'sm', 'xs', None]
        self.style = style
        self.size = size
        self.active = active
        self.wide = wide
        
    def customise_widget(self):
        self.widget.append_class('btn')
        if self.style:
            self.widget.append_class('btn-%s' % self.style)
        if self.size:
            self.widget.append_class('btn-%s' % self.size)
        if self.active:
            self.widget.append_class('active')
        if self.wide:
            self.widget.append_class('btn-block')


class ChoicesLayout(Layout):
    def __init__(self, inline=False):
        super(ChoicesLayout, self).__init__()
        self.inline = inline

    def add_choice(self, html_input):
        assert isinstance(html_input, (CheckboxInput, SingleRadioButton))
 
        label_widget = Label(self.view)

        if self.inline:
            label_widget.append_class('%s-inline' % html_input.input_type)
            wrapper = label_widget
        else:
            outer_div = Div(self.view)
            outer_div.append_class(html_input.input_type)
            outer_div.add_child(label_widget)
            wrapper = outer_div

        label_widget.add_child(html_input)
        label_widget.add_child(TextNode(self.view, html_input.label))

        self.widget.add_child(wrapper)

        return wrapper


class FormLayout(Layout):
    def __init__(self, inline=False, horizontal=False):
        super(FormLayout, self).__init__()
        assert not (inline and horizontal), 'Cannot set both inline and horizontal'
        self.inline = inline
        self.horizontal = horizontal

    def customise_widget(self):
        if self.inline:
            self.widget.append_class('form-inline')
        elif self.horizontal:
            self.widget.append_class('form-horizontal')

    def add_input(self, html_input, render_label=None, help_text=None):
        render_label = render_label if render_label is not None else not isinstance(html_input, CheckboxInput)
        form_group = self.widget.add_child(Div(self.view))
        form_group.append_class('form-group')
        form_group.add_attribute_source(ValidationStateAttributes(html_input, 
                                                             error_class='has-error', 
                                                             success_class='has-success'))
        form_group.add_attribute_source(AccessRightAttributes(html_input, disabled_class='disabled'))

        if render_label:
            label = form_group.add_child(Label(self.view, text=html_input.label, for_input=html_input))
            label.append_class('control-label' if render_label else 'sr-only')

        if isinstance(html_input, CheckboxInput):
            form_group.use_layout(ChoicesLayout(inline=False))
            form_group.layout.add_choice(html_input)
        else:
            form_group.add_child(html_input)

        if html_input.get_input_status() == 'invalidly_entered':
            error_text = form_group.add_child(Span(self.view, text=html_input.validation_error.message))
            error_text.append_class('help-block')
            error_text.append_class('has-error')
            error_text.set_attribute('for', html_input.name)
            error_text.set_attribute('generated', 'true')

        if help_text:
            help_text = form_group.add_child(P(self.view, text=help_text))
            help_text.append_class('help-block')

        return form_group







