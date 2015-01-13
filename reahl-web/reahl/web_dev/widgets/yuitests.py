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

from reahl.webdev.tools import WidgetTester, Browser
from reahl.web_dev.fixtures import WebFixture

from reahl.web.ui import Panel, P, YuiDoc
from reahl.web.fw import UserInterface, ReahlWSGIApplication
from reahl.web.yui import TwoColumnPageYUI
from reahl.web.libraries import YuiGridsCss

@test(WebFixture)
def two_column_yui_layout_visual(fixture):

    #added this, but seems no css nor js files are server: 404
    fixture.config.web.frontend_libraries.add(YuiGridsCss())

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPageYUI)
            home = self.define_view('/', title='Hello')
            home.set_slot('main', P.factory(text='Main column'))
            home.set_slot('secondary', P.factory(text='Secondary column'))
            home.set_slot('header', P.factory(text='Header'))
            home.set_slot('footer', P.factory(text='Footer'))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    #wsgi_app = ReahlWSGIApplication(fixture.config)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')
    import pdb;pdb.set_trace()
    rendered_in_body = fixture.driver_browser.get_inner_html_for('//body')

    expected = '<div id="doc" class="yui-t2"><div id="hd" class="yui-g"><header><p>Header</p></header></div><div id="bd" role="main"><div id="yui-main"><div class="yui-b"><p>Main column</p></div></div><div class="yui-b"><p>Secondary column</p></div></div><div id="ft"><footer><p>Footer</p></footer></div></div>'
    vassert( rendered_in_body.startswith(expected) )


@test(WebFixture)
def two_column_yui_layout(fixture):
        """A simple Yui page with two columns, a header and a footer."""

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPageYUI)
                home = self.define_view('/', title='Home')
                home.set_slot('main', P.factory(text='Main column'))
                home.set_slot('secondary', P.factory(text='Secondary column'))
                home.set_slot('header', P.factory(text='Header'))
                home.set_slot('footer', P.factory(text='footer'))

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/')
        rendered_in_body = fixture.driver_browser.get_inner_html_for('//body')
        expected = '<div id="doc" class="yui-t2"><div id="hd" class="yui-g"><header><p>Header</p></header></div><div id="bd" role="main"><div id="yui-main"><div class="yui-b"><p>Main column</p></div></div><div class="yui-b"><p>Secondary column</p></div></div><div id="ft"><footer><p>Footer</p></footer></div></div>'
        vassert( rendered_in_body.startswith(expected) )



@test(WebFixture)
def twocolumn_pageyui(fixture):
    """A simple Yui page with two columns, a header and a footer."""
    widget = TwoColumnPageYUI(fixture.view, title='It: $current_title')
    widget.add_default_slot('slot1', P.factory())
    tester = WidgetTester(widget)

    rendered_html = tester.render_html()
    expected = '<!DOCTYPE html><html><head><title>It: A view</title></head><body><div id="doc" class="yui-t2"><div id="hd" class="yui-g"><header></header></div><div id="bd" role="main"><div id="yui-main"><div class="yui-b"></div></div><div class="yui-b"></div></div><div id="ft"><footer></footer></div></div></body></html>'
    vassert( rendered_html == expected )

    vassert( list(widget.default_slot_definitions.keys()) == ['slot1'] )

    vassert( isinstance(widget.layout.yui_page, YuiDoc) )
    vassert( widget.footer is widget.layout.yui_page.footer )
    vassert( widget.header is widget.layout.yui_page.header )
    vassert( widget.main is widget.layout.yui_page.main_block )
    vassert( widget.secondary is widget.layout.yui_page.secondary_block )
