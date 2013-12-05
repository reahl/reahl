# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


import os
import re
import contextlib
import pkg_resources

from webob import Request, Response

from nose.tools import istest
from reahl.tofu import Fixture, test, scenario
from reahl.tofu import vassert, expected
from reahl.stubble import EmptyStub, stubclass

from reahl.component.config import Configuration, ReahlSystemConfig
from reahl.component.exceptions import IncorrectArgumentError, IsInstance
from reahl.web.egg import WebConfig, ReahlEgg
from reahl.webelixirimpl import WebUserSession, PersistedException, UserInput
from reahl.web.fw import UrlBoundView, Region, WebExecutionContext, Widget
from reahl.web.ui import TwoColumnPage, P, Div, Slot
from reahl.webdev.tools import WidgetTester, Browser
from reahl.web_dev.fixtures import WebBasicsMixin, WebFixture


class WidgetFixture(Fixture, WebBasicsMixin):
    def new_region_factory(self):
        factory = Region.factory(u'test_region_name')
        factory.attach_to(u'/', {})
        return factory
        
    def new_region(self):
        factory = self.region_factory
        with self.context:
            return factory.create()

    def new_view(self, region=None, relative_path=u'/', title='A view', slot_definitions={}):
        region = region or self.region
        return UrlBoundView(region, relative_path, title, slot_definitions)


