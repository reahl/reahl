# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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
.. versionadded:: 3.2

Bootstrap-styled versions of Forms, Inputs and related Layouts.



"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

from reahl.component.exceptions import arg_checks, IsInstance
from reahl.component.i18n import Translator

import reahl.web.ui
from reahl.web.ui import WrappedInput, Label, HTMLAttributeValueOption
from reahl.web.bootstrap.ui import Div, P, WrappedInput, A, TextNode, Span
from reahl.web.bootstrap.grid import ColumnLayout


_ = Translator('reahl-web')


class Form(reahl.web.ui.Form):
    """A Form is a container for Inputs. Any Input has to belong to a Form. When a user clicks on
       a Button associated with a Form, the Event to which the Button is linked occurs at the 
       server. The value of every Input that is associated with the Form is sent along with the 
       Event to the server.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param unique_name: A name for this form, unique in the UserInterface where it is used.
    """
    javascript_widget_name = 'bootstrapform'


class NestedForm(reahl.web.ui.NestedForm):
    """A NestedForm can create the appearance of one Form being visually contained in
       another. Forms are not allowed to be children of other Forms but this restriction does 
       not apply to NestedForms. 

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param unique_name: (See :class:`Form`)
       :keyword css_id: (See :class:`HTMLElement`)
       
    """
    def create_out_of_bound_form(self, view, unique_name):
        return Form(view, unique_name, rendered_form=self)


class TextInput(reahl.web.ui.TextInput):
    """A single line Input for typing plain text.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :param fuzzy: If True, the typed input will be dealt with as "fuzzy input". Fuzzy input is
                     when a user is allowed to type almost free-form input for structured types of input,
                     such as a date. The assumption is that the `bound_field` used should be able to parse
                     such "fuzzy input". If fuzzy=True, the typed value will be changed on the fly to
                     the system's interpretation of what the user originally typed as soon as the TextInput
                     looses focus.
       :param placeholder: If given a string, placeholder is displayed in the TextInput if the TextInput 
                     is empty in order to provide a hint to the user of what may be entered into the TextInput. 
                     If given True instead of a string, the label of the TextInput is used.
    """
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field, fuzzy=False, placeholder=False):
        super(TextInput, self).__init__(form, bound_field, fuzzy=fuzzy, placeholder=placeholder)
        self.append_class('form-control')


class FieldSet(reahl.web.ui.FieldSet):
    """A visual grouping of HTMLElements inside a Form.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword legend_text: If given, the FieldSet will have a Legend containing this text.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, legend_text=None, css_id=None):
        super(FieldSet, self).__init__(view, legend_text=legend_text, css_id=css_id)


class PasswordInput(reahl.web.ui.PasswordInput):
    """A PasswordInput is a single line text input, but it does not show what the user is typing.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field):
        super(PasswordInput, self).__init__(form, bound_field)
        self.append_class('form-control')


class TextArea(reahl.web.ui.TextArea):
    """A muli-line Input for plain text.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
       :param rows: The number of rows that this Input should have.
       :param columns: The number of columns that this Input should have.
    """
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field, rows=None, columns=None):
        super(TextArea, self).__init__(form, bound_field, rows=rows, columns=rows)
        self.append_class('form-control')


class SelectInput(reahl.web.ui.SelectInput):
    """An Input that lets the user select an :class:`reahl.component.modelinterface.Choice` from a dropdown
       list of valid ones.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field):
        super(SelectInput, self).__init__(form, bound_field)
        self.append_class('form-control')


class PrimitiveCheckboxInput(reahl.web.ui.CheckboxInput):
    """A primitive checkbox (only the box itself).

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """
    append_error = False
    add_default_attribute_source = False


class CheckboxInput(WrappedInput):
    """A checkbox (with its label).

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """
    def __init__(self, form, bound_field):
        super(CheckboxInput, self).__init__(PrimitiveCheckboxInput(form, bound_field))
        div = Div(self.view).use_layout(ChoicesLayout(inline=False))
        div.layout.add_choice(self.input_widget)
        self.add_child(div)
        self.set_html_representation(div)

    @property
    def includes_label(self):
        return True
        
    @property
    def jquery_selector(self):
        return '%s.closest("div")' % (self.input_widget.jquery_selector)
        

class PrimitiveRadioButtonInput(reahl.web.ui.SingleRadioButton):
    append_error = False
    add_default_attribute_source = False

    def create_html_widget(self):
        return self.create_button_input()


class RadioButtonInput(reahl.web.ui.RadioButtonInput):
    """An Input that lets the user select a :class:`reahl.component.modelinterface.Choice` from a list of valid ones
       shown as radio buttons of which only one can be selected at a time.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field, button_layout=None):
        self.button_layout = button_layout or ChoicesLayout()
        super(RadioButtonInput, self).__init__(form, bound_field)

    def create_main_element(self):
        main_element = super(RadioButtonInput, self).create_main_element().use_layout(self.button_layout)
        main_element.append_class('form-control-label')
        return main_element

    def add_button_for_choice_to(self, widget, choice):
        button = PrimitiveRadioButtonInput(self, choice)
        widget.layout.add_choice(button)

    @property
    def includes_label(self):
        return True


