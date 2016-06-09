# Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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
"""
.. versionadded:: 3.2

Sometimes you need to display a long list of items. Displaying such a list on a single
page is not a good idea, because the page will take forever to load.

This module provides a few classes you can use to build a single View that displays
only one "pageful" of the list. You can then also include a :class:`PageMenu` -- a
menu on which a user can choose to navigate to another section (or page) of the list.



"""

from __future__ import print_function, unicode_literals, absolute_import, division
import six


from reahl.component.i18n import Translator
from reahl.component.modelinterface import exposed
from reahl.web.fw import Bookmark
from reahl.web.ui import HTMLWidget, Menu, AccessRightAttributes, ActiveStateAttributes
from reahl.web.bootstrap.ui import A, Span
from reahl.web.pager import PagedPanel, PageIndex, SequentialPageIndex, AnnualItemOrganiserProtocol, AnnualPageIndex


_ = Translator('reahl-web')


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
        super(PageMenu, self).__init__(view)

        self.menu = self.add_child(Menu(view, add_reahl_styling=False))
        self.create_items(self.menu)
        self.set_html_representation(self.menu)
        self.set_id(css_id)
        self.append_class('pagination')

        self.enable_refresh(self.query_fields.start_page_number)

    def add_styling_to_menu_item(self, item):
        item.a.append_class('page-link')
        item.widget.append_class('page-item')

    def create_items(self, menu):
        links = []

        self.add_bordering_link_for(menu, '←', 'First', 1,
                                   not self.page_index.has_previous_page)
        self.add_bordering_link_for(menu, '«', 'Prev', self.page_index.previous_page.number, 
                                   not self.page_index.has_previous_page)

        for page in self.page_index.pages_in_range:
            bookmark = self.paged_panel.get_bookmark(page_number=page.number, description=page.description)
            bookmark.query_arguments['start_page_number'] = self.page_index.start_page_number
            link = A.from_bookmark(self.view, bookmark)
            item = menu.add_a(link)
            item.widget.add_attribute_source(ActiveStateAttributes(item))
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

        link.add_child(Span(self.view, text=short_description)).set_attribute('aria-hidden', 'true');
        link.add_child(Span(self.view, text=long_description)).append_class('sr-only');
        link.set_attribute('aria-label', long_description);
        link.set_active(not disabled)
        item = menu.add_a(link)
        item.widget.add_attribute_source(AccessRightAttributes(link))
        self.add_styling_to_menu_item(item)
        
    def get_bookmark(self, start_page_number=1, disabled=False):
        bookmark = Bookmark.for_widget(None,
                                       query_arguments={'start_page_number': start_page_number,
                                                        'current_page_number': self.page_index.current_page_number},
                                       write_check=lambda: not disabled).on_view(self.view)
        return bookmark
    

    @exposed
    def query_fields(self, fields):
        fields.start_page_number = self.page_index.fields.start_page_number
        fields.current_page_number = self.paged_panel.query_fields.current_page_number

    @property
    def jquery_selector(self):
        return '"ul.pagination"'

    def get_js(self, context=None):
        js = ['$(%s).bootstrappagemenu({});' % self.jquery_selector]
        return super(PageMenu, self).get_js(context=context) + js 






