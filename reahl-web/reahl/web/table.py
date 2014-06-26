# Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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
Displaying tabular data in a paged, sortable manner
"""

from reahl.web.fw import Bookmark
from reahl.web.ui import A, Span, Panel, Table, Thead, Tr, Td, Th, TextNode
from reahl.web.pager import SequentialPageIndex, PagedPanel, PageMenu
from reahl.component.modelinterface import exposed, IntegerField, BooleanField


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


class DynamicColumn(object):
    def __init__(self, heading, make_widget, sort_key=None):
        self.sort_key = sort_key
        self.make_widget = make_widget
        self.heading = heading

    def as_widget(self, view, item):
        return self.make_widget(view, item)


class StaticColumn(DynamicColumn):
    def __init__(self, field, attribute_name, sort_key=None):
        super(StaticColumn, self).__init__(field.label, self.make_text_node, sort_key=sort_key)
        self.field = field
        self.attribute_name = attribute_name
    
    def make_text_node(self, view, item):
        field = self.field.copy()
        field.bind(self.attribute_name, item)
        return TextNode(view, field.as_input())


class PagedTable(PagedPanel):
    def __init__(self, view, page_index, columns, caption_text=None, summary=None, css_id=None):
        super(PagedTable, self).__init__(view, page_index, css_id=css_id)  
        self.columns = columns
        self.table = self.add_child(Table(view, caption_text=caption_text, summary=summary))

        self.create_header_columns()
        self.create_rows()

    def create_header_columns(self):
        table_header = self.table.add_child(Thead(self.view))
        header_tr = table_header.add_child(Tr(self.view))
        for column_number, column in enumerate(self.columns):
            column_th = header_tr.add_child(Th(self.view))
            column_th.add_child(Span(self.view, text=column.heading))
            if column.sort_key:
                column_th.add_child(self.create_sorter_controls(column_number))

    def create_rows(self):
        for item in self.current_contents:
            row = self.table.add_child(Tr(self.view))
            for column in self.columns:
                row_td = row.add_child(Td(self.view))
                row_td.add_child(column.as_widget(self.view, item))

    def create_sorter_controls(self, column_number):
        sorting_controls = Span(self.view)
        sorting_controls.append_class('reahl-column-sort')
        sorting_controls.add_child(self.create_sorter_link(column_number))
        sorting_controls.add_child(self.create_sorter_link(column_number, descending=True))
        return sorting_controls

    def create_sorter_link(self, column_number, descending=False):
        description = u'▼' if descending else u'▲'
        sort_descending = u'on' if descending else u'off'
        return A.from_bookmark(self.view, Bookmark.for_widget(description=description, 
                                              query_arguments={u'sort_column_number': column_number, 
                                                                u'sort_descending': sort_descending}))

    @exposed
    def query_fields(self, fields):
        fields.update_copies(super(PagedTable, self).query_fields)
        fields.sort_column_number = self.page_index.fields.sort_column_number
        fields.sort_descending = self.page_index.fields.sort_descending


class DataTable(Panel):
    def __init__(self, view, columns, items, items_per_page=10, caption_text=None, summary=None, form=None, css_id=None):
        super(DataTable, self).__init__(view, css_id=css_id)
        self.append_class(u'reahl-datatable')

        self.page_index = TablePageIndex(columns, items, items_per_page=items_per_page)

        paged_css_id = u'%s_paged' % css_id
        self.paged_contents = PagedTable(view, self.page_index, columns, caption_text=caption_text, summary=summary, css_id=paged_css_id)
        self.page_menu = PageMenu(view, u'page_menu', self.page_index, self.paged_contents)
        self.add_children([self.page_menu, self.paged_contents])


