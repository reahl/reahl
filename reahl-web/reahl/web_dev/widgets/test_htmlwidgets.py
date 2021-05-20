# Copyright 2013-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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




from reahl.tofu import scenario, Fixture, expected, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import EmptyStub, stubclass

from reahl.web.ui import *
from reahl.browsertools.browsertools import WidgetTester

from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
def test_basic_fixed_attributes(web_fixture):
    """How the static attributes of a Widget can be manipulated, queried and rendered."""

    fixture = web_fixture

    widget = HTMLElement(fixture.view, 'x')
    tester = WidgetTester(widget)

    # Adding / setting
    widget.set_attribute('attr1', 'value1')
    widget.add_to_attribute('listattr', ['one', 'two'])
    widget.add_to_attribute('listattr', ['three'])

    # Querying
    assert widget.has_attribute('attr1')
    assert widget.has_attribute('listattr')
    assert not widget.has_attribute('notthere')
    assert widget.attributes.v['attr1'] == 'value1'
    assert widget.attributes.v['listattr'] == 'one three two'

    # Rendering
    rendered = tester.render_html()
    assert rendered == '<x attr1="value1" listattr="one three two">'

    # Rendering - the order of attributes in the rendered output
    widget.set_attribute('id', '123')
    widget.add_to_attribute('class', ['z', 'b'])
    rendered = tester.render_html()
    assert rendered == '<x id="123" attr1="value1" listattr="one three two" class="b z">'


@with_fixtures(WebFixture)
def test_handy_methods(web_fixture):
    """Some handy methods for special attributes."""

    fixture = web_fixture

    widget = HTMLElement(fixture.view, 'x')
    tester = WidgetTester(widget)

    widget.set_title('the title')
    widget.set_id('the_id')
    widget.append_class('two')
    widget.append_class('one')

    rendered = tester.render_html()
    assert rendered == '<x id="the_id" title="the title" class="one two">'


@with_fixtures(WebFixture)
def test_dynamically_determining_attributes(web_fixture):
    """A Widget can determine its attribute values at the latest possible stage, based on changing data."""

    class WidgetWithDynamicAttributes(HTMLElement):
        state = '1'
        @property
        def attributes(self):
            attributes = super().attributes
            attributes.set_to('dynamic', self.state)
            attributes.add_to('dynamiclist', [self.state])
            attributes.add_to('not-there', ['a value'])
            attributes.remove_from('not-there', ['a value'])
            return attributes

    fixture = web_fixture

    widget = WidgetWithDynamicAttributes(fixture.view, 'x')
    widget.set_attribute('fixed', 'value1')
    tester = WidgetTester(widget)

    widget.state = '1'
    rendered = tester.render_html()
    assert rendered == '<x dynamic="1" dynamiclist="1" fixed="value1">'

    widget.state = '2'
    rendered = tester.render_html()
    assert rendered == '<x dynamic="2" dynamiclist="2" fixed="value1">'


@with_fixtures(WebFixture)
def test_delegating_setting_of_attributes(web_fixture):
    """One or more DelegatedAttributes instances can be added to an HTMLElement as `attribute_source` -- an
       object which the HTMLElement can use in order to let some other object modify or add to its attributes.
    """

    @stubclass(DelegatedAttributes)
    class MyDelegatedAttributesClass(DelegatedAttributes):
        def set_attributes(self, attributes):
            attributes.set_to('set-by-external-source', 'rhythm and poetry')

    fixture = web_fixture

    widget = HTMLElement(fixture.view, 'x')
    widget.add_attribute_source(MyDelegatedAttributesClass())
    tester = WidgetTester(widget)

    # Case: dynamic attributes are supplied by the wrapper
    rendered = tester.render_html()
    assert rendered == '<x set-by-external-source="rhythm and poetry">'


@with_fixtures(WebFixture)
def test_all_html_widgets_have_css_ids(web_fixture):
    """A Widget (for HTML) can have a css_id. If accessed, but not set, a ProgrammerError is raised."""

    fixture = web_fixture

    widget = HTMLElement(fixture.view, 'x')
    widget.tag_name = 'x'
    tester = WidgetTester(widget)

    widget._css_id = None
    with expected(ProgrammerError):
        widget.css_id

    widget._css_id = 'myid'
    assert widget.css_id == 'myid'


@with_fixtures(WebFixture)
def test_jquery_support(web_fixture):
    """Each HTML Widget has a jquery_selector that targets it uniquely. By default
       this makes use of the css_id of the Widget, which thus need to be set, however
       subclasses may override this behaviour. The jquery_selector (or a more lax
       selector for the Widget) can also be further narrowed to a specific
       jquery selector context."""

    fixture = web_fixture

    widget = HTMLElement(fixture.view, 'x')
    tester = WidgetTester(widget)

    with expected(ProgrammerError):  # css id not set
        widget.jquery_selector

    widget.set_id('anid')
    assert widget.jquery_selector == '"#%s"' % widget.css_id
    assert widget.attributes['id'].as_html_value() == widget.css_id

    contextualised = widget.contextualise_selector('selector', 'context')
    assert contextualised ==  'selector, "context"'

    contextualised = widget.contextualise_selector('selector', None)
    assert contextualised ==  'selector'