class ButtonInput(reahl.web.ui.ButtonInput):
    """A button.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param event: The :class:`~reahl.web.component.modelinterface.Event` that will fire when the user clicks on this ButtonInput.
       :keyword css_id: (See :class:`HTMLElement`)
    """
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, event):
        super(ButtonInput, self).__init__(form, event)
        self.append_class('btn')

Button = ButtonInput


class StaticData(reahl.web.ui.Input):
    """A fake input which just displays the value of the :class:`~reahl.component.modelinterface.Field` 
       to which the StaticData is attached, but does not include a way to change the value.

       This is useful in cases where you want to display some data that is exposed via a 
       :class:`~reahl.component.modelinterface.Field` in a Form amongst normal Inputs.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`)
    """
    def __init__(self, form, bound_field):
        super(StaticData, self).__init__(form, bound_field)
        p = self.add_child(P(self.view, text=self.value))
        p.append_class('form-control-static')

    def can_write(self):
        return False




class CueInput(reahl.web.ui.WrappedInput):
    """A Widget that wraps around a given Input to augment it with a "cue" - a hint that
       appears only when the Input has focus. The intention of the cue is to give the 
       user a hint as to what to input into the Input.

       :param html_input: The :class:`~reahl.web.ui.Input` to be augmented.
       :param cue_widget: An :class:`~reahl.web.fw.Widget` that serves as the cue.
    """
    def __init__(self, html_input, cue_widget):
        super(CueInput, self).__init__(html_input)
        div = self.add_child(Div(self.view))
        self.set_html_representation(div)

        div.append_class('reahl-bootstrapcueinput')
        cue_widget.append_class('reahl-bootstrapcue')

        div.add_child(html_input)
        self.cue_widget = div.add_child(cue_widget)

    def get_js(self, context=None):
        js = ['$(".reahl-bootstrapcueinput").bootstrapcueinput();']
        return super(CueInput, self).get_js(context=context) + js

    @property
    def includes_label(self):
        return self.input_widget.includes_label



class ButtonStyle(HTMLAttributeValueOption):
    valid_options = ['default', 'primary', 'success', 'info', 'warning', 'danger', 'link']
    def __init__(self, name):
        super(ButtonStyle, self).__init__(name, name is not None, prefix='btn', 
                                          constrain_value_to=self.valid_options)


class ButtonSize(HTMLAttributeValueOption):
    valid_options = ['lg', 'sm', 'xs']
    def __init__(self, size_string):
        super(ButtonSize, self).__init__(size_string, size_string is not None, prefix='btn', 
                                         constrain_value_to=self.valid_options)



class ButtonLayout(reahl.web.ui.Layout):
    """A ButtonLayout can be used to make something (like an :class:`A`) look like
       a :class:`Button`. It has a few options controlling specifics of that look, 
       and can be used to change the default look of a :class:`Button` as well.

       :keyword style: The general style of the button 
                   (one of: 'default', 'primary', 'success', 'info', 'warning', 'danger', 'link')
       :keyword size: The size of the button (one of: 'xs', 'sm', 'lg')
       :keyword active: If True, the button is visually altered to indicate it is active 
                        (buttons can be said to be active in the same sense that a menu item can 
                        be the currently active menu item).
       :keyword wide: If True, the button stretches to the entire width of its parent.

    """ 
    def __init__(self, style=None, size=None, active=False, wide=False):
        super(ButtonLayout, self).__init__()
        self.style = ButtonStyle(style)
        self.size = ButtonSize(size)
        self.active = HTMLAttributeValueOption('active', active)
        self.wide = HTMLAttributeValueOption('btn-block', wide)

    def customise_widget(self):
        self.widget.append_class('btn')

        if isinstance(self.widget, A) and self.widget.disabled:
            self.widget.append_class('disabled')
        for option in [self.style, self.size, self.active, self.wide]:
            if option.is_set: 
                self.widget.append_class(option.as_html_snippet())
        


class ChoicesLayout(reahl.web.ui.Layout):
    def __init__(self, inline=False):
        super(ChoicesLayout, self).__init__()
        self.inline = inline

    @arg_checks(html_input=IsInstance((PrimitiveCheckboxInput, PrimitiveRadioButtonInput)))
    def add_choice(self, html_input): 
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


