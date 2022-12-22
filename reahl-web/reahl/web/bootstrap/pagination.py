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

Sometimes you need to display a long list of items. Displaying such a list on a single
page is not a good idea, because the page will take forever to load.

This module provides a few classes you can use to build a single View that displays
only one "pageful" of the list. You can then also include a :class:`PageMenu` -- a
menu on which a user can choose to navigate to another section (or page) of the list.



"""


from functools import partial
from abc import ABCMeta, abstractmethod

from reahl.component.i18n import Catalogue
from reahl.component.modelinterface import ExposedNames, IntegerField
from reahl.component.decorators import memoized
from reahl.web.fw import Bookmark
from reahl.web.ui import AccessRightAttributes, ActiveStateAttributes, HTMLWidget
from reahl.web.bootstrap.ui import A, Span, Div
from reahl.web.bootstrap.navs import Menu

_ = Catalogue('reahl-web')


class PageIndexProtocol(object, metaclass=ABCMeta):
    @property
    @abstractmethod
    def pages_in_range(self): pass
    @property
    @abstractmethod
    def current_page(self): pass
    @property
    @abstractmethod
    def start_page(self): pass
    @property
    @abstractmethod
    def end_page(self): pass
    @property
    @abstractmethod
    def previous_page(self): pass
    @property
    @abstractmethod
    def next_page(self): pass
    @property
    @abstractmethod
    def last_page(self): pass
    @property
    @abstractmethod
    def has_next_page(self): pass
    @property
    @abstractmethod
    def has_previous_page(self): pass


class PagedPanel(Div):
    """A :class:`Div` whose contents change, depending on the page selected by a user from a :class:`PageMenu`.
       A programmer should subclass from PagedPanel, supplying an `__init__` method which populates the PagedPanel
       with appropriate contents, based on its `.current_contents`.

       .. admonition:: Styling

          Represented in HTML by an <div> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param page_index: The :class:`PageIndex` to use to supply contents to the pages displayed by this PagedPanel.
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
    """
    def __init__(self, view, page_index, css_id):
        self.page_index = page_index
        super().__init__(view, css_id=css_id)
        self.enable_refresh()

    def get_bookmark(self, description=None, page_number=1):
        return Bookmark.for_widget(description or '%s' % page_number,
                                   query_arguments={'current_page_number': page_number}).on_view(self.view)

    query_fields = ExposedNames()
    query_fields.current_page_number = lambda i: i.page_index.fields.current_page_number

    @property
    def current_contents(self):
        """The list of items that should be displayed for the current page."""
        return self.page_index.current_page.contents


class Page:
    def __init__(self, number, description, contents_getter):
        self.number = number
        self.description = description
        self.contents_getter = contents_getter

    @property
    def contents(self):
        return self.contents_getter()


class PageIndex(PageIndexProtocol):
    """An object responsible for breaking a long list of items up into shorter lists for display. Each such
       shorter list is referred to as a page. Different ways of breaking long lists into smaller lists
       are provided by subclasses.

       :keyword current_page_number: The initial page shown to users.
       :keyword start_page_number: The first page that should be listed in the current :class:`PageMenu`.
       :keyword max_page_links: The number of pages to be shown in the current :class:`PageMenu`.
    """
    def __init__(self, current_page_number=1, start_page_number=1, max_page_links=5):
        super().__init__()
        self.current_page_number = current_page_number
        self.start_page_number = start_page_number
        self.max_page_links = max_page_links

    fields = ExposedNames()
    fields.current_page_number = lambda i: IntegerField(required=False, default=1)
    fields.start_page_number =   lambda i: IntegerField(required=False, default=1)

    @abstractmethod
    def get_contents_for_page(self, page_number):
        """Override this method in subclasses to obtain the correct list of items for the given `page_number`."""

    @property
    @abstractmethod
    def total_number_of_pages(self):
        """Override this @property in subclasses to state what the total number of pages is."""

    def get_description_for_page(self, page_number):
        return str(page_number)

    @property
    @memoized
    def current_page(self):
        return self.get_page_number(self.current_page_number)

    def get_page_number(self, page_number):
        return Page(page_number, self.get_description_for_page(page_number), partial(self.get_contents_for_page, page_number))

    @property
    @memoized
    def pages_in_range(self):
        return [self.get_page_number(page_number)
                for page_number in list(range(self.start_page_number, self.end_page.number+1))]

    @property
    @memoized
    def start_page(self):
        return self.get_page_number(self.start_page_number)

    @property
    @memoized
    def end_page(self):
        page_number = self.start_page_number+min(self.max_page_links-1, self.total_number_of_pages-self.start_page_number)
        return self.get_page_number(page_number)

    @property
    @memoized
    def previous_page(self):
        page_number = max(1, self.start_page_number - self.max_page_links)
        return self.get_page_number(page_number)

    @property
    @memoized
    def next_page(self):
        page_number = min(self.end_page.number + 1, self.total_number_of_pages)
        return self.get_page_number(page_number)

    @property
    @memoized
    def last_page(self):
        page_number =  max(self.total_number_of_pages - self.max_page_links + 1, 1)
        return self.get_page_number(page_number)

    @property
    @memoized
    def has_next_page(self):
        return self.end_page.number < self.total_number_of_pages

    @property
    @memoized
    def has_previous_page(self):
        return self.start_page_number > 1


class SequentialPageIndex(PageIndex):
    """A PageIndex that breaks a list of items up into smaller lists, by cutting the original list
           into sections that have a maximum number of items per page.

           :param items: The long list of items.
           :keyword items_per_page: The maximum number of items to allow on a page.
           :keyword current_page_number: (See :class:`PageIndex`)
           :keyword start_page_number: (See :class:`PageIndex`)
           :keyword max_page_links: (See :class:`PageIndex`)
        """
    def __init__(self, items, items_per_page=5, current_page_number=1, start_page_number=1, max_page_links=4):
        super().__init__(current_page_number=current_page_number,
                                                  start_page_number=start_page_number,
                                                  max_page_links=max_page_links)
        self.items = items
        self.items_per_page = items_per_page

    def get_contents_for_page(self, page_number):
        range_start = (page_number-1)*self.items_per_page
        range_end = range_start+min(self.items_per_page, len(self.items)-range_start)-1
        return self.items[range_start:range_end+1]

    @property
    @memoized
    def total_number_of_pages(self):
        return ((len(self.items)-1) // self.items_per_page)+1


class AnnualItemOrganiserProtocol(object, metaclass=ABCMeta):
    """Manages a list of items, each of which is seen to be for a particular year.
    """
    @abstractmethod
    def get_years(self):
        """Returns a list of integers, each representing a year which is applicable to at least one item in a list of items."""

    @abstractmethod
    def get_items_for_year(self, year):
        """Returns a list if items to which `year` (an integer) is applicable."""


class AnnualPageIndex(PageIndex):
    """A PageIndex that breaks a list of items up into smaller lists, by arranging all items
       that have the same year on the same page.

       :param annual_item_organiser: An object that implements :class:`AnnualItemOrganiserProtocol`. Its methods
                                     will be called to find the relevent items, or determine what years are applicable.
       :keyword current_page_number: (See :class:`PageIndex`)
       :keyword start_page_number: (See :class:`PageIndex`)
       :keyword max_page_links: (See :class:`PageIndex`)
    """
    def __init__(self, annual_item_organiser, current_page_number=1, start_page_number=1, max_page_links=4):
        super().__init__(current_page_number=current_page_number,
                                              start_page_number=start_page_number,
                                              max_page_links=max_page_links)
        self.annual_item_organiser = annual_item_organiser

    def get_contents_for_page(self, page_number):
        year = self.years[page_number-1]
        return self.annual_item_organiser.get_items_for_year(year)

    def get_description_for_page(self, page_number):
        return str(self.years[page_number-1])

    @property
    def years(self):
        return self.annual_item_organiser.get_years()

    @property
    @memoized
    def total_number_of_pages(self):
        return len(self.years)


class PageMenu(HTMLWidget):
    """An Menu, which lists the pages of items that can be navigated by a user. If there are
       many pages, only a small subset is shown, with controls allowing the user to browse to
       the wanted page number and choose it.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`reahl.web.ui.HTMLElement`)
       :param page_index: The :class:`PageIndex` whose pages are displayed by this PageMenu.
       :param paged_panel: The :class:`PagedPanel` in which the contents of a page is displayed.

    """
    def __init__(self, view, css_id, page_index, paged_panel):
        self.page_index = page_index
        self.paged_panel = paged_panel
        super().__init__(view)

        self.menu = self.add_child(Menu(view))
        self.create_items(self.menu)
        self.set_html_representation(self.menu)
        self.set_id(css_id)
        self.append_class('pagination')

        self.enable_refresh(self.query_fields.start_page_number)

    def add_styling_to_menu_item(self, item):
        item.a.append_class('page-link')
        item.html_representation.append_class('page-item')

    def create_items(self, menu):

        self.add_bordering_link_for(menu, '←', 'First', 1,
                                   not self.page_index.has_previous_page)
        self.add_bordering_link_for(menu, '«', 'Prev', self.page_index.previous_page.number, 
                                   not self.page_index.has_previous_page)

        for page in self.page_index.pages_in_range:
            bookmark = self.paged_panel.get_bookmark(page_number=page.number, description=page.description)
            bookmark.query_arguments['start_page_number'] = self.page_index.start_page_number
            link = A.from_bookmark(self.view, bookmark)
            item = menu.add_a(link)
            item.html_representation.add_attribute_source(ActiveStateAttributes(item))
            self.add_styling_to_menu_item(item)
            if self.page_index.current_page_number == page.number:
                item.set_active()

        self.add_bordering_link_for(menu, '»', 'Next', self.page_index.next_page.number, 
                                    not self.page_index.has_next_page)
        self.add_bordering_link_for(menu, '→', 'Last', self.page_index.last_page.number, 
                                    not self.page_index.has_next_page)

    def add_bordering_link_for(self, menu, short_description, long_description, start_page_number, disabled):
        link = A.from_bookmark(self.view, self.get_bookmark(start_page_number=start_page_number, 
                                                            disabled=disabled))

        link.add_child(Span(self.view, text=short_description)).set_attribute('aria-hidden', 'true')
        link.add_child(Span(self.view, text=long_description)).append_class('sr-only')
        link.set_attribute('aria-label', long_description)
        if disabled:
            link.set_attribute('tabindex', '-1')
        link.set_active(not disabled)
        item = menu.add_a(link)
        item.html_representation.add_attribute_source(AccessRightAttributes(link))
        self.add_styling_to_menu_item(item)
        return link
        
    def get_bookmark(self, start_page_number=1, disabled=False):
        bookmark = Bookmark.for_widget(None,
                                       query_arguments={'start_page_number': start_page_number,
                                                        'current_page_number': self.page_index.current_page_number},
                                       write_check=lambda: not disabled).on_view(self.view)
        return bookmark

    query_fields = ExposedNames()
    query_fields.start_page_number = lambda i: i.page_index.fields.start_page_number
    query_fields.current_page_number = lambda i: i.paged_panel.query_fields.current_page_number

    @property
    def jquery_selector(self):
        return '"ul.pagination"'

    def get_js(self, context=None):
        js = ['$(%s).bootstrappagemenu({});' % self.jquery_selector]
        return super().get_js(context=context) + js 
