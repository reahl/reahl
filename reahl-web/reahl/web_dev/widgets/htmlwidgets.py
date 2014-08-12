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


from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import vassert, expected
from reahl.stubble import EmptyStub

from reahl.web.ui import *
from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture

@test(WebFixture)
def basic_fixed_attributes(fixture):
    """How the static attributes of a Widget can be manipulated, queried and rendered."""

    widget = HTMLElement(fixture.view, 'x')
    tester = WidgetTester(widget)

    # Adding / setting
    widget.set_attribute('attr1', 'value1')
    widget.add_to_attribute('listattr', ['one', 'two'])
    widget.add_to_attribute('listattr', ['three'])
    
    # Querying
    vassert( widget.has_attribute('attr1') )
    vassert( widget.has_attribute('listattr') )
    vassert( not widget.has_attribute('notthere') )
    vassert( widget.attributes.v['attr1'] == 'value1' )
    vassert( widget.attributes.v['listattr'] == 'one three two' )
    
    # Rendering
    rendered = tester.render_html()
    vassert( rendered == '<x attr1="value1" listattr="one three two">' )

    # Rendering - the order of attributes in the rendered output
    widget.set_attribute('id', '123')
    widget.add_to_attribute('class', ['z', 'b'])
    rendered = tester.render_html()
    vassert( rendered == '<x id="123" attr1="value1" listattr="one three two" class="b z">' )


@test(WebFixture)
def handy_methods(fixture):
    """Some handy methods for special attributes."""

    widget = HTMLElement(fixture.view, 'x')
    tester = WidgetTester(widget)

    widget.set_title('the title')
    widget.set_id('the id')
    widget.append_class('two')
    widget.append_class('one')

    rendered = tester.render_html()
    vassert( rendered == '<x id="the id" title="the title" class="one two">' )

@test(WebFixture)
def dynamically_determining_attributes(fixture):
    """A Widget can determine its attribute values at the latest possible stage, based on changing data."""

    class WidgetWithDynamicAttributes(HTMLElement):
        state = '1'
        @property
        def attributes(self):
            attributes = super(WidgetWithDynamicAttributes, self).attributes
            attributes.set_to('dynamic', self.state)
            attributes.add_to('dynamiclist', [self.state])
            attributes.add_to('not-there', ['a value'])
            attributes.remove_from('not-there', ['a value'])
            return attributes

    widget = WidgetWithDynamicAttributes(fixture.view, 'x')
    widget.set_attribute('fixed', 'value1')
    tester = WidgetTester(widget)

    widget.state = '1'
    rendered = tester.render_html()
    vassert( rendered == '<x dynamic="1" dynamiclist="1" fixed="value1">' )

    widget.state = '2'
    rendered = tester.render_html()
    vassert( rendered == '<x dynamic="2" dynamiclist="2" fixed="value1">' )


@test(WebFixture)
def wrapper_widgets(fixture):
    """Sometimes, a HTMLElement is "wrapped" by an Input which represents the HTMLElement. In this case,
       dynamic as well as static attributes for the wrapped HTMLElement are obtained from its Input wrapper."""

    class WrapperWidget(Input):
        def get_wrapped_html_attributes(self, attributes):
            attributes.set_to('set-by-wrapper', 'rhythm and poetry')
            return attributes

    field = Field()
    field.bind('aname', field)
    wrapper = WrapperWidget(Form(fixture.view, 'formname'), field)
    widget = HTMLElement(fixture.view, 'x', wrapper_widget=wrapper)
    tester = WidgetTester(widget)

    # Case: dynamic attributes are supplied by the wrapper
    rendered = tester.render_html()
    vassert( rendered == '<x set-by-wrapper="rhythm and poetry">' )

    # Case:several methods to set static attributes are delegated from the wrapper
    wrapper.set_id('myid')
    wrapper.set_title('mytitle')
    wrapper.add_to_attribute('list-attribute', ['one', 'two'])
    wrapper.set_attribute('an-attribute', 'a value')

    rendered = tester.render_html()
    vassert( rendered == '<x id="myid" an-attribute="a value" list-attribute="one two" set-by-wrapper="rhythm and poetry" title="mytitle">' )

@test(WebFixture)
def all_html_widgets_have_css_ids(fixture):
    """A Widget (for HTML) can have a css_id. If accessed, but not set, a ProgrammerError is raised."""
    
    widget = HTMLElement(fixture.view, 'x')
    widget.tag_name = 'x'
    tester = WidgetTester(widget)

    widget._css_id = None
    with expected(ProgrammerError): 
        widget.css_id
    
    widget._css_id = 'myid'
    vassert( widget.css_id == 'myid' )

