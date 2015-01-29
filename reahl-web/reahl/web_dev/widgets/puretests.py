# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import test
from reahl.tofu import vassert, scenario

from reahl.webdev.tools import XPath, Browser

from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture

from reahl.web.fw import UserInterface
from reahl.web.ui import Panel, P, HTML5Page, Header, Footer

from reahl.web.pure import ColumnLayout, UnitSize, PageColumnLayout

class ColumnConstructionScenarios(WebFixture):
    @scenario
    def without_sizes(self):
        """Construct the ColumnLayout with a list of column names."""
        self.layout = ColumnLayout('column_a', 'column_b')
        self.expected_class_for_column_b = 'pure-u'

    @scenario
    def with_size(self):
        """You can optionally specify the sizes a column should adhere to."""
        self.layout = ColumnLayout('column_a', ('column_b', UnitSize(default='1/2')))
        self.expected_class_for_column_b = 'pure-u-1-2'


@test(ColumnConstructionScenarios)
def column_layout_basics(fixture):
    """A ColumnLayout turns its Widget into a sequence of columns, each of which is a Panel, laid out next to each other."""

    widget = Panel(fixture.view)
    
    vassert( not widget.has_attribute('class') )
    vassert( not widget.children )
    
    widget.use_layout(fixture.layout)

    vassert( widget.get_attribute('class') == 'pure-g' )
    column_a, column_b = widget.children
    vassert( isinstance(column_a, Panel) )
    vassert( isinstance(column_b, Panel) )

    vassert( column_a.get_attribute('class') == 'pure-u' )    # never varies in scenarios
    vassert( column_b.get_attribute('class') == fixture.expected_class_for_column_b )


@test(WebFixture)
def order_of_columns(fixture):
    """Columns are added in the order given to the ColumnLayout constructor, and the Panel representing each column
       can be obtained using dictionary access on Layout.columns."""

    widget = Panel(fixture.view).use_layout(ColumnLayout('column_name_a', 'column_name_b'))

    column_a = widget.layout.columns['column_name_a']
    column_b = widget.layout.columns['column_name_b']
    
    first_column, second_column = widget.children

    vassert( first_column is column_a )
    vassert( second_column is column_b )


@test(WebFixture)
def a_slot_created_for_each_column(fixture):
    """Each column has a Slot, named after the column name as specified."""

    widget = Panel(fixture.view).use_layout(ColumnLayout('column_name_a', 'column_name_b'))

    column_a, column_b = widget.children
    vassert( 'column_name_a' in column_a.available_slots )
    vassert( 'column_name_b' in column_b.available_slots )


@test(WebFixture)
def adding_columns(fixture):
    """You can add additional columns after construction, containing a supplied Widget."""

    widget = Panel(fixture.view).use_layout(ColumnLayout())

    vassert( not widget.children )

    contents_of_column = P(fixture.view)
    widget.layout.add_column(contents_of_column)

    [added_column] = widget.children
    vassert( added_column.get_attribute('class') == 'pure-u' )
    vassert( added_column.children == [contents_of_column] )



class SizingFixture(WebFixture):
    @scenario
    def all_sizes_given(self):
        self.sizes = dict(default='1/2', sm='1/3', md='2/3', lg='1/4', xl='3/4')
        self.expected_classes = ['pure-u-1-2','pure-u-lg-1-4','pure-u-md-2-3','pure-u-sm-1-3','pure-u-xl-3-4']

    @scenario
    def some_sizes_unspecified(self):
        self.sizes = dict(default='1/3', sm='2/3')
        self.expected_classes = ['pure-u-1-3','pure-u-sm-2-3']


@test(SizingFixture)
def sizing_when_adding(fixture):
    """When adding a column, the unit_size kwarg can be used to specify sizes for the added column."""

    widget = Panel(fixture.view).use_layout(ColumnLayout())

    widget.layout.add_column(P(fixture.view), unit_size=UnitSize(**fixture.sizes))

    widget.children[0].attributes['class'] == fixture.expected_classes




