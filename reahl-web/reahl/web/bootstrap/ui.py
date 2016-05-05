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
This module houses stylised versions of very basic user interface
elements -- user interface elements that have a one-to-one
correspondence to HTML elements (or are of similar simplicity).

.. versionadded:: 3.2


"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

from copy import copy

from reahl.component.exceptions import ProgrammerError, arg_checks, IsInstance
from reahl.component.i18n import Translator

import reahl.web.ui
from reahl.web.ui import A, Article, Body, Br, Caption, Col, ColGroup, Div, FieldSet, Footer, H, Head, Header, Img, \
    Label, Li, Link, LiteralHTML, Meta, Nav, Ol, OptGroup, P, RunningOnBadge, Slot, Span, Tbody, Td, TextNode, \
    Tfoot, Th, Thead, Title, Tr, Ul, DynamicColumn, StaticColumn, WrappedInput, FieldSet

from reahl.web.bootstrap.grid import Container, ColumnLayout, ResponsiveSize, HTMLAttributeValueOption


_ = Translator('reahl-web')




class HTML5Page(reahl.web.ui.HTML5Page):
    """A web page that may be used as the page of a web application. It ensures that everything needed by
       the framework (linked CSS and JavaScript, etc) is available on such a page.

       .. admonition:: Styling
       
          Renders as an HTML5 page with customised <head> and an empty <body>.
       
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword title: (See :class:`reahl.web.ui.HTML5Page`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, title='$current_title', css_id=None):
        super(HTML5Page, self).__init__(view, title=title, css_id=css_id)

    def check_form_related_programmer_errors(self):
        super(HTML5Page, self).check_form_related_programmer_errors()
        self.check_grids_nesting()
        
    def check_grids_nesting(self):
        for widget, parents_set in self.parent_widget_pairs(set([])):
            if isinstance(widget.layout, ColumnLayout):
                if not any(isinstance(parent.layout, Container) for parent in parents_set):
                    raise ProgrammerError(('%s does not have a parent with Layout of type %s.' % widget)+\
                      ' %s has a ColumnLayout, and thus needs to have an anchestor with a Container Layout.' % widget)



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


class _UnstyledHTMLFileInput(reahl.web.ui.SimpleFileInput):
    append_error = False
    add_default_attribute_source = False

    def __init__(self, form, bound_field):
        super(_UnstyledHTMLFileInput, self).__init__(form, bound_field)
        self.append_class('form-control-file')


class FileInputButton(reahl.web.ui.WrappedInput):
    """A single button which activated the browser's file choice dialog when clicked. The chosen file
       will be uploaded once the user clicks on any :class:`Button` associated with the same :class:`Form`
       as this Input.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param bound_field: (See :class:`~reahl.web.ui.Input`, must be of 
              type :class:`reahl.component.modelinterface.FileField`)
    """
    def __init__(self, form, bound_field):
        label = Label(form.view)
        self.simple_input = label.add_child(_UnstyledHTMLFileInput(form, bound_field))
        self.simple_input.html_representation.append_class('btn-secondary')
        label.add_child(Span(form.view, text=_('Choose file(s)')))
        super(FileInputButton, self).__init__(self.simple_input)
        self.add_child(label)

        label.append_class('reahl-bootstrapfileinputbutton')
        label.append_class('btn')
        label.append_class('btn-primary')
        self.set_html_representation(label)

    def get_js(self, context=None):
        js = ['$(".reahl-bootstrapfileinputbutton").bootstrapfileinputbutton({});']
        return super(FileInputButton, self).get_js(context=context) + js


class FileInput(reahl.web.ui.WrappedInput):
    """A visual combination of a two buttons and a status area. When the
    user clicks on the 'Choose file' button, the browser's file choice
    dialog is activated. Once chosen the file name that was chosen is
    shown in the status area. The last button will upload this file
    when clicked (it is automatically clicked is the user's JavaScript
    is enabled).

    :param form: (See :class:`~reahl.web.ui.Input`)
    :param bound_field: (See :class:`~reahl.web.ui.Input`, must be of 
           type :class:`reahl.component.modelinterface.FileField`)

    """
    def __init__(self, form, bound_field):
        file_input = FileInputButton(form, bound_field)
        super(FileInput, self).__init__(file_input)

        self.input_group = self.add_child(Div(self.view))
        self.input_group.append_class('input-group')
        self.input_group.append_class('reahl-bootstrapfileinput')
        self.set_html_representation(self.input_group)

        span = self.input_group.add_child(Span(form.view))
        span.append_class('input-group-btn')
        span.add_child(file_input)

        filename_input = self.input_group.add_child(Span(self.view, text=_('No files chosen')))
        filename_input.append_class('form-control')


    def get_js(self, context=None):
        js = ['$(".reahl-bootstrapfileinput").bootstrapfileinput({nfilesMessage: "%s", nofilesMessage: "%s"});' % \
              (_('files chosen'), _('No files chosen'))]
        return super(FileInput, self).get_js(context=context) + js



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


class Alert(Div):
    """A message box meant to alert the user of some message.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param message: The message to display inside the Alert.
    :keyword severity: One of 'success', 'info', 'warning', 'danger' to indicate the color scheme to be used for the Alert.

    """
    def __init__(self, view, message, severity='danger'):
        super(Alert, self).__init__(view)
        severity_option = HTMLAttributeValueOption(severity, severity, prefix='alert',
                                              constrain_value_to=['success', 'info', 'warning', 'danger'])
        self.add_child(TextNode(view, message))
        self.append_class('alert')
        self.append_class(severity_option.as_html_snippet())
        self.set_attribute('role', 'alert')


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


class Table(reahl.web.ui.Table):
    """Tabular data displayed as rows broken into columns.

       :param view: (See :class:`~reahl.web.fw.Widget`)
       :keyword caption_text: If text is given here, a caption will be added to the table containing the caption text.
       :keyword summary:  A textual summary of the contents of the table which is not displayed visually, \
                but may be used by a user agent for accessibility purposes.
       :keyword css_id: (See :class:`~reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, caption_text=None, summary=None, css_id=None):
        super(Table, self).__init__(view, caption_text=caption_text, summary=summary, css_id=css_id)
        self.append_class('table')


class HeadingTheme(HTMLAttributeValueOption):
    def __init__(self, name):
        super(HeadingTheme, self).__init__(name, name is not None, constrain_value_to=['inverse', 'default'])


class TableLayout(reahl.web.ui.Layout):
    """A Layout for customising details of hoe a Table is displayed.

    :keyword inverse: If True, table text is light text on dark background.
    :keyword border: If True, a border is rendered around the table and each cell.
    :keyword compact: If True, make the table more compact by cutting cell padding in half.
    :keyword striped: If True, colour successive rows lighter and darker.
    :keyword highlight_hovered: If True, a row is highlighted when the mouse hovers over it.
    :keyword transposed: If True, each row is displayed as a column instead, with its heading in the first cell.
    :keyword responsive: If True, the table will scroll horizontally on smaller devices.
    :keyword heading_theme: One of 'inverse' or 'default'. An inverse heading is one with light text on a darker background.
    """
    def __init__(self,
                  inverse=False, border=False, compact=False,
                  striped=False, highlight_hovered=False, transposed=False, responsive=False,
                  heading_theme=None):
        super(TableLayout, self).__init__()
        self.table_properties = [HTMLAttributeValueOption('inverse', inverse, prefix='table'),
                                 HTMLAttributeValueOption('striped', striped, prefix='table'),
                                 HTMLAttributeValueOption('bordered', border, prefix='table'),
                                 HTMLAttributeValueOption('hover', highlight_hovered, prefix='table'),
                                 HTMLAttributeValueOption('sm', compact, prefix='table'),
                                 HTMLAttributeValueOption('reflow', transposed, prefix='table'),
                                 HTMLAttributeValueOption('responsive', responsive, prefix='table')]
        self.heading_theme = HeadingTheme(heading_theme)

    def customise_widget(self):
        super(TableLayout, self).customise_widget()

        for table_property in self.table_properties:
            if table_property.is_set:
                self.widget.append_class(table_property.as_html_snippet())
        self.style_heading()

    def style_heading(self):
        if self.heading_theme.is_set:
            if not self.widget.thead:
                raise ProgrammerError('No Thead found on %s, but you asked to style is using heading_theme' % self.widget)
            self.widget.thead.append_class('thead-%s' % self.heading_theme)

