# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
# -*- encoding: utf-8 -*-
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

from reahl.web.fw import Layout
from reahl.web.libraries import YuiGridsCss
from reahl.web.ui import FieldSet, Span, Label, Div, YuiUnit, YuiGrid, P, ButtonInput


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.layout:PriorityGroup instead
class PriorityGroup(object):
    """A PriorityGroup ensures that only one of the Widgets added to it has primary priority,
       the others in the group can have secondary priority, or no priority specified. This
       is used for styling Widgets based on their priority in the PriorityGroup.
    """
    def __init__(self):
        self.widgets = set()
        self.has_primary = False

    def add(self, widget):
        """Adds `widget`, with no priority set."""
        assert widget not in self.widgets, '%s is already added to %s' % (widget, self)
        self.widgets.add(widget)

    def add_secondary(self, widget):
        """Adds `widget`, with secondary priority."""
        self.add(widget)
        widget.set_priority(secondary=True)

    def add_primary(self, widget):
        """Adds `widget`, with primary priority."""
        assert not self.has_primary, 'Cannot add more than one widget as primary to %s' % self
        self.add(widget)
        widget.set_priority(primary=True)
        self.has_primary = True


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.layout:InputGroup
class InputGroup(FieldSet):
    __doc__ = FieldSet.__doc__


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.layout:LabelledInlineInput instead
# Uses: reahl/web/reahl.labelledinput.css
class LabelledInlineInput(Span):
    """A Widget that wraps around a given Input, adding a Label to the Input. Adheres to text flow.

       .. admonition:: Styling

          Rendered as a <span class="reahl-labelledinput"> containing the <label> followed by
          another <span> which contains the `html_input`. If the current input is not valid, it will also have
          class reahl-state-error.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    def __init__(self, html_input, css_id=None):
        view = html_input.view
        super(LabelledInlineInput, self).__init__(view, css_id=css_id)
        self.label = self.add_child(self.make_label(html_input))
        self.inner_span = self.add_child(Span(view))
        self.html_input = self.inner_span.add_child(html_input)

    def make_label(self, for_input):
        return Label(self.view, for_input=for_input)

    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(LabelledInlineInput, self).attributes
        attributes.add_to('class', ['reahl-labelledinput'])
        if self.html_input.get_input_status() == 'invalidly_entered':
            attributes.add_to('class', ['reahl-state-error'])
        return attributes


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.layout:LabelledBlockInput
# Uses: reahl/web/reahl.labelledinput.css
class LabelledBlockInput(Div):
    """A Widget that wraps around a given Input, adding a Label to the Input. Labels and their corresponding Inputs
       are arranged in columns. Successive LabelledBlockInputs are positioned underneath one another. This has the
       effect that the Labels and Inputs of successive LabelledBlockInputs line up.

       .. admonition:: Styling

          Rendered as a <div class="reahl-labelledinput"> containing two <div> elements: one with the Label
          in it, and the other with `html_input` itself. If the current input is not valid, it will also have
          class reahl-state-error.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    def __init__(self, html_input, css_id=None):
        view = html_input.view
        super(LabelledBlockInput, self).__init__(view, css_id=css_id)
        self.html_input = html_input

        if YuiGridsCss.is_enabled():
            self.append_class('yui-g')
            self.label_part = self.add_child(YuiUnit(view, first=True))
            self.input_part = self.add_child(YuiUnit(view))
        else:
            from reahl.web.pure import ColumnLayout, UnitSize
            self.use_layout(ColumnLayout(('label', UnitSize('1/4')), ('input', UnitSize('3/4'))))
            self.label_part = self.layout.columns['label']
            self.input_part = self.layout.columns['input']

        self.label = self.label_part.add_child(Label(self.view, for_input=html_input))
        self.input_part.add_child(html_input)

    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(LabelledBlockInput, self).attributes
        attributes.add_to('class', ['reahl-labelledinput'])
        if self.html_input.get_input_status() == 'invalidly_entered':
            attributes.add_to('class', ['reahl-state-error'])
        return attributes


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.layout:CueInput instead
# Uses: reahl/web/reahl.cueinput.js
class CueInput(Div):
    """A Widget that wraps around a given Input, adding a Label to the Input and a "cue" - a hint that
       appears only when the Input has focus. The intention of the cue is to give the user a hint as to
       what to input into the Input.

       Successive CueInputs are arranged underneath each other, with their labels, Inputs and Cue's lined up.

       .. admonition:: Styling

          Rendered as a <div class="reahl-cueinput reahl-labelledinput"> containing two <div> elements: one with the Label
          in it, and the other with two more <div> elements. The first of these contains the `html_input` itself. The
          last contains the `cue_widget`. If the current input is not valid, it will also have
          class reahl-state-error.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    def __init__(self, html_input, cue_widget, css_id=None):
        view = html_input.view
        super(CueInput, self).__init__(view, css_id=css_id)
        self.html_input = html_input

        if YuiGridsCss.is_enabled():
            self.append_class('yui-g')
            self.label_part = self.add_child(YuiUnit(view, first=True))
            self.input_wrapper = self.add_child(YuiGrid(view))
            self.input_part = self.input_wrapper.add_child(YuiUnit(view, first=True))
            self.cue_part = self.input_wrapper.add_child(YuiUnit(view))
        else:
            from reahl.web.pure import ColumnLayout, UnitSize
            self.use_layout(ColumnLayout(('label', UnitSize('1/4')), ('input', UnitSize('1/2')), ('cue', UnitSize('1/4'))))
            self.label_part = self.layout.columns['label']
            self.input_part = self.layout.columns['input']
            self.cue_part = self.layout.columns['cue']

        self.label = self.label_part.add_child(Label(self.view, for_input=html_input))
        self.input_part.add_child(self.html_input)
        self.cue_part.append_class('reahl-cue')
        self.cue_part.add_child(cue_widget)
        cue_widget.set_attribute('hidden', 'true')


    @property
    def visible(self):
        return self.html_input.visible

    @property
    def attributes(self):
        attributes = super(CueInput, self).attributes
        attributes.add_to('class', ['reahl-cueinput', 'reahl-labelledinput'])
        if self.html_input.get_input_status() == 'invalidly_entered':
            attributes.add_to('class', ['reahl-state-error'])
        return attributes

    def get_js(self, context=None):
        js = ['$(%s).cueinput();' % self.contextualise_selector('".reahl-cueinput"', context)]
        return super(CueInput, self).get_js(context=context) + js


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.layout:LabelOverInput instead
# Uses: reahl/web/reahl.labeloverinput.js
# Uses: reahl/web/reahl.labeloverinput.css
class LabelOverInput(LabelledInlineInput):
    """A :class:`LabelledInlineWidget` that shows the Label superimposed over the Input itself.
       The label is only visible while the Input is empty.

       .. admonition:: Styling

          Rendered like a :class:`LabelledInlineWidget` with reahl-labeloverinput appended to the class
          of the containing <div> element.

       :param html_input: (See :class:`InputLabel`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    @property
    def attributes(self):
        attributes = super(LabelOverInput, self).attributes
        attributes.add_to('class', ['reahl-labeloverinput'])
        return attributes

    def make_label(self, for_input):
        class AutoHideLabel(Label):
            @property
            def attributes(self):
                attributes = super(AutoHideLabel, self).attributes
                if self.for_input.value != '':
                    attributes.set_to('hidden', 'true')
                return attributes
        return AutoHideLabel(self.view, for_input=for_input)

    def get_js(self, context=None):
        js = ['$(%s).labeloverinput();' % self.contextualise_selector('".reahl-labeloverinput"', context)]
        return super(LabelOverInput, self).get_js(context=context) + js


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.menu:HorizontalLayout
class HorizontalLayout(Layout):
    """A Layout that causes Widgets to be displayed horizontally.

       .. admonition:: Styling

          Adds class reahl-horizontal to its Widget.

       (Only works for :class:`Menu` and subclasses.)

    """
    def customise_widget(self):
        super(HorizontalLayout, self).customise_widget()
        self.widget.html_representation.append_class('reahl-horizontal')


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.menu:VerticalLayout
class VerticalLayout(Layout):
    """A Layout that causes Widgets to be displayed vertically.

       .. admonition:: Styling

          Adds class reahl-vertical to its Widget.

       (Only works for :class:`Menu` and subclasses.)

    """
    def customise_widget(self):
        super(VerticalLayout, self).customise_widget()
        self.widget.html_representation.append_class('reahl-vertical')


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.layout:ErrorFeedbackMessage
class ErrorFeedbackMessage(P):
    """A user message indicating some error condition, such as a form validation which failed.

       .. admonition:: Styling

          Renders as an HTML <p class="error feedback"> element.
    """
    @property
    def attributes(self):
        attributes = super(ErrorFeedbackMessage, self).attributes
        attributes.add_to('class', ['error', 'feedback'])
        return attributes


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.layout:Button instead
class Button(Span):
    """A button.

       .. admonition:: Styling

          Represented in HTML by an <input type="submit"> element, wrapped in a <span class="reahl-button">.

       :param form: (See :class:`~reahl.web.ui.Input`)
       :param event: The :class:`~reahl.web.component.modelinterface.Event` that will fire when the user clicks on this ButtonInput.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, form, event, css_id=None):
        super(Button, self).__init__(form.view, css_id=css_id)
        self.html_input = self.add_child(ButtonInput(form, event))

    @property
    def attributes(self):
        attributes = super(Button, self).attributes
        attributes.add_to('class', ['reahl-button'])
        return attributes