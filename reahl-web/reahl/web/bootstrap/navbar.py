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

""".. versionadded:: 3.2

A Bootstrap Navbar is a header for a web application with all manner
of useful content, including a navigation menu.

"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

from reahl.component.exceptions import arg_checks, IsInstance, ProgrammerError

from reahl.web.fw import Layout
from reahl.web.ui import Url, HTMLElement, HTMLWidget, HTMLAttributeValueOption
from reahl.web.bootstrap.ui import Div, Nav, A, TextNode
from reahl.web.bootstrap.forms import Form
import reahl.web.bootstrap.navs
from reahl.web.bootstrap.grid import Container, DeviceClass


class CollapseToggle(HTMLElement):
    def __init__(self, view, target_widget, text=None, hide_for_size=None):
        text = text or '☰'

        super(CollapseToggle, self).__init__(view, 'button', children_allowed=True)
        self.set_attribute('type', 'button')

        self.target_widget = target_widget
        self.append_class('navbar-toggler')
        self.set_attribute('data-toggle', 'collapse')
        self.set_attribute('data-target', '#%s' % target_widget.css_id)
        if hide_for_size:
            self.append_class('hidden-%s-up' % hide_for_size.class_label)

        self.add_child(TextNode(view, text))


class ResponsivePull(HTMLAttributeValueOption):
    def __init__(self, side, device_class):
        is_set = True if device_class else False
        self.device_class_label = device_class if (is_set and device_class is not True) else None
        super(ResponsivePull, self).__init__(side, is_set, prefix='pull')

    @property
    def side(self):
        return self.option_string

    def as_html_snippet(self):
        if self.device_class_label:
            return '-'.join([self.prefix, self.device_class_label, self.side])
        return super(ResponsivePull, self).as_html_snippet()


class ResponsiveFloat(Layout):
    def __init__(self, left=None, right=None):
        super(ResponsiveFloat, self).__init__()
        if left and right:
            raise ProgrammerError('Both left= and right= have been given. Specify left or right, not both.')

        self.left = ResponsivePull('left', left)
        self.right = ResponsivePull('right', right)

    def customise_widget(self):
        super(ResponsiveFloat, self).customise_widget()
        for responsive_pull in [self.left, self.right]:
            if responsive_pull.is_set:
                self.widget.append_class(responsive_pull.as_html_snippet())


class NavbarFixed(HTMLAttributeValueOption):
    def __init__(self, fixed_to):
        super(NavbarFixed, self).__init__(fixed_to, fixed_to is not None, 
                                          prefix='navbar-fixed', constrain_value_to=['top', 'bottom'])

class ColourTheme(HTMLAttributeValueOption):
    def __init__(self, name):
        super(ColourTheme, self).__init__(name, name is not None, 
                                          prefix='navbar', constrain_value_to=['light', 'dark'])

class BackgroundScheme(HTMLAttributeValueOption):
    def __init__(self, name):
        super(BackgroundScheme, self).__init__(name, name is not None, 
                                               prefix='bg', constrain_value_to=['primary', 'inverse', 'faded']) 

class NavbarLayout(Layout):
    """Used to populate a Navbar.

    :keyword fixed_to: If one of 'top' or 'bottom', the Navbar will stick to the top or bottom of the viewport.
    :keyword full: If True, the Navbar fills the available width.
    :keyword center_contents: If True, all the contents of the Navbar is centered within the Navbar itself.
    :keyword colour_theme: Whether the Navbar has a 'dark' or 'light' background.
    :keyword bg_scheme: Whether the Navbar should use 'primary' colors, an 'inverse' (light on dark) scheme or a 'faded' background.
    """
    def __init__(self, fixed_to=None, full=False, center_contents=False, colour_theme=None, bg_scheme=None):
        super(NavbarLayout, self).__init__()
        if fixed_to and full:
            raise ProgrammerError('Both fixed_to and full are given. Give fixed_to or full, but not both')
        
        self.fixed = NavbarFixed(fixed_to)
        self.full = HTMLAttributeValueOption('navbar-full', full)
        self.center_contents = center_contents
        self.colour_theme = ColourTheme(colour_theme)
        self.bg_scheme = BackgroundScheme(bg_scheme)
        self.brand = None
        self.contents_container = None

    def customise_widget(self):
        super(NavbarLayout, self).customise_widget()
        nav = self.widget.html_representation
        if self.center_contents:
            centering_div = nav.add_child(Div(self.view).use_layout(Container()))
            self.contents_container = centering_div
        else:
            self.contents_container = nav

        for option in [self.fixed, self.full]:
            if option.is_set:
                self.widget.append_class(option.as_html_snippet())
            
        for option in [self.colour_theme, self.bg_scheme]:
            if option.is_set:
                nav.append_class(option.as_html_snippet())

    def set_brand_text(self, brand_text):
        """Sets the brand to be a link to the home page that contains the given text.

        :param brand_text: Text to use for branding.
        """
        brand_a = A(self.view, Url('/#'), description=brand_text)
        self.set_brand(brand_a)

    @arg_checks(brand_html_element=IsInstance(HTMLElement))
    def set_brand(self, brand_html_element):
        """Sets `brand_html_element` to be used as branding.

        :param brand_html_element: An :class:`~reahl.web.ui.HTMLElement` to be used as branding.
        """
        if self.brand:
            raise ProgrammerError('Brand has already been set to: %s' % self.brand)

        self.contents_container.insert_child(0, brand_html_element)
        brand_html_element.append_class('navbar-brand')
        self.brand = brand_html_element

    @arg_checks(widget=IsInstance((reahl.web.bootstrap.navs.Nav, Form)))
    def add(self, widget, left=None, right=None):
        """Adds the given Form or Nav `widget` to the Navbar.

        :param widget: A :class:`~reahl.web.bootstrap.navs.Nav` or :class:`~reahl.web.bootstrap.ui.Form` to add.
        :keyword left: If True, `widget` is aligned to the left of the Navbar.
        :keyword right: If True, `widget` is aligned to the right of the Navbar.
        """
        if isinstance(widget, reahl.web.bootstrap.navs.Nav):
            widget.append_class('navbar-nav')
        if left or right:
            child = Div(self.view).use_layout(ResponsiveFloat(left=left, right=right))
            child.add_child(widget)
        else:
            child = widget
        self.contents_container.add_child(child)
        return widget

    def add_toggle(self, target_html_element, text=None):
        """Adds a link that toggles the display of the given `target_html_element`.

        :param target_html_element: A :class:`~reahl.web.ui.HTMLElement`
        :keyword text: Text to be used on the toggle link.
        """
        if not target_html_element.css_id_is_set:
            raise ProgrammerError('%s has no css_id set. A toggle is required to have a css_id' % target_html_element)
        target_html_element.append_class('collapse')
        toggle = CollapseToggle(self.view, target_html_element, text=text)
        self.contents_container.add_child(toggle)
        return toggle


class ResponsiveLayout(NavbarLayout):
    def __init__(self, collapse_below_device_class, fixed_to=None, full=False, center_contents=False, colour_theme=None, bg_scheme=None, text=None):
        super(ResponsiveLayout, self).__init__(fixed_to=fixed_to, full=full, center_contents=center_contents, colour_theme=colour_theme, bg_scheme=bg_scheme)
        self.collapse_below_device_class = DeviceClass(collapse_below_device_class)
        if not self.collapse_below_device_class.one_smaller:
            raise ProgrammerError(('There is no device class smaller than %s' % self.collapse_below_device_class)+\
                                  ' It does not make sense to collapse only if the viewport is smaller than the smallest device')
        self.text = text

    def customise_widget(self):
        super(ResponsiveLayout, self).customise_widget()
        if not self.widget.css_id_is_set:
            raise ProgrammerError('%s has no css_id set. A %s can only be used with a Widget that has a css_id' % \
                                (self.widget, self.__class__))

        collapsable = Div(self.view, css_id='%s_collapsable' % self.widget.css_id)
        collapsable.append_class('collapse')
        toggle_widget = CollapseToggle(self.view, collapsable, text=self.text, hide_for_size=self.collapse_below_device_class)
        toggle_size = self.collapse_below_device_class.one_smaller
        collapsable.append_class('navbar-toggleable-%s' % toggle_size.class_label)
        
        self.contents_container.add_child(toggle_widget)
        self.contents_container.add_child(collapsable)
        self.contents_container = collapsable


class Navbar(HTMLWidget):
    """A bootstrap Navbar can be used as page header in a web
    application. A Navbar can contain some branding text, a
    :class:`~reahl.web.bootstrap.navs.Nav` and a small
    :class:`~reahl.web.bootstrap.ui.Form`.

    You populate a Navbar using a NavbarLayout for complete control
    over how the Navbar is laid out, which of its possible elements 
    are present and how they are composed themselves.

    :param view: (See :class:`reahl.web.fw.Widget`)
    """
    def __init__(self, view):
        super(Navbar, self).__init__(view)

        self.navbar = self.add_child(Nav(view))
        self.navbar.append_class('navbar')
        self.set_html_representation(self.navbar)





