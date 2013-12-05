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


from nose.tools import istest
from reahl.tofu import Fixture, test, scenario
from reahl.tofu import vassert, expected
from reahl.stubble import EmptyStub

from reahl.web.fw import Url
from reahl.web.ui import *
from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture

@istest
class HTMLWidgetBasics(object):
    @test(WebFixture)
    def basic_fixed_attributes(self, fixture):
        """How the static attributes of a Widget can be manipulated, queried and rendered."""

        widget = HTMLElement(fixture.view, u'x')
        tester = WidgetTester(widget)

        # Adding / setting
        widget.set_attribute(u'attr1', u'value1')
        widget.add_to_attribute(u'listattr', [u'one', u'two'])
        widget.add_to_attribute(u'listattr', [u'three'])
        
        # Querying
        vassert( widget.has_attribute(u'attr1') )
        vassert( widget.has_attribute(u'listattr') )
        vassert( not widget.has_attribute(u'notthere') )
        vassert( widget.attributes.v[u'attr1'] == u'value1' )
        vassert( widget.attributes.v[u'listattr'] == u'one three two' )
        
        # Rendering
        rendered = tester.render_html()
        vassert( rendered == u'<x attr1="value1" listattr="one three two">' )

        # Rendering - the order of attributes in the rendered output
        widget.set_attribute(u'id', u'123')
        widget.add_to_attribute(u'class', [u'z', u'b'])
        rendered = tester.render_html()
        vassert( rendered == u'<x id="123" attr1="value1" listattr="one three two" class="b z">' )


    @test(WebFixture)
    def handy_methods(self, fixture):
        """Some handy methods for special attributes."""

        widget = HTMLElement(fixture.view, u'x')
        tester = WidgetTester(widget)

        widget.set_title(u'the title')
        widget.set_id(u'the id')
        widget.append_class(u'two')
        widget.append_class(u'one')

        rendered = tester.render_html()
        vassert( rendered == u'<x id="the id" title="the title" class="one two">' )

    @test(WebFixture)
    def dynamically_determining_attributes(self, fixture):
        """A Widget can determine its attribute values at the latest possible stage, based on changing data."""

        class WidgetWithDynamicAttributes(HTMLElement):
            state = u'1'
            @property
            def attributes(self):
                attributes = super(WidgetWithDynamicAttributes, self).attributes
                attributes.set_to(u'dynamic', self.state)
                attributes.add_to(u'dynamiclist', [self.state])
                attributes.add_to(u'not-there', [u'a value'])
                attributes.remove_from(u'not-there', [u'a value'])
                return attributes

        widget = WidgetWithDynamicAttributes(fixture.view, u'x')
        widget.set_attribute(u'fixed', u'value1')
        tester = WidgetTester(widget)

        widget.state = u'1'
        rendered = tester.render_html()
        vassert( rendered == u'<x dynamic="1" dynamiclist="1" fixed="value1">' )

        widget.state = u'2'
        rendered = tester.render_html()
        vassert( rendered == u'<x dynamic="2" dynamiclist="2" fixed="value1">' )


    @test(WebFixture)
    def wrapper_widgets(self, fixture):
        """Sometimes, a HTMLElement is "wrapped" by an Input which represents the HTMLElement. In this case,
           dynamic as well as static attributes for the wrapped HTMLElement are obtained from its Input wrapper."""

        class WrapperWidget(Input):
            def get_wrapped_html_attributes(self, attributes):
                attributes.set_to(u'set-by-wrapper', u'rhythm and poetry')
                return attributes

        field = Field()
        field.bind('aname', field)
        wrapper = WrapperWidget(Form(fixture.view, u'formname'), field)
        widget = HTMLElement(fixture.view, u'x', wrapper_widget=wrapper)
        tester = WidgetTester(widget)

        # Case: dynamic attributes are supplied by the wrapper
        rendered = tester.render_html()
        vassert( rendered == u'<x set-by-wrapper="rhythm and poetry">' )

        # Case:several methods to set static attributes are delegated from the wrapper
        wrapper.set_id(u'myid')
        wrapper.set_title(u'mytitle')
        wrapper.add_to_attribute(u'list-attribute', [u'one', u'two'])
        wrapper.set_attribute(u'an-attribute', u'a value')

        rendered = tester.render_html()
        vassert( rendered == u'<x id="myid" an-attribute="a value" list-attribute="one two" set-by-wrapper="rhythm and poetry" title="mytitle">' )

    @test(WebFixture)
    def all_html_widgets_have_css_ids(self, fixture):
        """A Widget (for HTML) can have a css_id. If accessed, but not set, a ProgrammerError is raised."""
        
        widget = HTMLElement(fixture.view, u'x')
        widget.tag_name = u'x'
        tester = WidgetTester(widget)

        widget._css_id = None
        with expected(ProgrammerError): 
            widget.css_id
        
        widget._css_id = u'myid'
        vassert( widget.css_id == u'myid' )

    @test(WebFixture)
    def jquery_support(self, fixture):
        """Each HTML Widget has a jquery_selector that targets it uniquely. By default
           this makes use of the css_id of the Widget, which thus need to be set, however
           subclasses may override this behaviour. The jquery_selector (or a more lax 
           selector for the Widget) can also be further narrowed to a specific
           jquery selector context."""
        
        widget = HTMLElement(fixture.view, u'x')
        tester = WidgetTester(widget)

        with expected(ProgrammerError):  # css id not set
            widget.jquery_selector

        widget.set_id(u'anid')
        vassert( widget.jquery_selector == u'"#%s"' % widget.css_id )
        vassert( widget.attributes[u'id'].as_html_value() == widget.css_id )
        
        contextualised = widget.contextualise_selector(u'selector', u'context')
        vassert( contextualised ==  u'selector, "context"' )

        contextualised = widget.contextualise_selector(u'selector', None)
        vassert( contextualised ==  u'selector' )

    @test(WebFixture)
    def single_tags(self, fixture):
        """Definition of a HTMLElement."""
        
        single_tag = HTMLElement(fixture.view, u'single')
        tester = WidgetTester(single_tag)

        with expected(AssertionError):
            single_tag.add_child(P(fixture.view))

        rendered = tester.render_html()
        vassert( rendered == u'<single>' )

    @test(WebFixture)
    def closing_tags(self, fixture):
        """Definition of a HTMLElement with children."""
        
        closing_tag = HTMLElement(fixture.view, u'closing', children_allowed=True)
        tester = WidgetTester(closing_tag)

        closing_tag.add_child(P(fixture.view))

        rendered = tester.render_html()
        vassert( rendered == u'<closing><p></p></closing>' )



