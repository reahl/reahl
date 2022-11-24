# Copyright 2016-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

# noinspection PyUnresolvedReferences

from reahl.component.exceptions import arg_checks, IsInstance, ProgrammerError

from reahl.web.fw import Layout
from reahl.web.ui import Url, Widget, HTMLWidget, HTMLElement, HTMLAttributeValueOption
from reahl.component.i18n import Catalogue
from reahl.web.bootstrap.ui import Div, Nav, A, TextNode, Span
from reahl.web.bootstrap.forms import Form
import reahl.web.bootstrap.navs
from reahl.web.bootstrap.grid import Container, DeviceClass

_ = Catalogue('reahl-web')


class CollapseToggle(HTMLElement):
    def __init__(self, view, target_widget, text=None):
        super().__init__(view, 'button', children_allowed=True)
        self.set_attribute('type', 'button')

        self.target_widget = target_widget
        self.append_class('navbar-toggler')
        self.set_attribute('data-toggle', 'collapse')
        self.set_attribute('data-target', '#%s' % target_widget.css_id)
        self.set_attribute('aria-controls', '%s' % target_widget.css_id)
        self.set_attribute('aria-label', _('Toggle navigation'))

        if text is None:
            collapse_toggle_widget = Span(self.view)
            collapse_toggle_widget.append_class('navbar-toggler-icon')
        else:
            collapse_toggle_widget = TextNode(view, text)
        self.add_child(collapse_toggle_widget)


class NavbarFixed(HTMLAttributeValueOption):
    def __init__(self, fixed_to):
        super().__init__(fixed_to, fixed_to is not None, 
                                          prefix='', constrain_value_to=['fixed-top', 'fixed-bottom', 'sticky-top'])


class NavbarTogglerAlignment(HTMLAttributeValueOption):
    def __init__(self, alignment):
        super().__init__(alignment, alignment is not None,
                                                     prefix='navbar-toggler', constrain_value_to=['left', 'right'])


class ColourTheme(HTMLAttributeValueOption):
    def __init__(self, name):
        super().__init__(name, name is not None, 
                                          prefix='navbar', constrain_value_to=['light', 'dark'])


class BackgroundScheme(HTMLAttributeValueOption):
    def __init__(self, name):
        super().__init__(name, name is not None, 
                                               prefix='bg', constrain_value_to=['primary', 'dark', 'light'])


class NavbarLayout(Layout):
    """Used to populate a Navbar.

    :keyword fixed_to: May be one of 'top','bottom' or 'stickytop'.
                    The Navbar will stick to the top or bottom of the viewport.
    :keyword center_contents: If True, all the contents of the Navbar is centered within the Navbar itself.
    :keyword colour_theme: Use 'light' for use with light background colors, or 'dark' with dark background colors.
    :keyword bg_scheme: Whether the Navbar should use 'primary' colors, a 'dark' (light on dark) scheme
                        or a 'light' background.
    """
    def __init__(self, fixed_to=None, center_contents=False, colour_theme=None, bg_scheme=None):
        super().__init__()

        self.fixed = NavbarFixed(fixed_to)
        self.center_contents = center_contents
        self.colour_theme = ColourTheme(colour_theme)
        self.bg_scheme = BackgroundScheme(bg_scheme)
        self.brand = None
        self.toggle = None
        self.contents_container = None

    @property
    def nav(self):
        return self.widget.html_representation

    def customise_widget(self):
        super().customise_widget()
        if self.center_contents:
            centering_div = self.nav.add_child(Div(self.view).use_layout(Container()))
            self.contents_container = centering_div
        else:
            self.contents_container = self.nav
        self.main_container = self.contents_container

        if self.fixed.is_set:
            self.widget.append_class(self.fixed.as_html_snippet())

        for option in [self.colour_theme, self.bg_scheme]:
            if option.is_set:
                self.nav.append_class(option.as_html_snippet())

    def set_brand_text(self, brand_text):
        """Sets the brand to be a link to the home page that contains the given text.

        :param brand_text: Text to use for branding.
        """
        brand_a = A(self.view, Url('/'), description=brand_text)
        self.set_brand(brand_a)

    def insert_brand_widget(self, brand_html_element):
        index = 1 if self.toggle else 0
        self.main_container.insert_child(index, brand_html_element)

    @arg_checks(brand_html_element=IsInstance(HTMLWidget))
    def set_brand(self, brand_htmlwidget):
        """Sets `brand_widget` to be used as branding.

        :param brand_htmlwidget: An :class:`~reahl.web.ui.HTMLWidget` to be used as branding.
        """
        if self.brand:
            raise ProgrammerError('Brand has already been set to: %s' % self.brand)

        self.insert_brand_widget(brand_htmlwidget)
        brand_htmlwidget.append_class('navbar-brand')
        self.brand = brand_htmlwidget
        return self.brand

    @arg_checks(widget=IsInstance((reahl.web.bootstrap.navs.Nav, Form, TextNode)))
    def add(self, widget, left_aligned=False):
        """Adds the given Form or Nav `widget` to the Navbar.

        :param widget: A :class:`~reahl.web.bootstrap.navs.Nav`, :class:`~reahl.web.bootstrap.ui.Form` or
                       :class:`~reahl.web.bootstrap.ui.TextNode` to add.
        :keyword left_aligned: If True, render space to the right of widget. 

        .. versionchanged:: 6.1
           Added left_aligned keyword.
        """
        if isinstance(widget, reahl.web.bootstrap.navs.Nav):
            widget.append_class('navbar-nav')
        if isinstance(widget, Form):
            widget.append_class('form-inline')
        if isinstance(widget, TextNode):
            span = Span(self.view)
            span.add_child(widget)
            span.append_class('navbar-text')
            widget = span
        if left_aligned:
            widget.append_class('mr-auto')
        return self.contents_container.add_child(widget)

    def add_toggle(self, target_html_element, text=None, left_aligned=False):
        """Adds a link that toggles the display of the given `target_html_element`.

        :param target_html_element: A :class:`~reahl.web.ui.HTMLElement`
        :param text: Text to be used on the toggle link. If None, the boostrap navbar-toggler-icon is used
        :keyword left_aligned: If True, ensure that the toggle is to the far left.
        """
        if not target_html_element.css_id_is_set:
            raise ProgrammerError('%s has no css_id set. A toggle is required to have a css_id' % target_html_element)
        target_html_element.append_class('collapse')
        toggle = CollapseToggle(self.view, target_html_element, text=text)
        index = 1 if (self.brand and not left_aligned) else 0
        self.main_container.insert_child(index, toggle)

        self.toggle = toggle
        return toggle


