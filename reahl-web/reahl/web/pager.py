# Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
Tools for breaking long lists into shorter lists that can be paged.
"""

from __future__ import print_function
from __future__ import unicode_literals
import six


from abc import ABCMeta, abstractmethod, abstractproperty
from functools import partial

from reahl.component.i18n import Translator
from reahl.component.decorators import memoized
from reahl.component.modelinterface import IntegerField, exposed
from reahl.web.fw import Bookmark
from reahl.web.ui import HMenu, A, Panel

_ = Translator('reahl-web')


@six.add_metaclass(ABCMeta)
class PageIndexProtocol(object):
    @abstractproperty
    def pages_in_range(self): pass
    @abstractproperty
    def current_page(self): pass
    @abstractproperty
    def start_page(self): pass
    @abstractproperty
    def end_page(self): pass
    @abstractproperty
    def previous_page(self): pass
    @abstractproperty
    def next_page(self): pass
    @abstractproperty
    def last_page(self): pass
    @abstractproperty
    def has_next_page(self): pass
    @abstractproperty
    def has_previous_page(self): pass


class PagedPanel(Panel):
    """A :class:`Panel` whose contents change, depending on the page selected by a user from a :class:`PageMenu`.
       A programmer should subclass from PagedPanel, supplying an `__init__` method which populates the PagedPanel
       with appropriate contents, based on its `.current_contents`.
       
       .. admonition:: Styling
          
          Represented in HTML by an <div> element.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param page_index: The :class:`PageIndex` to use to supply contents to the pages displayed by this PagedPanel.
       :param css_id: (See :class:`HTMLElement`)
    """
    def __init__(self, view, page_index, css_id):
        self.page_index = page_index
        super(PagedPanel, self).__init__(view, css_id=css_id)
        self.enable_refresh()
    
    @classmethod
    def get_bookmark(cls, description=None, page_number=1):
        return Bookmark('', '', description=description or '%s' % page_number,
                        query_arguments={'current_page_number': page_number}, ajax=True)

    @exposed
    def query_fields(self, fields):
        fields.current_page_number = self.page_index.fields.current_page_number

    @property
    def current_contents(self):
        """The list of items that should be displayed for the current page."""
        return self.page_index.current_page.contents


class Page(object):
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

       :param current_page_number: The initial page shown to users.
       :param start_page_number: The first page that should be listed in the current :class:`PageMenu`.
       :param max_page_links: The number of pages to be shown in the current :class:`PageMenu`.
    """
    def __init__(self, current_page_number=1, start_page_number=1, max_page_links=5):
        super(PageIndex, self).__init__()
        self.current_page_number = current_page_number
        self.start_page_number = start_page_number
        self.max_page_links = max_page_links
        
    @exposed
    def fields(self, fields):
        fields.current_page_number = IntegerField(required=False, default=1)
        fields.start_page_number =   IntegerField(required=False, default=1)

    @abstractmethod
    def get_contents_for_page(self, page_number): 
        """Override this method in subclasses to obtain the correct list of items for the given `page_number`."""

    @abstractproperty
    def total_number_of_pages(self): 
        """Override this @property in subclasses to state what the total number of pages is."""    
    
    def get_description_for_page(self, page_number):
        return six.text_type(page_number)
    
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
                for page_number in range(self.start_page_number, self.end_page.number+1)]

    @property
    @memoized
    def start_page(self):
        return self.get_page_number(self.start_page_number)

    @property
    @memoized
    def end_page(self):
        page_number = self.start_page_number+min(self.max_page_links-1, self.total_number_of_pages-(self.start_page_number));
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
        return self.start_page.number > 1


class PageMenu(HMenu):
    """An HMenu, which lists the pages of items that can be navigated by a user. If there are
       many pages, only a small subset is shown, with controls allowing the user to browse to
       the wanted page number and choose it.

       .. admonition:: Styling
       
          Rendered as a <ul class="reahl-menu reahl-horizontal reahl-pagemenu">. The <a> inside its
          first <li> has class="first", the <a> in the second <li> has class="prev". The <a> in the 
          second last <li> has class="next", and the <a> in the last <li> has class="last".
          

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (See :class:`HTMLElement`)
       :param page_index: The :class:`PageIndex` whose pages are displayed by this PageMenu.
       :param page_container: The :class:`PagedPanel` in which the contents of a page is displayed.
    """
    def __init__(self, view, css_id, page_index, paged_panel):
        self.page_index = page_index
        super(PageMenu, self).__init__(view, [], css_id=css_id)
        self.append_class('reahl-pagemenu')

        self.paged_panel = paged_panel
        self.add_items()
        self.enable_refresh()

    def add_items(self):
        links = []

        first = A.from_bookmark(self.view, self.get_bookmark(start_page_number=1, description='|<'))
        first.append_class('first')
        first.set_active(self.page_index.has_previous_page)
        previous = A.from_bookmark(self.view, self.get_bookmark(start_page_number=self.page_index.previous_page.number, description='<'))
        previous.append_class('prev')
        previous.set_active(self.page_index.has_previous_page)
        links.extend([first, previous])

        for page in self.page_index.pages_in_range:
            link = A.from_bookmark(self.view, self.paged_panel.get_bookmark(page_number=page.number, description=page.description))
            links.append(link)

        next = A.from_bookmark(self.view, self.get_bookmark(start_page_number=self.page_index.next_page.number, description='>'))
        next.append_class('next')
        next.set_active(self.page_index.has_next_page)
        last = A.from_bookmark(self.view, self.get_bookmark(start_page_number=self.page_index.last_page.number, description='>|'))
        last.append_class('last')
        last.set_active(self.page_index.has_next_page)
        links.extend([next, last])

        self.set_items_from(links)

    @classmethod
    def get_bookmark(self, description=None, start_page_number=1):
        return Bookmark.for_widget(description=description or '%s' % start_page_number,
                                   query_arguments={'start_page_number': start_page_number})

    @exposed
    def query_fields(self, fields):
        fields.start_page_number = self.page_index.fields.start_page_number
    

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
        super(SequentialPageIndex, self).__init__(current_page_number=current_page_number,
                                              start_page_number=start_page_number,
                                              max_page_links=max_page_links)
        self.items = items
        self.items_per_page = items_per_page

    def get_contents_for_page(self, page_number):
        range_start = (page_number-1)*self.items_per_page
        range_end = range_start+min(self.items_per_page, len(self.items)-(range_start))-1
        return self.items[range_start:range_end+1]

    @property
    @memoized
    def total_number_of_pages(self):
        return ((len(self.items)-1) // (self.items_per_page))+1


@six.add_metaclass(ABCMeta)
class AnnualItemOrganiserProtocol(object):
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
       :param current_page_number: (See :class:`PageIndex`)
       :param start_page_number: (See :class:`PageIndex`)
       :param max_page_links: (See :class:`PageIndex`)
    """
    def __init__(self, annual_item_organiser, current_page_number=1, start_page_number=1, max_page_links=4):
        super(AnnualPageIndex, self).__init__(current_page_number=current_page_number,
                                          start_page_number=start_page_number,
                                          max_page_links=max_page_links)
        self.annual_item_organiser = annual_item_organiser

    def get_contents_for_page(self, page_number):
        year = self.years[page_number-1]
        return self.annual_item_organiser.get_items_for_year(year)

    def get_description_for_page(self, page_number):
        return six.text_type(self.years[page_number-1])

    @property
    def years(self):
        return self.annual_item_organiser.get_years()

    @property
    @memoized
    def total_number_of_pages(self):
        return len(self.years)