@test(WebFixture)
def jquery_support(fixture):
    """Each HTML Widget has a jquery_selector that targets it uniquely. By default
       this makes use of the css_id of the Widget, which thus need to be set, however
       subclasses may override this behaviour. The jquery_selector (or a more lax 
       selector for the Widget) can also be further narrowed to a specific
       jquery selector context."""
    
    widget = HTMLElement(fixture.view, 'x')
    tester = WidgetTester(widget)

    with expected(ProgrammerError):  # css id not set
        widget.jquery_selector

    widget.set_id('anid')
    vassert( widget.jquery_selector == '"#%s"' % widget.css_id )
    vassert( widget.attributes['id'].as_html_value() == widget.css_id )
    
    contextualised = widget.contextualise_selector('selector', 'context')
    vassert( contextualised ==  'selector, "context"' )

    contextualised = widget.contextualise_selector('selector', None)
    vassert( contextualised ==  'selector' )

@test(WebFixture)
def single_tags(fixture):
    """Definition of a HTMLElement."""
    
    single_tag = HTMLElement(fixture.view, 'single')
    tester = WidgetTester(single_tag)

    with expected(AssertionError):
        single_tag.add_child(P(fixture.view))

    rendered = tester.render_html()
    vassert( rendered == '<single>' )

@test(WebFixture)
def closing_tags(fixture):
    """Definition of a HTMLElement with children."""
    
    closing_tag = HTMLElement(fixture.view, 'closing', children_allowed=True)
    tester = WidgetTester(closing_tag)

    closing_tag.add_child(P(fixture.view))

    rendered = tester.render_html()
    vassert( rendered == '<closing><p></p></closing>' )


class Scenarios(WebFixture):
    @scenario
    def text_node(self):
        self.widget = TextNode(self.view, 'text')
        self.expected_html = 'text'

    @scenario
    def a1(self):
        self.widget = A(self.view, Url('/xyz'))
        self.expected_html = '<a href="/xyz"></a>'
        
    @scenario
    def a2(self):
        self.widget = A(self.view, Url('/xyz'), description='description')
        self.expected_html = '<a href="/xyz">description</a>'

    @scenario
    def a3(self):
        def disallowed(): return False
        self.widget = A(self.view, Url('/xyz'), description='description', write_check=disallowed)
        self.expected_html = '<a>description</a>'
        
    @scenario
    def h(self):
        self.widget = H(self.view, 2)
        self.expected_html = '<h2></h2>'
        
    @scenario
    def p1(self):
        self.widget = P(self.view)
        self.expected_html = '<p></p>'

    @scenario
    def p2(self):
        self.widget = P(self.view, text='text')
        self.expected_html = '<p>text</p>'

    @scenario
    def p_with_slots(self):
        template_p = P(self.view, text='the {0} {{brown}} {slot2} jumps')
        self.widget = template_p.format(Span(self.view, text='quick'), slot2=Span(self.view, text='fox'))
        self.expected_html = '<p>the <span>quick</span> {brown} <span>fox</span> jumps</p>'
        
    @scenario
    def title(self):
        self.widget = Title(self.view, 'text')
        self.expected_html = '<title>text</title>'
        
    @scenario
    def link(self):
        self.widget = Link(self.view, 'rr', 'hh', 'tt')
        self.expected_html = '<link href="hh" rel="rr" type="tt">'
        
    @scenario
    def header(self):
        self.widget = Header(self.view)
        self.expected_html = '<header></header>'
        
    @scenario
    def footer(self):
        self.widget = Footer(self.view)
        self.expected_html = '<footer></footer>'
        
    @scenario
    def li(self):
        self.widget = Li(self.view)
        self.expected_html = '<li></li>'
        
    @scenario
    def ul(self):
        self.widget = Ul(self.view)
        self.expected_html = '<ul></ul>'

    @scenario
    def img1(self):
        self.widget = Img(self.view, 'ss')
        self.expected_html = '<img src="ss">'
        
    @scenario
    def img2(self):
        self.widget = Img(self.view, 'ss', alt='aa')
        self.expected_html = '<img alt="aa" src="ss">'

    @scenario
    def span(self):
        self.widget = Span(self.view)
        self.expected_html = '<span></span>'
        
    @scenario
    def span_with_text(self):
        self.widget = Span(self.view, text='some text')
        self.expected_html = '<span>some text</span>'
        
    @scenario
    def div(self):
        self.widget = Div(self.view)
        self.expected_html = '<div></div>'

    @scenario
    def caption(self):
        self.widget = Caption(self.view, text='some text')
        self.expected_html = '<caption>some text</caption>'
        
    @scenario
    def col(self):
        self.widget = Col(self.view, span='2')
        self.expected_html = '<col span="2">'

    @scenario
    def colgroup(self):
        self.widget = Colgroup(self.view, span='2')
        self.expected_html = '<colgroup span="2"></colgroup>'

    @scenario
    def thead(self):
        self.widget = Thead(self.view)
        self.expected_html = '<thead></thead>'

    @scenario
    def tfoot(self):
        self.widget = Tfoot(self.view)
        self.expected_html = '<tfoot></tfoot>'

    @scenario
    def tbody(self):
        self.widget = Tbody(self.view)
        self.expected_html = '<tbody></tbody>'

    @scenario
    def tr(self):
        self.widget = Tr(self.view)
        self.expected_html = '<tr></tr>'

    @scenario
    def th(self):
        self.widget = Th(self.view)
        self.expected_html = '<th></th>'

    @scenario
    def td(self):
        self.widget = Td(self.view)
        self.expected_html = '<td></td>'

    @scenario
    def table(self):
        self.widget = Table(self.view, caption_text='my caption', summary='my summary')
        self.expected_html = '<table summary="my summary"><caption>my caption</caption></table>'
        
    @scenario
    def nav(self):
        self.widget = Nav(self.view)
        self.expected_html = '<nav></nav>'
        
    @scenario
    def article(self):
        self.widget = Article(self.view)
        self.expected_html = '<article></article>'
        
    @scenario
    def label1(self):
        self.widget = Label(self.view)
        self.expected_html = '<label></label>'
        
    @scenario
    def label2(self):
        self.widget = Label(self.view, text='text')
        self.expected_html = '<label>text</label>'
        
    @scenario
    def fieldset1(self):
        self.widget = FieldSet(self.view)
        self.expected_html = '<fieldset></fieldset>'
        
    @scenario
    def fieldset2(self):
        self.widget = FieldSet(self.view, label_text='text')
        self.expected_html = '<fieldset><label>text</label></fieldset>'