@test(WebFixture)
def page_column_layout_basics(fixture):
    """A PageColumnLayout adds a Panel to the body of its page (the page's document), containing a header, footer 
       with a div inbetween the two."""

    layout = PageColumnLayout()
    widget = HTML5Page(fixture.view).use_layout(layout)
    header, contents_div, footer = layout.document.children

    vassert( isinstance(header, Header) )
    vassert( isinstance(contents_div, Panel) )
    vassert( isinstance(footer, Footer) )


@test(WebFixture)
def page_column_layout_content_layout(fixture):
    """A PageColumnLayout lays out its content (the bits between header and footer) using a ColumnLayout with the columns it is created with."""

    widget = HTML5Page(fixture.view).use_layout(PageColumnLayout('column_a', 'column_b'))
    
    contents_layout = widget.layout.contents.layout
    vassert( isinstance(contents_layout, ColumnLayout) )
    vassert( 'column_a' in contents_layout.columns )
    vassert( 'column_b' in contents_layout.columns )


@test(WebFixture)
def page_column_layout_convenience_features(fixture):
    """A PageColumnLayout exposes useful methods to get to its contents, and adds ids to certain elements for convenience in CSS."""

    layout = PageColumnLayout()
    widget = HTML5Page(fixture.view).use_layout(layout)
    header, contents_div, footer = layout.document.children
    
    vassert( layout.document.css_id == 'doc' )
    vassert( header.css_id == 'hd' )
    vassert( footer.css_id == 'ft' )
    vassert( contents_div.css_id == 'bd' )
    vassert( contents_div.get_attribute('role') == 'main' )
    
    vassert( layout.header is header )
    vassert( layout.contents is contents_div )
    vassert( layout.footer is footer )
    vassert( layout.columns is contents_div.layout.columns )






"""find places that use yui - add include for yui 'library'"""


#------------------------------------------------

@test(WebFixture)
def humantest(fixture):

    class ColumnSpec(object):
        def __init__(self, name, fraction):
            self.name = name
            self.fraction = fraction
            
    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(PageColumnLayout(('secondary', UnitSize(lg='1/4', sm='1/2')), 
                                                                    ('main', UnitSize(lg='3/4', sm='1/2'))))

            home = self.define_view('/', title='Hello')
            home.set_slot('main', P.factory(text='Main column'))
            home.set_slot('secondary', P.factory(text='Secondary column'))
            home.set_slot('header', P.factory(text='Header'))
            home.set_slot('footer', P.factory(text='Footer'))
            self.define_view('/koos2', title='kosie', page=KoosPage.factory())

    class KoosPage(HTML5Page):
        def __init__(self, *args, **kwargs):
            super(KoosPage, self).__init__(*args, **kwargs)
            self.use_layout(PageColumnLayout(('koos0', UnitSize(default='1/2')), 'koos1'))
            self.layout.columns['koos0'].add_child(P(self.view, text='koos was hier'))
            self.layout.columns['koos1'].add_child(P(self.view, text='koos1 was hier'))

    class MainUI2(UserInterface):
        def assemble(self):
            home = self.define_view('/', title='Hello', page=KoosPage.factory())
            home.set_slot('koos0', P.factory(text='Main column'))
            home.set_slot('koos1', P.factory(text='Secondary column'))
            home.set_slot('header', P.factory(text='Header'))
            home.set_slot('footer', P.factory(text='Footer'))


    wsgi_app = fixture.new_wsgi_app(site_root=MainUI, enable_js=True)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')
    fixture.driver_browser.view_source()

    rendered_in_body = fixture.driver_browser.get_inner_html_for('//body')
    expected_html = '''<div id="doc">'''\
                  '''<header id="hd"><p>Header</p></header>'''\
                  '''<div id="bd" role="main" class="pure-g">'''\
                    '''<div class="pure-u pure-u-lg-1-4 pure-u-sm-1-2"><p>Secondary column</p></div>'''\
                    '''<div class="pure-u pure-u-lg-3-4 pure-u-sm-1-2"><p>Main column</p></div>'''\
                  '''</div>'''\
                  '''<footer id="ft"><p>Footer</p></footer></div>'''
    rendered_in_body = rendered_in_body[:len(expected_html)]
    vassert( rendered_in_body == expected_html )

    fixture.driver_browser.open('/koos2')
    fixture.driver_browser.view_source()
    




