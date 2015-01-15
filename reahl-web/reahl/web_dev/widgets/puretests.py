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
from reahl.tofu import vassert

from reahl.webdev.tools import XPath

from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture

from reahl.web.fw import UserInterface
from reahl.web.ui import Panel, P, HTML5Page

from reahl.web.pure import GridLayout, UnitSize, PageColumnLayout

#    def add_unit(self, widget, default=None, sm=None, md=None, lg=None, xl=None):


@test(WebFixture)
def grid_layout_basics(fixture):
    """A GridLayout turns its Widget into a Pure Grid to which children can be added as Pure Units."""

    widget = Panel(fixture.view).using_layout(GridLayout())

    widget.layout.add_unit(P(fixture.view))

    widget_tester = WidgetTester(widget)
    actual = widget_tester.render_html()
    
    vassert( actual == '<div class="pure-g"><div class="pure-u"><p></p></div></div>' )


@test(WebFixture)
def grid_layout_fractions(fixture):
    """When adding a unit, you can specify the sizes to be used for different media sizes."""

    widget = Panel(fixture.view).using_layout(GridLayout())

    widget.layout.add_unit(P(fixture.view), size=UnitSize(default='1/2', sm='1/3', md='2/3', lg='1/4', xl='3/4'))

    widget_tester = WidgetTester(widget)
    actual = widget_tester.render_html()
    
    vassert( actual == '<div class="pure-g"><div class="pure-u-1-2 pure-u-lg-1-4 pure-u-md-2-3 pure-u-sm-1-3 pure-u-xl-3-4"><p></p></div></div>' )


"""Responsive sizing for a unit can be described using a UnitSize object."""
"""A Layout can be spefified to a WidgetFactory in using_layout kwarg"""
"""Similarly, this can be passed on from .define_page"""
"""use_layout is an alias for using_layout that just reads better in other contexts"""
"""A ColumnLayout is (conceptually): a bunch of columns"""
  """Columns can be specified with a UnitSize (when passed as tuple), or without a UnitSize using a string."""
  """Dictionary access on layout.columns can be used to access the Panel in each named column as specified"""
  """Each column has a slot, named after the column name as specified."""
"""A PageColumnLayout adds a header, and footer to the body of the page, and a ColumnLayout (with given dimentions?) inbetween the header and footer"""
   """Exposes the header, footer and columns of the body of the page"""

@test(WebFixture)
def humantest(fixture):

    class ColumnSpec(object):
        def __init__(self, name, fraction):
            self.name = name
            self.fraction = fraction
            
    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page, using_layout=PageColumnLayout(('secondary', UnitSize(lg='1/4', sm='1/2')), 
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
            self.using_layout(PageColumnLayout(('koos0', UnitSize(default='1/2')), 'koos1'))
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

    fixture.driver_browser.open('/koos2')
    fixture.driver_browser.view_source()
    
    rendered_in_body = fixture.driver_browser.get_inner_html_for('//body')


    expected = '''<div id="doc">'''\
                  '''<header id="hd"><p>Header</p></header>'''\
                  '''<div id="bd" role="main" class="pure-g">'''\
                  '''  <div class="pure-u"><div><p>Main column</p></div></div>'''\
                  '''  <div class="pure-u"><div><p>Secondary column</p></div></div>'''\
                  '''</div>'''\
                  '''<footer id="ft"><p>Footer</p></footer></div>'''
    vassert( rendered_in_body.startswith(expected) )



