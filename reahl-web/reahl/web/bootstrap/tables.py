# Copyright 2014-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

Tables are Widgets that show data items in rows arranged into aligned columns.
This module includes tools to help transform data for display in a Table.

You can also display a Widget (such as a Button or Input) in a Table cell by using
DynamicColumn.

The number of data items displayed in a Table can potentially be very large. DataTable
solves this problem by only displaying a small portion of the data, allowing a user
to page to different pages, each containing a suitably-sized smaller list. DataTable
can also be set up to let a user sort data according to different columns.

"""



import functools

from reahl.component.exceptions import ProgrammerError
from reahl.component.modelinterface import ExposedNames, IntegerField, BooleanField
from reahl.web.fw import Bookmark, Widget, Layout

from reahl.web.ui import HTMLAttributeValueOption, StaticColumn, ColGroup, Col, Th, Tr, Td, Tbody, Thead, Tfoot, DynamicColumn, Caption

import reahl.web.ui
from reahl.web.bootstrap.ui import A, Div
from reahl.web.bootstrap.pagination import PageMenu, PagedPanel, SequentialPageIndex
from reahl.web.bootstrap.grid import DeviceClass


class Table(reahl.web.ui.HTMLWidget):
    """Tabular data displayed as rows broken into columns.

       :param view: (See :class:`~reahl.web.fw.Widget`)
       :keyword caption_text: If text is given here, a caption will be added to the table containing the caption text.
       :keyword summary:  A textual summary of the contents of the table which is not displayed visually, \
                but may be used by a user agent for accessibility purposes.
       :keyword css_id: (See :class:`~reahl.web.ui.HTMLElement`)

    """
    def __init__(self, view, caption_text=None, summary=None, css_id=None):
        super().__init__(view)
        self.main_div = self.add_child(Div(view, css_id=css_id))
        self.set_html_representation(self.main_div)
        self.table = self.main_div.add_child(reahl.web.ui.Table(view, caption_text=caption_text, summary=summary))
        self.table.append_class('table')

    def with_data(self, columns, items, footer_items=None):
        """Populate the table with the given data. Data is arranged into columns as
           defined by the list of :class:`DynamicColumn` or :class:`StaticColumn` instances passed in.

           :param columns: The :class:`DynamicColumn` instances that define the contents of the table.
           :param items: A list containing objects represented in each row of the table.
           :keyword footer_items: If given a footer is added. A list containing objects represented in each footer row of the table.

           .. versionchanged:: 5.0
              Added `footer_items`.
        """
        self.table.with_data(columns, items, footer_items=footer_items)
        return self

    @property
    def thead(self):
        return self.table.thead


class HeadingTheme(HTMLAttributeValueOption):
    def __init__(self, name):
        super().__init__(name, name is not None, constrain_value_to=['light', 'dark'])


class TableLayout(Layout):
    """A Layout for customising details of how a Table is displayed.

    :keyword dark: If True, table text is light text on dark background.
    :keyword border: If set to 'cells', a border is rendered around each cell.
                     When set to 'rows' (the default) only row delimeters are shown.
                     If 'borderless', no borders are rendered.
                     Allowed values: 'rows', 'cells' and 'borderless'.
    :keyword compact: If True, make the table more compact by cutting cell padding in half.
    :keyword striped: If True, colour successive rows lighter and darker.
    :keyword highlight_hovered: If True, a row is highlighted when the mouse hovers over it.
    :keyword responsive: If True, activate horizontal scrolling.  If set to a device class activate
                         horizontal scrolling only for devices smaller than the device class.
                         Allowed values : 'xs', 'sm', 'md', 'lg' and 'xl'
    :keyword heading_theme: One of 'light' or 'dark'. A light heading is one with darker text on a lighter background.
    """
    def __init__(self, dark=False, border='rows', compact=False, striped=False, highlight_hovered=False,
                 responsive=False, heading_theme=None):
        super().__init__()

        if isinstance(responsive, str):
            self.responsive_attribute_option = HTMLAttributeValueOption(responsive, True,
                                                                   prefix='table-responsive',
                                                                   constrain_value_to=DeviceClass.device_classes)
        else:
            self.responsive_attribute_option = HTMLAttributeValueOption('table-responsive', responsive)

        border_option = HTMLAttributeValueOption(border, border and border != 'rows',
                                                 prefix='table',
                                                 map_values_using={'cells': 'bordered', 'rows':''},
                                                 constrain_value_to=['borderless', 'cells', 'rows'])

        self.table_properties = [HTMLAttributeValueOption('dark', dark, prefix='table'),
                                 HTMLAttributeValueOption('striped', striped, prefix='table'),
                                 border_option,
                                 HTMLAttributeValueOption('hover', highlight_hovered, prefix='table'),
                                 HTMLAttributeValueOption('sm', compact, prefix='table')
                                 ]

        self.heading_theme = HeadingTheme(heading_theme)


    def customise_widget(self):
        super().customise_widget()

        if self.responsive_attribute_option.is_set:
            self.widget.main_div.append_class(self.responsive_attribute_option.as_html_snippet())

        for table_property in self.table_properties:
            if table_property.is_set:
                self.widget.table.append_class(table_property.as_html_snippet())
        self.style_heading()

    def style_heading(self):
        if self.heading_theme.is_set:
            table_header = self.widget.table.get_or_create_header()
            table_header.append_class('thead-%s' % self.heading_theme.as_html_snippet())


class TablePageIndex(SequentialPageIndex):
    def __init__(self, columns, items, items_per_page=10, current_page_number=1, start_page_number=1, max_page_links=5):
        super().__init__(items, items_per_page=items_per_page,
                                             current_page_number=current_page_number,
                                             start_page_number=start_page_number,
                                             max_page_links=max_page_links)
        self.sort_column_number = None
        self.sort_descending = False
        self.columns = columns

    @property
    def sorting_keys(self):
        return [column.sort_key for column in self.columns]

    def get_contents_for_page(self, page_number):
        if self.sort_column_number is not None:
            sorting_key = self.sorting_keys[self.sort_column_number]
            self.items.sort(key=sorting_key, reverse=self.sort_descending)

        return super().get_contents_for_page(page_number)

    fields = ExposedNames()
    fields.sort_column_number = lambda i: IntegerField(required=False, default=i.sort_column_number)
    fields.sort_descending = lambda i: BooleanField(required=False, default=i.sort_descending)


class PagedTable(PagedPanel):
    def __init__(self, view, page_index, columns, caption_text=None, summary=None, table_layout=None, css_id=None):
        super().__init__(view, page_index, css_id=css_id)

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

        self.table = self.add_child(Table(view, caption_text=caption_text, summary=summary))
        self.table.with_data(columns_with_sort_controls, self.current_contents)
        if table_layout:
            self.table.use_layout(table_layout)

    def create_sorter_link(self, column_number, heading_widget):
        show_control = (column_number == self.page_index.sort_column_number)
        if show_control:
            sort_descending = self.fields.toggle_sort_descending.as_input()
            link_class = 'sorted-descending' if self.page_index.sort_descending else 'sorted-ascending'
        else:
            sort_descending = self.fields.toggle_sort_descending.false_value
            link_class = None

        bookmark = Bookmark.for_widget(None,
                                       query_arguments={'sort_column_number': column_number,
                                                        'sort_descending': sort_descending})
        link = A.from_bookmark(self.view, bookmark.on_view(self.view))
        link.add_child(heading_widget)
        if link_class:
            link.append_class(link_class)
        return link

    @property
    def toggle_sort_descending(self):
        return not self.page_index.sort_descending

    fields = ExposedNames()
    fields.toggle_sort_descending = lambda i: BooleanField(writable=lambda field: False)
        
    query_fields = ExposedNames()
    query_fields.sort_column_number = lambda i: i.page_index.fields.sort_column_number
    query_fields.sort_descending = lambda i: i.page_index.fields.sort_descending


class DataTable(Div):
    """A table containing a potentially large set of data items. DataTable does not display all its items
       on the current page. It renders as a table spread over different pages between which a user can
       navigate, thus preventing a large data set sent back to a single page.

       If a :class:`DynamicColumn` is used to define the table also specifies a `sort_key`, the table
       is rendered with controls on that column heading that allows it to be sorted on that column. The
       sort operation applies to the entire dataset even though the user stays on the current page and only
       sees a subset of that data.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param columns: The :class:`DynamicColumn` instances that define the contents of the table.
       :param items: A list containing objects represented in each row of the table.
       :param css_id: (See :class:`HTMLElement`)

       :keyword items_per_page: The maximum number of rows allowed per page.
       :keyword max_page_links: The maximum number of page links to show in the page menu.
       :keyword caption_text: If given, a :class:`Caption` is added with this text.
       :keyword summary: If given, this text will be set as the summary of the contained :class:`Table` (See :class:`Table`).
       :keyword table_layout: If given, the layout is applied to the contained :class:`Table`.

    """
    def __init__(self, view, columns, items, css_id, items_per_page=10, max_page_links=5, caption_text=None, summary=None, table_layout=None):
        super().__init__(view, css_id=css_id)

        self.append_class('reahl-datatable')

        self.page_index = TablePageIndex(columns, items, items_per_page=items_per_page, max_page_links=max_page_links)

        paged_css_id = '%s_paged' % css_id
        self.paged_contents = PagedTable(view, self.page_index, columns, caption_text=caption_text, summary=summary, 
                                         table_layout=table_layout, css_id=paged_css_id)
        self.page_menu = PageMenu(view, 'page_menu', self.page_index, self.paged_contents)
        self.add_children([self.page_menu, self.paged_contents])

    @property
    def table(self):
        return self.paged_contents.table


