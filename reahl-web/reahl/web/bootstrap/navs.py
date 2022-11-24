# Copyright 2015-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


.. versionchanged:: 4.0
   Moved Menu here from reahl.web.ui.

.. versionchanged:: 4.0
   Removed the .add_item and add_submenu methods in favour of .add_a,.add_bookmark,.add_dropdown methods.

"""


import re

from babel import UnknownLocaleError, Locale

from reahl.component.eggs import ReahlEgg
from reahl.component.exceptions import ProgrammerError
from reahl.component.modelinterface import ExposedNames, Field
from reahl.component.context import ExecutionContext
from reahl.web.fw import Layout, Bookmark, Url
from reahl.web.ui import AccessRightAttributes, ActiveStateAttributes, HTMLWidget, HTMLAttributeValueOption
from reahl.web.bootstrap.ui import Div, Span, A, Ul, Li, H


class Menu(HTMLWidget):
    """A visual menu that lists a number of Views to which the user can choose to go to.

       .. admonition:: Styling

          Rendered as a <ul class="reahl-menu"> element that contains a <li> for each MenuItem.

       :param view: (See :class:`reahl.web.fw.Widget`)

       .. versionchanged:: 3.2
          Deprecated use of `a_list` and changed it temporarily to a keyword argument for backwards compatibility.

       .. versionchanged:: 3.2
          Deprecated css_id keyword argument.

       .. versionchanged:: 3.2
          Deprecated the `from_xxx` methods and added `with_xxx` replacements to be used after construction.

       .. versionchanged:: 3.2
          Deprecated `add_item` and replaced it with `add_submenu`.

       .. versionchanged:: 3.2
          Added a number of `add_xxx` methods for adding items from different sources.

       .. versionchanged:: 4.0
          Removed deprecated a_list and css_id
    """
    def __init__(self, view):
        super().__init__(view)
        self.menu_items = []
        self.create_html_representation()

    def create_html_representation(self):
        ul = self.add_child(Ul(self.view))
        self.set_html_representation(ul)
        ul.append_class('reahl-menu')
        return ul

    def with_bookmarks(self, bookmark_list):
        """Populates this Menu with a MenuItem for each Bookmark given in `bookmark_list`.

           Answers the same Menu.

           .. versionadded:: 3.2
        """
        for bookmark in bookmark_list:
            self.add_bookmark(bookmark)
        return self

    def with_languages(self):
        """Populates this Menu with a MenuItem for each available language.

           Answers the same Menu.

           .. versionadded:: 3.2
        """
        context = ExecutionContext.get_context()
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

           .. versionadded:: 3.2
        """
        for a in a_list:
            self.add_a(a)
        return self

    def add_bookmark(self, bookmark, active_regex=None):
        """Adds a MenuItem for the given :class:`Bookmark` to this Menu'.

           Answers the added MenuItem.

           .. versionadded:: 3.2
        """
        return self.add_a(A.from_bookmark(self.view, bookmark), active_regex=active_regex, exact_match=bookmark.exact)

    def add_a(self, a, active_regex=None, exact_match=None):
        """Adds an :class:`A` as a MenuItem.

           Answers the added MenuItem.

           .. versionadded:: 3.2
        """
        menu_item = MenuItem(self.view, a, active_regex=active_regex, exact_match=exact_match)
        self.menu_items.append(menu_item)
        self.add_html_for_item(menu_item)
        return menu_item

    def add_html_for_item(self, item):
        li = self.html_representation.add_child(Li(self.view))
        li.add_child(item.a)
        item.set_html_representation(li)
        return li


class MenuItem(HTMLWidget):
    """One item in a Menu. Different kinds of Menu render their items differently.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a: The :class:`A` to use as link.
       :keyword active_regex: If the href of `a` matches this regex, the MenuItem is deemed active.
       :keyword exact_match: (See :meth:`reahl.web.fw.Url.is_currently_active`)

       .. versionchanged:: 4.0
          Removed from_bookmark and css_id keyword argument.
    """
    def __init__(self, view, a, active_regex=None, exact_match=False):
        super().__init__(view)
        self.view = view
        self.exact_match = exact_match
        self.a = a
        self.active_regex = active_regex
        self.force_active = False
        self.is_active_callable = self.default_is_active

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


class Nav(Menu):
    """A Nav is a navigation menu, with items a user can click on to transition to 
    possibly different Views. Individual Items visually indicate whether they
    are active or disabled.

    .. note:: Don't be confused

       This, the :class:`reahl.web.bootstrap.navs.Nav` is not the same thing as a simple
       HTML-level :class:`reahl.web.bootstrap.ui.Nav`!

    :param view: (See :class:`~reahl.web.fw.Widget`)
    """
    def __init__(self, view):
        self.open_item = None
        super().__init__(view)

    query_fields = ExposedNames()
    query_fields.open_item = lambda i: Field(required=False, default=None)

    def create_html_representation(self):
        ul = super().create_html_representation()
        ul.append_class('nav')
        return ul
    
    def add_dropdown(self, title, dropdown_menu, drop_position='down', query_arguments={}):
        """Adds the dropdown_menu :class:`DropdownMenu` to this Nav. It appears as the
        top-level item with text `title`.

        :keyword drop_position: Position relative to the item where the dropdown should appear ('up', 'down', 'left' or 'right').
        :keyword query_arguments: (For internal use)
        """
        if self.open_item == title:
            extra_query_arguments = {'open_item': ''}
        else:
            extra_query_arguments = {'open_item': title}
        extra_query_arguments.update(query_arguments)

        bookmark = Bookmark.for_widget(title, query_arguments=extra_query_arguments).on_view(self.view)
        submenu = MenuItem(self.view, A.from_bookmark(self.view, bookmark))
        self.menu_items.append(submenu)

        li = self.add_html_for_item(submenu)
        li.add_child(dropdown_menu)

        if self.open_item == title:
            li.append_class('show')
        submenu.a.append_class('dropdown-toggle')
        submenu.a.set_attribute('data-toggle', 'dropdown')
        submenu.a.set_attribute('role', 'button')
        submenu.a.set_attribute('aria-haspopup', 'true')
        # submenu.a.set_attribute('aria-expanded', 'true') #FYI no need to set this this as it is handled by bootstrap js

        li.append_class(DropdownMenuPosition(drop_position).as_html_snippet())
        return submenu

    def add_html_for_item(self, item):
        li = super().add_html_for_item(item)
        li.append_class('nav-item')
        item.a.append_class('nav-link')
        item.a.add_attribute_source(ActiveStateAttributes(item, active_value='active'))
        item.a.add_attribute_source(AccessRightAttributes(item.a, disabled_class='disabled'))
        return li