class ResponsiveLayout(NavbarLayout):
    """Makes the Navbar responsive and collapseable depending on the device.


    :param collapse_below_device_class: Which device class should trigger responsive collapsing.
                                        Valid values: xs, sm, md, lg, xl
    :keyword center_contents: If True, all the contents of the Navbar is centered within the Navbar itself.
    :keyword fixed_to: May be one of 'fixed-top','fixed-bottom' or 'sticky-top'.
                    The Navbar will stick to the top or bottom of the viewport.
    :keyword align_toggle_left: If True align the toggle on the left (the default is to align it right).
    :keyword collapse_brand_with_content: When set to True, the brand should collapse with the content.
    :keyword colour_theme: Use 'light' for use with light background colors, or 'dark' with dark background colors.
    :keyword bg_scheme: Whether the Navbar should use 'primary' colors, a 'dark' (light on dark) scheme
                        or a 'light' background.
    :keyword text: Text to be used on the toggle link. If None, the boostrap navbar-toggler-icon is used.

    """
    def __init__(self, collapse_below_device_class, center_contents=False, fixed_to=None, align_toggle_left=False,
                 collapse_brand_with_content=False,
                 colour_theme=None, bg_scheme=None, text=None):
        super().__init__(fixed_to=fixed_to, center_contents=center_contents,
                                               colour_theme=colour_theme, bg_scheme=bg_scheme)
        self.collapse_below_device_class = DeviceClass(collapse_below_device_class)
        self.collapse_brand_with_content = collapse_brand_with_content
        self.align_toggle_left = align_toggle_left
        if not self.collapse_below_device_class.one_smaller:
            raise ProgrammerError(('There is no device class smaller than %s' %
                                   self.collapse_below_device_class) +
                                  ' It does not make sense to collapse only '
                                  'if the viewport is smaller than the smallest device')
        self.text = text
        self.collapsing_content = None

    def insert_brand_widget(self, brand_html_element):
        if self.collapse_brand_with_content:
            self.collapsing_content.insert_child(0, brand_html_element)
        else:
            # getting in here also means self.contents_container is NOT the centering_div as it would be in the other leg
            if self.align_toggle_left:
                super().insert_brand_widget(brand_html_element)
            else:
                self.main_container.insert_child(0, brand_html_element)


    def customise_widget(self):
        super().customise_widget()
        if not self.widget.css_id_is_set:
            raise ProgrammerError('%s has no css_id set. A %s can only be used with a Widget that has a css_id' %
                                  (self.widget, self.__class__))

        collapsing_content = Div(self.view, css_id='%s_collapsable' % self.widget.css_id)
        collapsing_content.append_class('navbar-collapse')
        self.collapsing_content = collapsing_content
        self.contents_container.add_child(collapsing_content)
        self.contents_container = collapsing_content

        self.add_toggle(collapsing_content, text=self.text, left_aligned=self.align_toggle_left)

        toggle_size = self.collapse_below_device_class.one_smaller
        self.nav.append_class('navbar-expand-%s' % toggle_size.name)



class Navbar(HTMLWidget):
    """A bootstrap Navbar can be used as page header in a web
    application. A Navbar can contain some branding text, a
    :class:`~reahl.web.bootstrap.navs.Nav` and a small
    :class:`~reahl.web.bootstrap.forms.Form`.

    You populate a Navbar using a NavbarLayout for complete control
    over how the Navbar is laid out, which of its possible elements 
    are present and how they are composed themselves.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :keyword css_id: (See :class:`reahl.web.fw.Widget`)
    """
    def __init__(self, view, css_id=None):
        super().__init__(view)

        self.navbar = self.add_child(Nav(view))
        self.navbar.append_class('navbar')
        self.set_html_representation(self.navbar)
        if css_id:
            self.set_id(css_id)
