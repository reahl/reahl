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

"""
.. versionadded:: 3.2

A Bootstrap "Nav" is a navigation menu: a list of items that are
links to other Views. Navs can also have a second level so that if you
click on an item, a dropdown list of vertically stacked options
appear.

This module contains the necessary Widgets and Layouts to create and
style Bootstrap Navs.


"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

import warnings, re

from babel import UnknownLocaleError, Locale

from reahl.component.eggs import ReahlEgg
from reahl.component.decorators import deprecated
from reahl.component.modelinterface import exposed, Field
from reahl.web.fw import Layout, Bookmark, Url, WebExecutionContext
from reahl.web.ui import AccessRightAttributes, ActiveStateAttributes, HTMLWidget
from reahl.web.bootstrap.ui import Div, Span, A, Ul, Li, TextNode

from reahl.component.exceptions import ProgrammerError



class Menu(HTMLWidget):
    add_reahl_styling = True
    """A visual menu that lists a number of Views to which the user can choose to go to.

       .. admonition:: Styling

          Rendered as a <ul class="reahl-menu"> element that contains a <li> for each MenuItem.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword a_list: (Deprecated) A list of :class:`A` instances to which each :class:`MenuItem` will lead.
       :keyword css_id: (Deprecated) (See :class:`reahl.web.ui.HTMLElement`)

       .. versionchanged:: 3.2
          Deprecated use of `a_list` and changed it temporarily to a keyword argument for backwards compatibility.
          Deprecated css_id keyword argument.
          Deprecated the `from_xxx` methods and added `with_xxx` replacements to be used after construction.
          Deprecated `add_item` and replaced it with `add_submenu`.
          Added a number of `add_xxx` methods for adding items from different sources.
    """
    def __init__(self, view, a_list=None, add_reahl_styling=None, css_id=None):
        super(Menu, self).__init__(view)
        if add_reahl_styling is not None:
            self.add_reahl_styling = add_reahl_styling
        self.menu_items = []
        self.create_html_representation()
        if css_id:
            warnings.warn('DEPRECATED: Passing a css_id upon construction. ' \
                          'Instead, please construct, supply a layout and THEN do .set_id().',
                          DeprecationWarning, stacklevel=2)
            self.set_id(css_id)
        if a_list is not None:
            warnings.warn('DEPRECATED: Passing an a_list upon construction. ' \
                          'Please construct, then use .with_a_list() instead.',
                          DeprecationWarning, stacklevel=2)
            self.with_a_list(a_list)

    @classmethod
    @deprecated('Please use :meth:`with_languages` instead on an already created instance.', '3.2')
    def from_languages(cls, view):
        """Constructs a Menu which contains a MenuItem for each locale supported by all the components
           in this application.

           :param view: (See :class:`reahl.web.fw.Widget`)
        """
        menu = cls(view)
        return menu.with_languages()

    @classmethod
    @deprecated('Please use :meth:`with_bookmarks` instead on an already created instance.', '3.2')
    def from_bookmarks(cls, view, bookmark_list):
        """Creates a Menu with a MenuItem for each Bookmark given in `bookmark_list`."""
        menu = cls(view)
        return menu.with_bookmarks(bookmark_list)


    def create_html_representation(self):
        ul = self.add_child(Ul(self.view))
        self.set_html_representation(ul)
        if self.add_reahl_styling:
            ul.append_class('reahl-menu')
        return ul

    def with_bookmarks(self, bookmark_list):
        """Populates this Menu with a MenuItem for each Bookmark given in `bookmark_list`.

           Answers the same Menu.

           .. versionadded: 3.2
        """
        for bookmark in bookmark_list:
            self.add_bookmark(bookmark)
        return self

    def with_languages(self):
        """Populates this Menu with a MenuItem for each available language.

           Answers the same Menu.

           .. versionadded: 3.2
        """
        current_url = Url.get_current_url()
        context = WebExecutionContext.get_context()
        supported_locales = ReahlEgg.get_languages_supported_by_all(context.config.reahlsystem.root_egg)
        for locale in supported_locales:
            try:
                language_name = Locale.parse(locale).display_name
            except UnknownLocaleError:
                language_name = locale

            bookmark = self.view.as_bookmark(description=language_name, locale=locale)
            bookmark.exact = True
            self.add_bookmark(bookmark)
        return self

    def with_a_list(self, a_list):
        """Populates this Menu with a MenuItem for each :class:`A` in `a_list`.

           Answers the same Menu.

           .. versionadded: 3.2
        """
        for a in a_list:
            self.add_a(a)
        return self

    def add_bookmark(self, bookmark):
        """Adds a MenuItem for the given :class:`Bookmark` to this Menu'.

           Answers the added MenuItem.

           .. versionadded: 3.2
        """
        return self.add_item(MenuItem.from_bookmark(self.view, bookmark))

    def add_a(self, a):
        """Adds an :class:`A` as a MenuItem.

           Answers the added MenuItem.

           .. versionadded: 3.2
        """
        return self.add_item(MenuItem(self.view, a))

    def add_item(self, item):
        """Adds MenuItem `item` to this Menu.

           .. versionchanged:: 3.2
              Deprecated adding submenus via this method. For sub menus, please use :meth:`add_submenu` instead.
        """
        self.menu_items.append(item)

        if isinstance(item, SubMenu):
            warnings.warn('DEPRECATED: calling add_item() with a SubMenu instance. Please use .add_submenu() instead.',
                          DeprecationWarning, stacklevel=2)
            item = self.add_html_for_submenu(item)
        else:
            self.add_html_for_item(item)
        return item

    def add_html_for_item(self, item):
        li = self.html_representation.add_child(Li(self.view))
        li.add_child(item.a)
        if self.add_reahl_styling:
            li.add_attribute_source(ActiveStateAttributes(item))
        item.widget = li
        return li

    def add_submenu(self, title, menu, query_arguments={}, **kwargs):
        """Adds 'menu` as a sub menu to this menu with the given `title`.

           Answers the added MenuItem.

           .. versionadded: 3.2
        """
        submenu = SubMenu(self.view, title, menu, query_arguments=query_arguments)
        self.menu_items.append(submenu)
        self.add_html_for_submenu(submenu, **kwargs)
        return submenu

    def add_html_for_submenu(self, submenu, add_dropdown_handle=False):
        li = self.add_html_for_item(submenu)
        if add_dropdown_handle:
            li.add_child(TextNode(self.view, '&nbsp;', html_escape=False))
            dropdown_handle = li.add_child(A(self.view, None, description='▼'))
            dropdown_handle.append_class('dropdown-handle')
        li.add_child(submenu.menu)
        submenu.widget = li
        return li


class MenuItem(object):
    """One item in a Menu.

       .. admonition:: Styling

          Rendered as a <li> element. When active, includes class="active".

       Normally, a programmer would not instantiate this class directly, rather use :meth:`MenuItem.from_bookmark`.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a: The :class:`A` to use as link.
       :keyword active_regex: If the href of `a` matches this regex, the MenuItem is deemed active.
       :keyword exact_match: (See :meth:`reahl.web.fw.Url.is_currently_active`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

       .. versionchanged:: 3.2
          Deprecated css_id keyword argument.
    """
    @classmethod
    def from_bookmark(cls, view, bookmark, active_regex=None):
        """Creates a MenuItem from a given Bookmark.

          :param view: (See :class:`reahl.web.fw.Widget`)
          :param bookmark: The :class:`reahl.web.fw.Bookmark` for which to create the MenuItem.
          :param active_regex: (See :class:`MenuItem`)
        """
        return cls(view, A.from_bookmark(view, bookmark), active_regex=active_regex, exact_match=bookmark.exact)

    def __init__(self, view, a, active_regex=None, exact_match=False, css_id=None):
        super(MenuItem, self).__init__()
        self.view = view
        self.exact_match = exact_match
        self.a = a
        self.widget = None
        self.active_regex = active_regex
        self.force_active = False
        self.is_active_callable = self.default_is_active
        if css_id:
            self.set_id(css_id)
            warnings.warn('DEPRECATED: Passing a css_id upon construction. ' \
                          'This ability will be removed in future versions.',
                          DeprecationWarning, stacklevel=2)

    def set_active(self):
        self.force_active = True

    def determine_is_active_using(self, is_active_callable):
        self.is_active_callable = is_active_callable

    @property
    def is_active(self):
        return self.is_active_callable()

    def default_is_active(self):
        if self.force_active:
            return True
        if not self.active_regex:
            return self.a.href and self.a.href.is_currently_active(exact_path=self.exact_match)
        return re.match(self.active_regex, self.view.relative_path)


class SubMenu(MenuItem):
    """A MenuItem that can contains another complete Menu itself.

       .. admonition:: Styling

          Rendered as a <li> element that contains a :class:`Menu` (see the latter for how it is rendered).

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text to use as a title for this SubMenu.
       :param menu: The :class:`Menu` contained inside this SubMenu.
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, title, menu, query_arguments={}, css_id=None):
        if query_arguments:
            a = A.from_bookmark(view, Bookmark.for_widget(title, query_arguments=query_arguments).on_view(view))
        else:
            a = A(view, None, description=title)
        super(SubMenu, self).__init__(view, a, css_id=css_id)
        self.title = title
        self.menu = menu



