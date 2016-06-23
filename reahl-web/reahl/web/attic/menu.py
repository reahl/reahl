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

import re
import warnings
from babel import Locale, UnknownLocaleError

from reahl.component.decorators import deprecated
from reahl.component.eggs import ReahlEgg
from reahl.web.fw import Bookmark, Url, WebExecutionContext
from reahl.web.ui import A, HTMLWidget, Ul, Li, ActiveStateAttributes, TextNode
from reahl.web.attic.layout import HorizontalLayout, VerticalLayout


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.menu:MenuItem instead
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


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.menu:Menu instead
# Uses: reahl/web/reahl.menu.css
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


# Uses: reahl/web/reahl.hmenu.css
@deprecated('Please use Menu(view, layout=HorizontalLayout()) instead.', '3.1')
class HMenu(Menu):
    """A Menu, with items displayed next to each other.

       .. admonition:: Styling

          Rendered as a <ul class="reahl-menu reahl-horizontal">

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a_list: (See :class:`Menu`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, a_list, css_id=None):
        super(HMenu, self).__init__(view, a_list, css_id=css_id)
        self.use_layout(HorizontalLayout())


@deprecated('Please use Menu(view, layout=VerticalLayout()) instead.', '3.1')
class VMenu(Menu):
    """A Menu, with items displayed underneath each other.

       .. admonition:: Styling

          Rendered as a <ul class="reahl-menu reahl-vertical">

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param a_list: (See :class:`Menu`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, a_list, css_id=None):
        super(VMenu, self).__init__(view, a_list, css_id=css_id)
        self.use_layout(VerticalLayout())