@with_fixtures(WebFixture)
def test_single_tags(web_fixture):
    """Definition of a HTMLElement."""

    fixture = web_fixture

    single_tag = HTMLElement(fixture.view, 'single')
    tester = WidgetTester(single_tag)

    with expected(AssertionError):
        single_tag.add_child(P(fixture.view))

    rendered = tester.render_html()
    assert rendered == '<single>'


@with_fixtures(WebFixture)
def test_closing_tags(web_fixture):
    """Definition of a HTMLElement with children."""

    fixture = web_fixture

    closing_tag = HTMLElement(fixture.view, 'closing', children_allowed=True)
    tester = WidgetTester(closing_tag)

    closing_tag.add_child(P(fixture.view))

    rendered = tester.render_html()
    assert rendered == '<closing><p></p></closing>'


@uses(web_fixture=WebFixture)
class WidgetScenarios(Fixture):

    @property
    def view(self):
        return self.web_fixture.view

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
        self.widget = ColGroup(self.view, span='2')
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
        self.widget = FieldSet(self.view, legend_text='text')
        self.expected_html = '<fieldset><legend>text</legend></fieldset>'


@with_fixtures(WidgetScenarios)
def test_basic_html_widgets(widget_scenarios):
    """Several basic widgets merely correspond to html elements."""

    tester = WidgetTester(widget_scenarios.widget)
    rendered_html = tester.render_html()
    assert rendered_html == widget_scenarios.expected_html


@with_fixtures(WebFixture)
def test_view_rights_propagate_to_a(web_fixture):
    """The access rights specified for a View are propagated to an A, made from a Bookmark to that View."""
    fixture = web_fixture

    fixture.view.write_check = EmptyStub()
    fixture.view.read_check = EmptyStub()
    a = A.from_bookmark(fixture.view, fixture.view.as_bookmark())
    assert a.read_check is fixture.view.read_check
    assert a.write_check is fixture.view.write_check


@with_fixtures(WebFixture)
def test_text_node_can_vary(web_fixture):
    """A TextNode can vary its text if constructed with a getter for the value instead of a hardcoded value."""

    fixture = web_fixture

    def getter():
        return fixture.current_value


    widget = TextNode(fixture.view, getter)
    tester = WidgetTester(widget)

    fixture.current_value = 'stuff'
    rendered = tester.render_html()
    assert rendered == 'stuff'

    fixture.current_value = 'other'
    rendered = tester.render_html()
    assert rendered == 'other'


@with_fixtures(WebFixture)
def test_text_node_escapes_html(web_fixture):
    """The text of a TextNode is html-escaped."""

    fixture = web_fixture

    widget = TextNode(fixture.view, '<tag> "Here" & \'there\'')
    tester = WidgetTester(widget)

    rendered = tester.render_html()
    assert rendered == '&lt;tag&gt; "Here" &amp; \'there\''


@with_fixtures(WebFixture)
def test_literal_html(web_fixture):
    """The LiteralHTML Widget just renders a chunk of HTML, but can answer queries about images in that HTML."""

    fixture = web_fixture

    contents = '<img src="_some_images/piet.pdf  "> <img src   = \' _some_images/koos was-^-hoêr.jpg\'>'
    literal_html = LiteralHTML(fixture.view, contents)
    tester = WidgetTester(literal_html)

    rendered_html = tester.render_html()
    assert rendered_html == contents

    # Case: when the content is transformed
    def text_transformation(text):
        return text.replace('im', 'IM')
    literal_html = LiteralHTML(fixture.view, contents, transform=text_transformation)
    tester = WidgetTester(literal_html)

    rendered_html = tester.render_html()
    assert rendered_html == text_transformation(contents)


@with_fixtures(WebFixture)
def test_head(web_fixture):
    """Head corresponds with the head HTML element, can have a title and always has a special Slot used by the framework."""

    fixture = web_fixture

    head = Head(fixture.view, 'a title')
    tester = WidgetTester(head)

    reahl_header_slot = head.children[1]
    assert isinstance(reahl_header_slot, Slot)
    assert reahl_header_slot.name == 'reahl_header'

    rendered_html = tester.render_html()
    assert rendered_html == '<head><title>a title</title></head>'


@with_fixtures(WebFixture)
def test_body(web_fixture):
    """Body corresponds with the body HTML element, and always has a special Slot at its end used by the framework."""

    fixture = web_fixture

    body = Body(fixture.view)
    tester = WidgetTester(body)

    body.add_child(P(fixture.view))

    reahl_footer_slot = body.children[-1]
    assert isinstance(reahl_footer_slot, Slot)
    assert reahl_footer_slot.name == 'reahl_footer'

    rendered_html = tester.render_html()
    assert rendered_html == '<body><div id="_reahl_out_of_bound_container"></div><p></p></body>'


@with_fixtures(WebFixture)
def test_html5_page(web_fixture):
    """An HTML5Page is an empty HTML 5 document using the header and body widgets."""

    fixture = web_fixture

    widget = HTML5Page(fixture.view, title='It: $current_title')
    widget.add_default_slot('slot1', P.factory())
    tester = WidgetTester(widget)

    rendered_html = tester.render_html()
    head = '<head><title>It: %s</title></head>' % fixture.view.title
    expected_regex = '^<!DOCTYPE html><html.*class="no-js"><script>.*</script>%s<body><div id="_reahl_out_of_bound_container"></div></body></html>$' % head
    assert re.match(expected_regex, rendered_html.replace('\n', ''))

    assert list(widget.default_slot_definitions.keys()) == ['slot1']