class Nav(Menu):
    """A Nav is a navigation menu, with items a user can click on to transition to 
    possibly different Views. Individual Items visually indicate whether they
    are active or disabled.

    .. note:: Don't be confused

       This, the :class:`reahl.web.bootstrap.navs.Nav` is not the same thing as a simple
       HTML-level :class:`reahl.web.bootstrap.ui.Nav`!

    :param view: (See :class:`~reahl.web.fw.Widget`)
    :keyword a_list: A list of :class:`~reahl.web.bootstrap.ui.A`\s representing the items.
    :keyword css_id: (See :class:`~reahl.web.ui.HTMLElement`)
    """
    add_reahl_styling = False

    def __init__(self, view, a_list=None, css_id=None):
        self.open_item = None
        super(Nav, self).__init__(view, a_list=None, css_id=None)

    @exposed
    def query_fields(self, fields):
        fields.open_item = Field(required=False, default=None)

    def create_html_representation(self):
        ul = super(Nav, self).create_html_representation()
        ul.append_class('nav')
        return ul
    
    def add_dropdown(self, title, dropdown_menu, drop_up=False, query_arguments={}):
        """Adds the dropdown_menu :class:`DropdownMenu` to this Nav. It appears as the
        top-level item with text `title`.

        :keyword drop_up: If True, the dropdown will drop upwards from its item, instead of down.
        :keyword query_arguments: (For internal use)
        """
        return self.add_submenu(title, dropdown_menu, extra_query_arguments=query_arguments, drop_up=drop_up)

    def add_html_for_item(self, item):
        li = super(Nav, self).add_html_for_item(item)
        li.append_class('nav-item')
        item.a.append_class('nav-link')
        item.a.add_attribute_source(ActiveStateAttributes(item, active_class='active'))
        item.a.add_attribute_source(AccessRightAttributes(item.a, disabled_class='disabled'))
        return li

    def add_submenu(self, title, menu, extra_query_arguments={}, **kwargs):
        if self.open_item == title:
            query_arguments={'open_item': ''}
        else:
            query_arguments={'open_item': title}
        query_arguments.update(extra_query_arguments)
        submenu = super(Nav, self).add_submenu(title, menu, query_arguments=query_arguments, **kwargs)
        return submenu
    
    def add_html_for_submenu(self, submenu, drop_up=False):
        li = super(Nav, self).add_html_for_submenu(submenu)
        if self.open_item == submenu.title:
            li.append_class('open')
        submenu.a.append_class('dropdown-toggle')
        submenu.a.set_attribute('data-toggle', 'dropdown')
        submenu.a.set_attribute('data-target', '-')
        submenu.a.add_child(Span(self.view)).append_class('caret')
        li.append_class('drop%s' % ('up' if drop_up else 'down'))
        return li