@test(Scenarios)
def basic_html_widgets(fixture):
    """Several basic widgets merely correspond to html elements."""
    
    tester = WidgetTester(fixture.widget)
    rendered_html = tester.render_html()
    vassert( rendered_html == fixture.expected_html )

@test(WebFixture)
def view_rights_propagate_to_a(fixture):
    """The access rights specified for a View are propagated to an A, made from a Bookmark to that View."""
    fixture.view.write_check = EmptyStub()
    fixture.view.read_check = EmptyStub()
    a = A.from_bookmark(fixture.view, fixture.view.as_bookmark())
    vassert( a.read_check is fixture.view.read_check )
    vassert( a.write_check is fixture.view.write_check )

@test(WebFixture)
def text_node_can_vary(fixture):
    """A TextNode can vary its text if constructed with a getter for the value instead of a hardcoded value."""
    def getter():
        return fixture.current_value
    widget = TextNode(fixture.view, getter)
    tester = WidgetTester(widget)
    
    fixture.current_value = 'stuff'
    rendered = tester.render_html()
    vassert( rendered == 'stuff' )

    fixture.current_value = 'other'
    rendered = tester.render_html()
    vassert( rendered == 'other' )

@test(WebFixture)
def text_node_escapes_html(fixture):
    """The text of a TextNode is html-escaped."""

    widget = TextNode(fixture.view, '<tag>')
    tester = WidgetTester(widget)
    
    rendered = tester.render_html()
    vassert( rendered == '&lt;tag&gt;' )


@test(WebFixture)
def literal_html(fixture):
    """The LiteralHTML Widget just renders a chunk of HTML, but can answer queries about images in that HTML."""
    
    contents = '<img src="_some_images/piet.pdf  "> <img src   = \' _some_images/koos was-^-hoêr.jpg\'>'
    literal_html = LiteralHTML(fixture.view, contents)
    tester = WidgetTester(literal_html)

    rendered_html = tester.render_html()
    vassert( rendered_html == contents )

    # Case: when the content is transformed
    def text_transformation(text):
        return text.replace('im', 'IM')
    literal_html = LiteralHTML(fixture.view, contents, transform=text_transformation)
    tester = WidgetTester(literal_html)

    rendered_html = tester.render_html()
    vassert( rendered_html == text_transformation(contents) )

@test(WebFixture)
def head(fixture):
    """Head corresponds with the head HTML element, can have a title and always has a special Slot used by the framework."""

    head = Head(fixture.view, 'a title')
    tester = WidgetTester(head)

    reahl_header_slot = head.children[1]
    vassert( isinstance(reahl_header_slot, Slot) )
    vassert( reahl_header_slot.name == 'reahl_header' )

    rendered_html = tester.render_html()
    vassert( rendered_html == '<head><title>a title</title></head>' )

@test(WebFixture)
def body(fixture):
    """Body corresponds with the body HTML element, and always has a special Slot at its end used by the framework."""
    body = Body(fixture.view)
    tester = WidgetTester(body)

    body.add_child(P(fixture.view))
    
    reahl_footer_slot = body.children[1]
    vassert( isinstance(reahl_footer_slot, Slot) )
    vassert( reahl_footer_slot.name == 'reahl_footer' )

    rendered_html = tester.render_html()
    vassert( rendered_html == '<body><p></p></body>' )