@istest
class WidgetBasics(object):
    @test(WebFixture)
    def basic_widget(self, fixture):
        """Basic widgets are created by adding children widgets to them, and the result is rendered in HTML"""
        
        class MyMessage(Div):
            def __init__(self, view):
                super(MyMessage, self).__init__(view)
                self.add_child(P(view, text=u'Hello World!'))
                self.add_children([P(view, text=u'a'), P(view, text=u'b')])

        message = MyMessage(fixture.view)
        
        widget_tester = WidgetTester(message)
        actual = widget_tester.render_html()
        
        vassert( actual == u'<div><p>Hello World!</p><p>a</p><p>b</p></div>' )

    @test(WebFixture)
    def visibility(self, fixture):
        """Widgets are rendered only if their .visible property is True."""
        
        class MyMessage(Widget):
            is_visible = True
            def __init__(self, view):
                super(MyMessage, self).__init__(view)
                self.add_child(P(view, text=u'你好世界!'))
                
            @property
            def visible(self):
                return self.is_visible
 
        message = MyMessage(fixture.view)
        
        widget_tester = WidgetTester(message)

        # Case: when visible
        message.is_visible = True
        actual = widget_tester.render_html()
        vassert( actual == u'<p>你好世界!</p>' )

        # Case: when not visible
        message.is_visible = False
        actual = widget_tester.render_html()
        vassert( actual == u'' )

    @test(WebFixture)
    def widget_factories_and_args(self, fixture):
        """Widgets can be created from factories which allow you to supply widget-specific args 
           and/or kwargs before a view is available."""
        
        class WidgetWithArgs(Widget):
            def __init__(self, view, arg, kwarg=None):
                super(WidgetWithArgs, self).__init__(view)
                self.saved_arg = arg
                self.saved_kwarg = kwarg

        factory = WidgetWithArgs.factory('a', kwarg='b')

        widget = factory.create(fixture.view)
        
        vassert( widget.saved_arg == 'a' )
        vassert( widget.saved_kwarg == 'b' )

    @test(WebFixture)
    def widget_factories_error(self, fixture):
        """Supplying arguments to .factory that do not match those of the Widget's __init__ is reported to the programmer.."""
        
        class WidgetWithArgs(Widget):
            def __init__(self, view, arg, kwarg=None):
                super(WidgetWithArgs, self).__init__(view)
                self.saved_arg = arg
                self.saved_kwarg = kwarg

        def check_exc(ex):
            vassert( str(ex).startswith("An attempt was made to create a WidgetFactory for <class 'reahl.web_dev.widgets.widgetbasics.WidgetWithArgs'> with arguments that do not match what is expected for <class 'reahl.web_dev.widgets.widgetbasics.WidgetWithArgs'>") )
        with expected(IncorrectArgumentError, test=check_exc):
            factory = WidgetWithArgs.factory('a', 'b', 'c')

    @test(WebFixture)
    def widget_construct_error(self, fixture):
        """Passing anything other than a View as a Widget's view argument on construction results in an error."""

        with expected(IsInstance):
            Widget(EmptyStub())

    @test(WebFixture)
    def widget_adding_error(self, fixture):
        """Passing anything other than other Widgets to .add_child or add_children results in an error."""

        widget = Widget(fixture.view)

        with expected(IsInstance):
            widget.add_child(EmptyStub())

        with expected(IsInstance):
            widget.add_children([Widget(fixture.view), EmptyStub()])

    @test(WebFixture)
    def basic_working_of_slots(self, fixture):
        """Slots are special Widgets that can be added to the main window. The contents of a
           Slot are then supplied (differently) by different Views."""

        class MyMainWindow(Widget):
            def __init__(self, view):
                super(MyMainWindow, self).__init__(view)
                self.add_child(Slot(view, u'slot1'))
                self.add_child(Slot(view, u'slot2'))

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(MyMainWindow)

                home = self.define_view(u'/', title=u'Home')
                home.set_slot(u'slot1', P.factory(text=u'a'))
                home.set_slot(u'slot2', P.factory(text=u'b'))

                other = self.define_view(u'/other', title=u'Other')
                other.set_slot(u'slot1', P.factory(text=u'other'))

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)
        
        browser.open('/')
        [slot1_p, slot2_p] = browser.lxml_html.xpath('//p')
        vassert( slot1_p.text == u'a' )
        vassert( slot2_p.text == u'b' )

        browser.open('/other')
        [slot1_p] = browser.lxml_html.xpath('//p')
        vassert( slot1_p.text == u'other' )


    @test(WebFixture)
    def defaults_for_slots(self, fixture):
        """A Widget can have defaults for its slots."""

        class MyMainWindow(Widget):
            def __init__(self, view):
                super(MyMainWindow, self).__init__(view)
                self.add_child(Slot(view, u'slot3'))
                self.add_default_slot(u'slot3', P.factory(text=u'default'))
               
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(MyMainWindow)
                self.define_view(u'/', title=u'Home')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)
        
        browser.open('/')
        [slot3_p] = browser.lxml_html.xpath('//p')
        vassert( slot3_p.text == u'default' )


    @test(WebFixture)
    def activating_javascript(self, fixture):
        """The JavaScript snippets of all Widgets are collected in a jQuery.ready() function by"""
        """ an automatically inserted Widget in the slot named reahl_header.  Duplicate snippets are removed."""
        @stubclass(Widget)
        class WidgetWithJavaScript(Widget):
            def __init__(self, view, fake_js):
                super(WidgetWithJavaScript, self).__init__(view)
                self.fake_js = fake_js
                
            def get_js(self, context=None):
                return [self.fake_js]

        class MyMainWindow(Widget):
            def __init__(self, view):
                super(MyMainWindow, self).__init__(view)
                self.add_child(Slot(view, u'reahl_header'))
                self.add_child(WidgetWithJavaScript(view, u'js1'))
                self.add_child(WidgetWithJavaScript(view, u'js2'))
                self.add_child(WidgetWithJavaScript(view, u'js1'))

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(MyMainWindow)
                self.define_view(u'/', title=u'Home')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)
        
        browser.open('/')
        rendered_js = browser.lxml_html.xpath('//script')[1].text
        vassert( rendered_js == u'\njQuery(document).ready(function($){\n$(\'body\').addClass(\'enhanced\');\njs1\njs2\n\n});\n' )
        
        number_of_duplicates = rendered_js.count('js1') - 1
        vassert( number_of_duplicates == 0 )


    class AttachmentScenarios(WebFixture):
        @scenario
        def javascript(self):
            self.static_file = u'/static/reahl.js'
            self.attachment_label = u'js'

        @scenario
        def css(self):
            self.static_file = u'/static/reahl.css'
            self.attachment_label = u'css'

    @test(AttachmentScenarios)
    def shipping_attachments(self, fixture):
        """The JavaScript and CSS files listed in the .reahlproject are discovered when the webserver starts up, and put into one file
           for inclusion on each page of a Reahl web application."""

        webapp = fixture.new_webapp(enable_js=True)
        browser = Browser(webapp)
        browser.open(fixture.static_file)

        def broken_but_comparable_minify(some_js):
            minified = re.sub(u'/\*.*\*/', u'', some_js)
            minified = re.sub(u'//.*\n', u'', minified)
            minified = re.sub(u'\n', u'', minified)
            minified = re.sub(u'\t', u'', minified)
            minified = re.sub(u' ', u'', minified)
            return minified

        import reahl.web
        reahl_egg = ReahlEgg(pkg_resources.require('reahl-web')[0])
        attachments = reahl_egg.find_attachments(fixture.attachment_label)

        # Only the js/css of one widget is checked to check the mechanism...
        with open(attachments[0].filename, u'r') as snippet_file:
            snippet = broken_but_comparable_minify(snippet_file.read())

        served_statics = broken_but_comparable_minify(browser.raw_html)

        vassert( served_statics.find(snippet) > 0 )