class NavLayout(Layout):
    def __init__(self, key=None, justified=False):
        super(NavLayout, self).__init__()
        self.justified = justified
        self.key = key

    @property
    def additional_css_class(self):
        return 'nav-%ss' % self.key

    def customise_widget(self):
        super(NavLayout, self).customise_widget()
        if self.key:
            self.widget.append_class(self.additional_css_class)
        if self.justified:
            self.widget.append_class('nav-justified')


class PillLayout(NavLayout):
    """This Layout makes a Nav appear as horizontally or vertically arranged pills (buttons).

    :keyword stacked: If True, the pills are stacked vertically.
    :keyword justified: If True, the pills are widened to fill all available space.
    """
    def __init__(self, stacked=False, justified=False):
        super(PillLayout, self).__init__(key='pill', justified=justified)
        if all([stacked, justified]):
            raise ProgrammerError('Pills must be stacked or justified, but not both')
        self.stacked = stacked
        self.justified = justified

    def customise_widget(self):
        super(PillLayout, self).customise_widget()
        if self.stacked:
            self.widget.append_class('nav-stacked')


class TabLayout(NavLayout):
    """This Layout makes a Nav appear as horizontal tabs.

    :keyword justified: If True, the tabs are widened to fill all available space.
    """
    def __init__(self, justified=False):
        super(TabLayout, self).__init__(key='tab', justified=justified)




class DropdownMenu(Menu):
    """A second-level menu that can be added to a Nav."""
    add_reahl_styling = False
    def create_html_representation(self):
        div = self.add_child(Div(self.view))
        self.set_html_representation(div)
        div.append_class('dropdown-menu')
        return div

    def add_html_for_item(self, item):
        self.html_representation.add_child(item.a)
        item.a.append_class('dropdown-item')
        item.a.add_attribute_source(ActiveStateAttributes(item, active_class='active'))
        item.a.add_attribute_source(AccessRightAttributes(item.a, disabled_class='disabled'))
        return item.a

    def add_submenu(self, menu, title):
        raise ProgrammerError('You cannot add a submenu to a %s.' % self.widget.__class__)



class DropdownMenuLayout(Layout):
    """Changes a DropdownMenu alignment.

    :keyword align_right: If True, align the dropdown to the right side of its parent item, else to the left.
    """
    def __init__(self, align_right=False):
        super(DropdownMenuLayout, self).__init__()
        self.align_right = align_right

    def customise_widget(self):
        if self.align_right:
            self.widget.append_class('dropdown-menu-right')

