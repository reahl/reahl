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

from __future__ import print_function, unicode_literals, absolute_import, division

import functools

from reahl.component.modelinterface import exposed, IntegerField, BooleanField
from reahl.web.fw import Bookmark, Widget
from reahl.web.bootstrap.ui import A, Span, Div, Table, TextNode
from reahl.web.bootstrap.pagination import PageMenu
from reahl.web.pager import SequentialPageIndex, PagedPanel

class TablePageIndex(SequentialPageIndex):
    def __init__(self, columns, items, items_per_page=10, current_page_number=1, start_page_number=1, max_page_links=5):
        super(TablePageIndex, self).__init__(items, items_per_page=items_per_page, current_page_number=current_page_number, start_page_number=start_page_number, max_page_links=max_page_links)
        self.sort_column_number = 0
        self.sort_descending = False
        self.columns = columns

    @property
    def sorting_keys(self):
        return [column.sort_key for column in self.columns]

    def get_contents_for_page(self, page_number):
        sorting_key = self.sorting_keys[self.sort_column_number]
        self.items.sort(key=sorting_key, reverse=self.sort_descending)
        return super(TablePageIndex, self).get_contents_for_page(page_number)

    @exposed
    def fields(self, fields):
        fields.update_copies(super(TablePageIndex, self).fields)
        fields.sort_column_number = IntegerField(required=False, default=self.sort_column_number)
        fields.sort_descending = BooleanField(required=False, default=self.sort_descending)


class PagedTable(PagedPanel):
    def __init__(self, view, page_index, columns, caption_text=None, summary=None, css_id=None):
        super(PagedTable, self).__init__(view, page_index, css_id=css_id)

        def make_heading_with_sort_controls(column_number, column, view):
            heading_widget = Widget(view)
            if column.sort_key:
                heading = self.create_sorter_link(column_number, column.make_heading_widget(view))
            else:
                heading = column.make_heading_widget(view)
            heading_widget.add_child(heading)

            return heading_widget

        columns_with_sort_controls = []
        for i, column in enumerate(columns):
            make_heading_partial = functools.partial(make_heading_with_sort_controls, i, column)
            columns_with_sort_controls.append(column.with_overridden_heading_widget(make_heading_partial))

        self.table = self.add_child(Table.from_columns(view, columns_with_sort_controls,
                                                  self.current_contents,
                                                  caption_text=caption_text,
                                                  summary=summary))

    def create_sorter_link(self, column_number, heading_widget):
        show_control = (column_number == self.page_index.sort_column_number)
        if show_control:
            sort_descending = 'off' if self.page_index.sort_descending else 'on'
            link_class = 'sorted-descending' if sort_descending=='off' else 'sorted-ascending'
        else:
            sort_descending = 'off'
            link_class = None

        bookmark = Bookmark.for_widget(None,
                                       query_arguments={'sort_column_number': column_number,
                                                        'sort_descending': sort_descending})
        link = A.from_bookmark(self.view, bookmark.on_view(self.view))
        link.add_child(heading_widget)
        if link_class:
            link.append_class(link_class)
        return link

    @exposed
    def query_fields(self, fields):
        fields.update_copies(super(PagedTable, self).query_fields)
        fields.sort_column_number = self.page_index.fields.sort_column_number
        fields.sort_descending = self.page_index.fields.sort_descending



class DataTable(Div):
    """A table containing a potentially large set of data items. DataTable does not display all its items
       on the current page. It renders as a table spread over different pages between which a user can
       navigate, thus preventing a large data set sent back to a single page.

       If a :class:`DynamicColumn` is used to define the table also specifies a `sort_key`, the table
       is rendered with controls on that column heading that allows it to be sorted on that column. The
       sort operation applies to the entire dataset even though the user stays on the current page and only
       sees a subset of that data.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param columns: The :class:`reahl.web.ui.DynamicColumn` instances that define the contents of the table.
       :param items: A list containing objects represented in each row of the table.
       :param css_id: (See :class:`HTMLElement`)

       :keyword items_per_page: The maximum number of rows allowed per page.
       :keyword caption_text: If given, a :class:`reahl.web.ui.Caption` is added with this text.
       :keyword summary: If given, a :class:`reahl.web.ui.Summary` is added with this text.
       :keyword table_layout: If given, the layout is applied to the contained :class:`reahl.web.ui.Table`.

    """
    def __init__(self, view, columns, items, css_id, items_per_page=10, caption_text=None, summary=None, table_layout=None):
        super(DataTable, self).__init__(view, css_id=css_id)

        self.append_class('reahl-datatable')

        self.page_index = TablePageIndex(columns, items, items_per_page=items_per_page)

        paged_css_id = '%s_paged' % css_id
        self.paged_contents = PagedTable(view, self.page_index, columns, caption_text=caption_text, summary=summary, css_id=paged_css_id)
        self.page_menu = PageMenu(view, 'page_menu', self.page_index, self.paged_contents)
        self.add_children([self.page_menu, self.paged_contents])
        if table_layout:
            self.table.use_layout(table_layout)

    @property
    def table(self):
        return self.paged_contents.table