class DropdownMenuPosition(HTMLAttributeValueOption):
    def __init__(self, name):
        super().__init__(name, True, prefix='drop', delimiter='',
                                                   constrain_value_to=['up', 'down', 'left', 'right'])


class ContentAlignment(HTMLAttributeValueOption):
    valid_options = ['center', 'end']
    def __init__(self, name):
        super().__init__(name, name is not None, prefix='justify-content',
                                                   constrain_value_to=self.valid_options)


class ContentJustification(HTMLAttributeValueOption):
    valid_options = ['fill', 'justified']

    def __init__(self, name):
        super().__init__(name, name is not None, prefix='nav',
                                                   constrain_value_to=self.valid_options)


class NavLayout(Layout):
    def __init__(self, key=None, content_alignment=None, content_justification=None):
        super().__init__()
        if content_alignment and content_justification:
            raise ProgrammerError('Cannot set content_alignment and content_justfication at the same time')
        self.content_alignment = ContentAlignment(content_alignment)
        self.content_justification = ContentJustification(content_justification)
        self.key = key

    @property
    def additional_css_class(self):
        return 'nav-%ss' % self.key

    def customise_widget(self):
        super().customise_widget()
        if self.key:
            self.widget.append_class(self.additional_css_class)
            self.widget.set_attribute('role', 'tablist')
        if self.content_alignment.is_set:
            self.widget.append_class(self.content_alignment.as_html_snippet())
        if self.content_justification.is_set:
            self.widget.append_class(self.content_justification.as_html_snippet())


class PillLayout(NavLayout):
    """This Layout makes a Nav appear as horizontally or vertically arranged pills (buttons).

    :keyword stacked: If True, the pills are stacked vertically.
    :keyword content_alignment: If given, changes how content is aligned inside the Nav (default is start)
                                (One of: center, end)
    :keyword content_justification: If given, makes the content take up all space in the Nav. Either with elements having equal space (fill), or unequal space (justified)
                                (One of: fill, justified)

    """
    def __init__(self, stacked=False, content_alignment=None, content_justification=None):
        super().__init__(key='pill', content_alignment=content_alignment, content_justification=content_justification)
        if all([stacked, content_alignment or content_justification]):
            raise ProgrammerError('Pills must be stacked, aligned or justified, but you cannot give all options together')
        self.stacked = stacked

    def customise_widget(self):
        super().customise_widget()
        if self.stacked:
            self.widget.append_class('flex-column')


class TabLayout(NavLayout):
    """This Layout makes a Nav appear as horizontal tabs.

    :keyword content_alignment: If given, changes how content is aligned inside the Nav (default is start)
                                (One of: center, end)
    :keyword content_justification: If given, makes the content take up all space in the Nav. Either with elements having equal space (fill), or unequal space (justified)
                                (One of: fill, justified)
    """
    def __init__(self, content_alignment=None, content_justification=None):
        super().__init__(key='tab', content_alignment=content_alignment, content_justification=content_justification)


class DropdownMenu(Menu):
    """A second-level menu that can be added to a Nav."""
    def create_html_representation(self):
        div = self.add_child(Div(self.view))
        self.set_html_representation(div)
        div.append_class('dropdown-menu')
        return div

    def add_html_for_item(self, item):
        self.html_representation.add_child(item.a)
        item.a.append_class('dropdown-item')
        item.a.add_attribute_source(ActiveStateAttributes(item, active_value='active'))
        item.a.add_attribute_source(AccessRightAttributes(item.a, disabled_class='disabled'))
        item.set_html_representation(item.a)
        return item.a

    def add_form(self, form):
        self.html_representation.add_child(form)
        form.append_class('px-4') #padding/margin
        form.append_class('py-3') #padding/margin
        return form

    def add_header(self, header):
        self.html_representation.add_child(header)
        header.append_class('dropdown-header')
        return header

    def add_divider(self):
        divider = self.html_representation.add_child(Div(self.view))
        divider.append_class('dropdown-divider')
        return divider


class DropdownMenuLayout(Layout):
    """Changes a DropdownMenu alignment.

    :keyword align_right: If True, align the dropdown to the right side of its parent item, else to the left.
    """
    def __init__(self, align_right=False):
        super().__init__()
        self.align_right = align_right

    def customise_widget(self):
        if self.align_right:
            self.widget.append_class('dropdown-menu-right')