@istest
class BasicHTMLWidgets(object):
    class Scenarios(WebFixture):
        @scenario
        def text_node(self):
            self.widget = TextNode(self.view, u'text')
            self.expected_html = u'text'

        @scenario
        def a1(self):
            self.widget = A(self.view, Url(u'/xyz'))
            self.expected_html = u'<a href="/xyz"></a>'
            
        @scenario
        def a2(self):
            self.widget = A(self.view, Url(u'/xyz'), description=u'description')
            self.expected_html = u'<a href="/xyz">description</a>'

        @scenario
        def a3(self):
            def disallowed(): return False
            self.widget = A(self.view, Url(u'/xyz'), description=u'description', write_check=disallowed)
            self.expected_html = u'<a>description</a>'
            
        @scenario
        def h(self):
            self.widget = H(self.view, 2)
            self.expected_html = u'<h2></h2>'
            
        @scenario
        def p1(self):
            self.widget = P(self.view)
            self.expected_html = u'<p></p>'

        @scenario
        def p2(self):
            self.widget = P(self.view, text=u'text')
            self.expected_html = u'<p>text</p>'

        @scenario
        def p_with_slots(self):
            template_p = P(self.view, text=u'the {0} {{brown}} {slot2} jumps')
            self.widget = template_p.format(Span(self.view, text=u'quick'), slot2=Span(self.view, text=u'fox'))
            self.expected_html = u'<p>the <span>quick</span> {brown} <span>fox</span> jumps</p>'
            
        @scenario
        def title(self):
            self.widget = Title(self.view, u'text')
            self.expected_html = u'<title>text</title>'
            
        @scenario
        def link(self):
            self.widget = Link(self.view, u'rr', u'hh', u'tt')
            self.expected_html = u'<link href="hh" rel="rr" type="tt">'
            
        @scenario
        def header(self):
            self.widget = Header(self.view)
            self.expected_html = u'<header></header>'
            
        @scenario
        def footer(self):
            self.widget = Footer(self.view)
            self.expected_html = u'<footer></footer>'
            
        @scenario
        def li(self):
            self.widget = Li(self.view)
            self.expected_html = u'<li></li>'
            
        @scenario
        def ul(self):
            self.widget = Ul(self.view)
            self.expected_html = u'<ul></ul>'
            
        @scenario
        def img1(self):
            self.widget = Img(self.view, u'ss')
            self.expected_html = u'<img src="ss">'
            
        @scenario
        def img2(self):
            self.widget = Img(self.view, u'ss', alt=u'aa')
            self.expected_html = u'<img alt="aa" src="ss">'
            
        @scenario
        def span(self):
            self.widget = Span(self.view)
            self.expected_html = u'<span></span>'
            
        @scenario
        def span_with_text(self):
            self.widget = Span(self.view, text=u'some text')
            self.expected_html = u'<span>some text</span>'
            
        @scenario
        def div(self):
            self.widget = Div(self.view)
            self.expected_html = u'<div></div>'
            
        @scenario
        def nav(self):
            self.widget = Nav(self.view)
            self.expected_html = u'<nav></nav>'
            
        @scenario
        def article(self):
            self.widget = Article(self.view)
            self.expected_html = u'<article></article>'
            
        @scenario
        def label1(self):
            self.widget = Label(self.view)
            self.expected_html = u'<label></label>'
            
        @scenario
        def label2(self):
            self.widget = Label(self.view, text=u'text')
            self.expected_html = u'<label>text</label>'
            
        @scenario
        def fieldset1(self):
            self.widget = FieldSet(self.view)
            self.expected_html = u'<fieldset></fieldset>'
            
        @scenario
        def fieldset2(self):
            self.widget = FieldSet(self.view, label_text=u'text')
            self.expected_html = u'<fieldset><label>text</label></fieldset>'

    @test(Scenarios)
    def basic_html_widgets(self, fixture):
        """Several basic widgets merely correspond to html elements."""
        
        tester = WidgetTester(fixture.widget)
        rendered_html = tester.render_html()
        vassert( rendered_html == fixture.expected_html )

    @test(WebFixture)
    def view_rights_propagate_to_a(self, fixture):
        """The access rights specified for a View are propagated to an A, made from a Bookmark to that View."""
        fixture.view.write_check = EmptyStub()
        fixture.view.read_check = EmptyStub()
        a = A.from_bookmark(fixture.view, fixture.view.as_bookmark())
        vassert( a.read_check is fixture.view.read_check )
        vassert( a.write_check is fixture.view.write_check )
    
    @test(WebFixture)
    def text_node_can_vary(self, fixture):
        """A TextNode can vary its text if constructed with a getter for the value instead of a hardcoded value."""
        def getter():
            return fixture.current_value
        widget = TextNode(fixture.view, getter)
        tester = WidgetTester(widget)
        
        fixture.current_value = u'stuff'
        rendered = tester.render_html()
        vassert( rendered == u'stuff' )

        fixture.current_value = u'other'
        rendered = tester.render_html()
        vassert( rendered == u'other' )

    @test(WebFixture)
    def text_node_escapes_html(self, fixture):
        """The text of a TextNode is html-escaped."""

        widget = TextNode(fixture.view, u'<tag>')
        tester = WidgetTester(widget)
        
        rendered = tester.render_html()
        vassert( rendered == u'&lt;tag&gt;' )


    @test(WebFixture)
    def literal_html(self, fixture):
        """The LiteralHTML Widget just renders a chunk of HTML, but can answer queries about images in that HTML."""
        
        contents = u'<img src="_some_images/piet.pdf  "> <img src   = \' _some_images/koos was-^-hoêr.jpg\'>'
        literal_html = LiteralHTML(fixture.view, contents)
        tester = WidgetTester(literal_html)

        rendered_html = tester.render_html()
        vassert( rendered_html == contents )

        # Case: when the content is transformed
        def text_transformation(text):
            return text.replace(u'im', u'IM')
        literal_html = LiteralHTML(fixture.view, contents, transform=text_transformation)
        tester = WidgetTester(literal_html)

        rendered_html = tester.render_html()
        vassert( rendered_html == text_transformation(contents) )

    @test(WebFixture)
    def head(self, fixture):
        """Head corresponds with the head HTML element, can have a title and always has a special Slot used by the framework."""

        head = Head(fixture.view, u'a title')
        tester = WidgetTester(head)

        reahl_header_slot = head.children[1]
        vassert( isinstance(reahl_header_slot, Slot) )
        vassert( reahl_header_slot.name == u'reahl_header' )

        rendered_html = tester.render_html()
        vassert( rendered_html == u'<head><title>a title</title></head>' )

    @test(WebFixture)
    def body(self, fixture):
        """Body corresponds with the body HTML element, and always has a special Slot at its end used by the framework."""
        body = Body(fixture.view)
        tester = WidgetTester(body)

        body.add_child(P(fixture.view))
        
        reahl_footer_slot = body.children[1]
        vassert( isinstance(reahl_footer_slot, Slot) )
        vassert( reahl_footer_slot.name == u'reahl_footer' )

        rendered_html = tester.render_html()
        vassert( rendered_html == u'<body><p></p></body>' )