class FormLayout(reahl.web.ui.Layout):
    """A FormLayout is used to create Forms that have a consistent look by arranging 
       all its Inputs, their Labels and possible validation error messages in a 
       certain way.

       This basic FormLayout positions Labels above added Inputs and allow for an
       optional helpful text message with each input.

       Different kinds of FormLayouts allow different kinds of arrangements.

       Different FormLayouts can be used on different sub-parts of a Form by
       composing a Form of Divs of FieldSets that each use a different 
       FormLayout.
    """
    def create_form_group(self, html_input):
        form_group = self.widget.add_child(Div(self.view))
        form_group.append_class('form-group')
        form_group.add_attribute_source(reahl.web.ui.ValidationStateAttributes(html_input, 
                                                             error_class='has-danger', 
                                                             success_class='has-success'))
        form_group.add_attribute_source(reahl.web.ui.AccessRightAttributes(html_input, disabled_class='disabled'))
        return form_group

    def add_input_to(self, parent_element, html_input):
        return parent_element.add_child(html_input)

    def add_validation_error_to(self, form_group, html_input):
        error_text = form_group.add_child(Span(self.view, text=html_input.validation_error.message))
        error_text.append_class('text-help')
        error_text.append_class('has-danger')
        error_text.set_attribute('for', html_input.name)
        error_text.set_attribute('generated', 'true')
        return error_text

    def add_help_text_to(self, parent_element, help_text):
        help_text_p = parent_element.add_child(P(self.view, text=help_text))
        help_text_p.append_class('text-muted')
        return help_text_p

    def add_label_to(self, form_group, html_input, hidden):
        label = form_group.add_child(Label(self.view, text=html_input.label, for_input=html_input))
        if hidden:
            label.append_class('sr-only')
        return label

    def add_input(self, html_input, hide_label=False, help_text=None):
        """Adds an input to the Form.

           :param html_input: The Input to add.
           :keyword hide_label: If True, makes the label invisible yet available to screenreaders.
           :keyword help_text: Helpful text to display with each Input field.
        """
        form_group = self.create_form_group(html_input)

        if not html_input.includes_label:
            self.add_label_to(form_group, html_input, hide_label)

        self.add_input_to(form_group, html_input)

        if html_input.get_input_status() == 'invalidly_entered':
            self.add_validation_error_to(form_group, html_input)

        if help_text:
            self.add_help_text_to(form_group, help_text)

        return html_input


class GridFormLayout(FormLayout):
    """A GridFormLayout arranges its Labels and Inputs in a grid with two columns. Labels 
       go into the left column and Inputs into the right column. The programmer specifies
       how wide each column should be.

       :param label_column_size: A :class:`~reahl.web.bootstrap.grid.ResponsiveSize` for the width of the Label column.
       :param input_column_size: A :class:`~reahl.web.bootstrap.grid.ResponsiveSize` for the width of the Input column.
    """
    def __init__(self, label_column_size, input_column_size):
        super(GridFormLayout, self).__init__()
        self.label_column_size = label_column_size
        self.input_column_size = input_column_size

    def create_form_group(self, html_input):
        form_group = super(GridFormLayout, self).create_form_group(html_input)
        form_group.use_layout(ColumnLayout(('label', self.label_column_size), ('input', self.input_column_size)))
        return form_group

    def add_label_to(self, form_group, html_input, hidden):
        column = form_group.layout.columns['label']
        label = super(GridFormLayout, self).add_label_to(column, html_input, hidden)
        label.append_class('form-control-label')
        return label

    def add_input_to(self, parent_element, html_input):
        input_column = parent_element.layout.columns['input']
        return super(GridFormLayout, self).add_input_to(input_column, html_input)

    def add_help_text_to(self, parent_element, help_text):
        input_column = parent_element.layout.columns['input']
        return super(GridFormLayout, self).add_help_text_to(input_column, help_text)


class InlineFormLayout(FormLayout):
    """A FormLayout which positions all its Inputs and Labels on one line. The browser
       flows this like any paragraph of text. Each Label precedes its associated Input."""
    def customise_widget(self):
        super(InlineFormLayout, self).customise_widget()
        self.widget.append_class('form-inline')


class InputGroup(reahl.web.ui.WrappedInput):
    """A composition of an Input with something preceding and/or following it.

    :param prepend: A :class:`~reahl.web.fw.Widget` to prepend to the :class:`~reahl.web.ui.Input`.
    :param input_widget: The :class:`~reahl.web.ui.Input` to use.
    :param append: A :class:`~reahl.web.fw.Widget` to append to the :class:`~reahl.web.ui.Input`.
    """
    def __init__(self, prepend, input_widget, append):
        super(InputGroup, self).__init__(input_widget)
        self.div = self.add_child(Div(self.view))
        self.div.append_class('input-group')
        if prepend:
            self.add_as_addon(prepend)
        self.input_widget = self.div.add_child(input_widget)
        if append:
            self.add_as_addon(append)
        self.set_html_representation(self.div)

    def add_as_addon(self, addon):
        if isinstance(addon, six.string_types):
            span = Span(self.view, text=addon)
        else:
            span = Span(self.view)
            span.add_child(addon)
        span.append_class('input-group-addon')
        return self.div.add_child(span)
