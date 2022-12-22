# Copyright 2015-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from sqlalchemy import Column, String, Integer

from reahl.tofu import scenario, Fixture, uses, expected
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import XPath, Browser
from reahl.browsertools.browsertools import WidgetTester
from reahl.component.modelinterface import ExposedNames, Field, BooleanField, Event, Choice, ChoiceField,\
    MultiChoiceField, IntegerField, Action
from reahl.component.exceptions import DomainException
from reahl.web.fw import Url, ValidationException
from reahl.web.bootstrap.ui import A, Div, FieldSet
from reahl.web.bootstrap.forms import Button, FormLayout, InlineFormLayout, GridFormLayout, Form, ChoicesLayout,\
    TextInput, CheckboxInput, PrimitiveCheckboxInput, RadioButtonSelectInput, ButtonLayout
from reahl.web.bootstrap.grid import ResponsiveSize

from reahl.web_dev.fixtures import WebFixture
from reahl.sqlalchemysupport import Session, Base
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture


@uses(web_fixture=WebFixture)
class FormLayoutScenarios(Fixture):

    def new_widget(self):
        return Div(self.web_fixture.view).use_layout(self.layout)

    @scenario
    def basic_form(self):
        self.layout = FormLayout()
        self.expected_html = '<div></div>'

    @scenario
    def inline_form(self):
        self.layout = InlineFormLayout()
        self.expected_html = '<div class="form-inline"></div>'

    @scenario
    def grid_form(self):
        self.layout = GridFormLayout(ResponsiveSize(xl=4), ResponsiveSize(xl=8))
        self.expected_html = '<div></div>'


@with_fixtures(WebFixture, FormLayoutScenarios)
def test_basic_form_layouts(web_fixture, form_layout_scenarios):
    """There are three basic layouts of forms in bootstrap."""

    tester = WidgetTester(form_layout_scenarios.widget)
    actual = tester.render_html()
    assert actual == form_layout_scenarios.expected_html


@uses(web_fixture=WebFixture)
class FormLayoutFixture(Fixture):
    form_group_xpath = '//form/div[contains(@class, "form-group")]'

    def new_domain_object(self):
        class StubDomainObject:
            fields = ExposedNames()
            fields.an_attribute = lambda i: Field(label='Some input', required=True)
        return StubDomainObject()

    def form_contains_form_group(self, browser):
        return browser.get_xpath_count(self.form_group_xpath) == 1

    def get_form_group_children(self, browser, index=0):
        return browser.xpath( '%s[%s]/*' % (self.form_group_xpath, index+1) )

    def get_form_group(self, browser, index=0):
        form_groups = browser.xpath('%s[%s]' % (self.form_group_xpath, index+1))
        return form_groups[index]

    def get_form_group_highlight_marks(self, browser, index=0):
        def is_form_control_element(element):
            return 'class' in element.attrib \
                   and 'form-control' in element.attrib['class']
        [some_input] = [element for element in self.get_form_group_children(browser, index=index)
                           if is_form_control_element(element)]
        return [mark for mark in some_input.attrib['class'].split(' ')
                     if mark.startswith('is-')]

    def get_form_group_errors(self, browser, index=0):
        def is_error_element(element):
            return 'class' in element.attrib \
                   and 'invalid-feedback' in element.attrib['class']
        def is_visible(element):
            return not (('style' in element.attrib) and ('display: none' in element.attrib['style']))

        return [element for element in self.get_form_group_children(browser, index=index)
                        if is_error_element(element) and is_visible(element) ]

    def get_label_in_form_group(self, browser, form_group_index=0):
        return browser.xpath('%s[%s]/div/label' % (self.form_group_xpath, form_group_index+1))


@with_fixtures(WebFixture, FormLayoutFixture)
def test_adding_basic_input(web_fixture, form_layout_fixture):
    """Adding an input to a FormLayout, adds it in a bootstrap form-group with Some input."""
    fixture = form_layout_fixture

    class FormWithInputAddedUsingDefaults(Form):
        def __init__(self, view):
            super().__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute))

    browser = Browser(web_fixture.new_wsgi_app(child_factory=FormWithInputAddedUsingDefaults.factory()))
    browser.open('/')

    assert fixture.form_contains_form_group(browser)

    [label, input_widget] = fixture.get_form_group_children(browser)

    # form-group has a label, correctly set up for bootstrap
    assert label.tag == 'label'
    assert label.attrib['for'] == input_widget.attrib['id']
    assert label.text == 'Some input'

    # form-group has an input, correctly set up for bootstrap
    assert input_widget.tag == 'input'
    assert input_widget.attrib['name'] == 'aform-an_attribute'


@with_fixtures(WebFixture, FormLayoutFixture)
def test_grid_form_layouts(web_fixture, form_layout_fixture):
    """A GridFormLayout adds the Label and Input of each added input in separate columns sized like you specify"""
    fixture = form_layout_fixture

    class FormWithGridFormLayout(Form):
        def __init__(self, view):
            super().__init__(view, 'aform')
            self.use_layout(GridFormLayout(ResponsiveSize(lg=4), ResponsiveSize(lg=8)))
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute), help_text='some help')

    browser = Browser(web_fixture.new_wsgi_app(child_factory=FormWithGridFormLayout.factory()))
    browser.open('/')

    [label_column, input_column] = fixture.get_form_group_children(browser)
    assert label_column.tag == 'div'
    assert 'col-lg-4' in label_column.attrib['class'].split(' ')
    assert 'column-label' in label_column.attrib['class'].split(' ')

    [label] = fixture.get_label_in_form_group(browser)
    assert 'col-form-label' in label.attrib['class'].split(' ')

    assert input_column.tag == 'div'
    assert 'col-lg-8' in input_column.attrib['class'].split(' ')
    assert 'column-input' in input_column.attrib['class'].split(' ')

    [input_, help_text] = input_column.getchildren()
    assert input_.tag == 'input'
    assert help_text.tag == 'p'
    assert 'form-text' in help_text.attrib['class'].split(' ')


@with_fixtures(WebFixture, FormLayoutFixture)
def test_inline_form_layouts(web_fixture, form_layout_fixture):
    """An InlineFormLayout adds the Label and Input of each added input next to each other, with some space between them."""
    fixture = form_layout_fixture

    class FormWithInlineFormLayout(Form):
        def __init__(self, view):
            super().__init__(view, 'aform')
            self.use_layout(InlineFormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute), help_text='some help')

    browser = Browser(web_fixture.new_wsgi_app(child_factory=FormWithInlineFormLayout.factory()))
    browser.open('/')

    [label, input_, help_text] = fixture.get_form_group_children(browser)

    #check spacing specified between label, input and help_text
    assert label.tag == 'label'
    assert 'mr-2' == label.attrib['class']

    assert input_.tag == 'input'

    assert help_text.tag == 'span'
    assert 'ml-2' in help_text.attrib['class'].split(' ')


@with_fixtures(WebFixture, FormLayoutFixture)
def test_specifying_help_text(web_fixture, form_layout_fixture):
    """You can optionally specify help_text when adding an input."""
    fixture = form_layout_fixture

    class FormWithInputAndHelp(Form):
        def __init__(self, view):
            super().__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute), help_text='some help')

    browser = Browser(web_fixture.new_wsgi_app(child_factory=FormWithInputAndHelp.factory()))
    browser.open('/')

    [label, input_widget, help_text] = fixture.get_form_group_children(browser)

    # form-group has help-text
    assert help_text.tag == 'p'
    assert 'text-muted' in help_text.attrib['class']
    assert help_text.text == 'some help'


@with_fixtures(WebFixture, FormLayoutFixture)
def test_omitting_label(web_fixture, form_layout_fixture):
    """The label will be rendered hidden (but available to screen readers) if this is explicity requested."""
    fixture = form_layout_fixture

    class FormWithInputNoLabel(Form):
        def __init__(self, view):
            super().__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute), hide_label=True)


    browser = Browser(web_fixture.new_wsgi_app(child_factory=FormWithInputNoLabel.factory()))
    browser.open('/')

    [label, help_text] = fixture.get_form_group_children(browser)
    assert label.tag == 'label'
    assert label.attrib['class'] == 'sr-only'


@with_fixtures(WebFixture, FormLayoutFixture)
def test_adding_checkboxes(web_fixture, form_layout_fixture):
    """CheckboxInputs are added non-inlined, and by default without labels."""

    class DomainObjectWithBoolean:
        fields = ExposedNames()
        fields.an_attribute = lambda i: BooleanField(label='Some input', required=True)

    fixture = form_layout_fixture

    fixture.domain_object = DomainObjectWithBoolean()

    class FormWithInputWithCheckbox(Form):
        def __init__(self, view):
            super().__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(CheckboxInput(self, fixture.domain_object.fields.an_attribute))

    browser = Browser(web_fixture.new_wsgi_app(child_factory=FormWithInputWithCheckbox.factory()))
    browser.open('/')

    assert not any(child.tag == 'label' for child in fixture.get_form_group_children(browser))
    [div] = fixture.get_form_group_children(browser)
    [checkbox] = div.getchildren()
    checkbox_classes = checkbox.attrib['class'].split(' ')
    assert 'custom-control' in checkbox_classes
    assert 'custom-checkbox' in checkbox_classes


class ValidationScenarios(FormLayoutFixture):
    def new_ModelObject(self):
        class ModelObject(Base):
            __tablename__ = 'model_object'
            id = Column(Integer, primary_key=True)
            an_attribute = Column(String)
            another_attribute = Column(String)
            
            fields = ExposedNames()
            fields.an_attribute = lambda i: Field(label='Some input', required=True)
            fields.another_attribute = lambda i: Field(label='Another input', required=True)
            events = ExposedNames()
            events.submit = lambda i: Event(label='Submit')
        return ModelObject

    def new_Form(self):
        fixture = self
        class FormWithInput(Form):
            def __init__(self, view):
                super().__init__(view, 'aform')
                self.set_attribute('novalidate', 'novalidate')
                self.use_layout(FormLayout())
                self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute))
                self.layout.add_input(TextInput(self, fixture.domain_object.fields.another_attribute))
                self.define_event_handler(fixture.domain_object.events.submit)
                self.add_child(Button(self, fixture.domain_object.events.submit))
        return FormWithInput

    @scenario
    def with_javascript(self):
        self.web_fixture.reahl_server.set_app(self.web_fixture.new_wsgi_app(child_factory=self.Form.factory(), enable_js=True))
        self.browser = self.web_fixture.driver_browser

    @scenario
    def without_javascript(self):
        self.browser = Browser(self.web_fixture.new_wsgi_app(child_factory=self.Form.factory()))


@with_fixtures(SqlAlchemyFixture, ValidationScenarios)
def test_input_validation_cues(sql_alchemy_fixture, validation_scenarios):
    """Visible cues are inserted to indicate the current validation state
       and possible validation error messages to a user. """
    fixture = validation_scenarios

    browser = fixture.browser

    with sql_alchemy_fixture.persistent_test_classes(fixture.ModelObject):
        fixture.domain_object = fixture.ModelObject()
        Session.add(fixture.domain_object)
        browser.open('/')

        assert not fixture.get_form_group_highlight_marks(browser, index=0)
        assert not fixture.get_form_group_errors(browser, index=0)

        browser.type(XPath.input_labelled('Some input'), '')
        browser.click(XPath.button_labelled('Submit'))

        assert ['is-invalid'] == fixture.get_form_group_highlight_marks(browser, index=0)
        [error] = fixture.get_form_group_errors(browser, index=0)
        assert error.text == 'Some input is required'

        browser.type(XPath.input_labelled('Some input'), 'valid value')
        browser.click(XPath.button_labelled('Submit'))

        assert ['is-valid'] == fixture.get_form_group_highlight_marks(browser, index=0)
        assert not fixture.get_form_group_errors(browser, index=0)

        browser.type(XPath.input_labelled('Another input'), 'valid value')
        browser.click(XPath.button_labelled('Submit'))

        assert not fixture.get_form_group_highlight_marks(browser, index=0)
        assert not fixture.get_form_group_errors(browser, index=0)


@with_fixtures(WebFixture, SqlAlchemyFixture, ValidationScenarios.with_javascript)
def test_input_validation_cues_javascript_interaction(web_fixture, sql_alchemy_fixture, javascript_validation_scenario):
    """The visual cues rendered server-side can subsequently be manipulated via javascript."""
    fixture = javascript_validation_scenario

    web_fixture.reahl_server.set_app(web_fixture.new_wsgi_app(child_factory=fixture.Form.factory(), enable_js=False))

    browser = fixture.browser

    with sql_alchemy_fixture.persistent_test_classes(fixture.ModelObject):
        fixture.domain_object = fixture.ModelObject()
        Session.add(fixture.domain_object)
        browser.open('/')
        browser.type(XPath.input_labelled('Some input'), '')
        browser.click(XPath.button_labelled('Submit'))

        assert ['is-invalid'] == fixture.get_form_group_highlight_marks(browser, index=0)
        [error] = fixture.get_form_group_errors(browser, index=0)
        assert error.text == 'Some input is required'

        web_fixture.reahl_server.set_app(web_fixture.new_wsgi_app(child_factory=fixture.Form.factory(), enable_js=True))
        browser.open('/')

        browser.click(XPath.button_labelled('Submit'))

        assert ['is-invalid'] == fixture.get_form_group_highlight_marks(browser, index=0)
        [error] = fixture.get_form_group_errors(browser, index=0)
        assert error.text == 'Some input is required'

        browser.type(XPath.input_labelled('Some input'), 'valid value', trigger_blur=False, wait_for_ajax=False)
        browser.press_tab()

        def form_group_is_marked_success(index):
            return ['is-valid'] == fixture.get_form_group_highlight_marks(browser, index=index)
        assert web_fixture.driver_browser.wait_for(form_group_is_marked_success, 0)
        assert not fixture.get_form_group_errors(browser, index=0)


class CheckboxFixture(Fixture):
    def new_field(self):
        return BooleanField(label='Subscribe to newsletter?')

    def new_domain_object(self):
        fixture = self
        class ModelObject:
            fields = ExposedNames()
            fields.an_attribute = lambda i: fixture.field
            events = ExposedNames()
            events.submit = lambda i: Event(label='Submit')
        return ModelObject()

    def new_Form(self):
        fixture = self
        class FormWithInput(Form):
            def __init__(self, view):
                super().__init__(view, 'aform')
                self.use_layout(FormLayout())
                self.layout.add_input(CheckboxInput(self, fixture.domain_object.fields.an_attribute))
                self.define_event_handler(fixture.domain_object.events.submit)
                self.add_child(Button(self, fixture.domain_object.events.submit))
        return FormWithInput


@with_fixtures(WebFixture, CheckboxFixture)
def test_checkbox_basics_with_boolean_field(web_fixture, checkbox_fixture):
    """CheckboxInput can be used to toggle a single yes/no answer, in which case it renders a single checkbox."""

    web_fixture.reahl_server.set_app(web_fixture.new_wsgi_app(child_factory=checkbox_fixture.Form.factory()))
    browser = web_fixture.driver_browser
    browser.open('/')

    checkbox = XPath.input_labelled('Subscribe to newsletter?')
    assert not browser.is_selected(checkbox)
    assert browser.is_element_present(XPath.label().with_text('Subscribe to newsletter?'))
    assert browser.is_element_present('//div[@class="reahl-checkbox-input reahl-primitiveinput"]/div/input/following-sibling::label')
    assert browser.get_attribute('//label', 'class') == 'custom-control-label'
    checkbox_classes = browser.get_attribute('//div/input[@type="checkbox"]/..', 'class').split(' ')
    assert 'custom-control' in checkbox_classes
    assert 'custom-checkbox' in checkbox_classes
    assert browser.get_attribute('//div/input[@type="checkbox"]', 'class') == 'custom-control-input'

    browser.set_selected(checkbox)
    browser.click(XPath.button_labelled('Submit'))

    assert browser.is_selected(checkbox)


@with_fixtures(WebFixture, CheckboxFixture)
def test_click_checkbox_label_with_boolean_field(web_fixture, checkbox_fixture):
    """Clickin on the label of a single checkbox, toggles the checkbox itself."""

    web_fixture.reahl_server.set_app(web_fixture.new_wsgi_app(child_factory=checkbox_fixture.Form.factory()))
    browser = web_fixture.driver_browser
    browser.open('/')

    checkbox = XPath.input_labelled('Subscribe to newsletter?')
    assert not browser.is_selected(checkbox)
    browser.click(XPath.label().with_text('Subscribe to newsletter?'))
    assert browser.is_selected(checkbox)


@with_fixtures(WebFixture, CheckboxFixture)
def test_checkbox_basics_with_multichoice_field(web_fixture, checkbox_fixture):
    """CheckboxInput can also be used to choose many things from a list, in which case it renders many checkboxes."""

    choices = [Choice(1, IntegerField(label='One')),
               Choice(2, IntegerField(label='Two', writable=Action(lambda:False))),
               Choice(3, IntegerField(label='Three')),
               Choice(4, IntegerField(label='Four')),
               ]
    checkbox_fixture.field = MultiChoiceField(choices, label='Make your choice', default=[1])

    web_fixture.reahl_server.set_app(web_fixture.new_wsgi_app(child_factory=checkbox_fixture.Form.factory()))
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.is_element_present(XPath.label().with_text('Make your choice'))

    assert browser.get_xpath_count('//div[@class="reahl-checkbox-input reahl-primitiveinput"]/div/input[@class="custom-control-input"]/following-sibling::label[@class="custom-control-label"]') == 4

    checkbox_one = XPath.input_labelled('One')
    checkbox_two = XPath.input_labelled('Two')
    checkbox_three = XPath.input_labelled('Three')
    checkbox_four = XPath.input_labelled('Four')

    assert browser.is_selected(checkbox_one)
    assert not browser.is_selected(checkbox_two)
    assert not browser.is_element_enabled(checkbox_two)
    # assert browser.is_visible(checkbox_two) #cannot do this as the way bootsrap renders, the actual html input has opacity=0
    assert not browser.is_selected(checkbox_three)
    assert not browser.is_selected(checkbox_four)
    browser.set_deselected(checkbox_one)
    browser.set_selected(checkbox_three)
    browser.set_selected(checkbox_four)
    browser.click(XPath.button_labelled('Submit'))
    assert not browser.is_selected(checkbox_one)
    assert browser.is_selected(checkbox_three)
    assert browser.is_selected(checkbox_four)


@uses(web_fixture=WebFixture)
class ChoicesFixture(Fixture):

    def new_form(self):
        return Form(self.web_fixture.view, 'test')

    def new_boolean_field(self):
        field = BooleanField()
        field.bind('field', self)
        return field


@with_fixtures(WebFixture, ChoicesFixture)
def test_choices_layout_applied_to_checkbox(web_fixture, choices_fixture):
    """A ChoicesLayout lays out PrimitiveCheckboxInputs inside a Label containing the Field label, such that they will be stacked."""
    fixture = choices_fixture

    stacked_container = Div(web_fixture.view).use_layout(ChoicesLayout())
    stacked_container.layout.add_choice(PrimitiveCheckboxInput(fixture.form, fixture.boolean_field))

    stacked_container_classes = stacked_container.children[0].get_attribute('class').split(' ')
    assert 'custom-control' in stacked_container_classes
    assert 'custom-checkbox' in stacked_container_classes

    [checkbox_input, label] = stacked_container.children[0].children
    [description_widget] = label.children
    assert label.tag_name == 'label'

    assert checkbox_input.html_representation.input_type == 'checkbox'
    assert description_widget.value == 'field'


@with_fixtures(WebFixture, ChoicesFixture)
def test_checkbox_with_inline_layout(web_fixture, choices_fixture):
    """PrimitiveCheckboxInputs can be rendered inlined with each other by using the ChoicesLayout with the inline=True setting."""
    fixture = choices_fixture

    inlined_container = Div(web_fixture.view).use_layout(ChoicesLayout(inline=True))
    inlined_container.layout.add_choice(PrimitiveCheckboxInput(fixture.form, fixture.boolean_field))

    assert 'custom-control-inline' in inlined_container.children[0].get_attribute('class').split(' ')


@uses(web_fixture=WebFixture)
class DisabledScenarios(Fixture):

    @scenario
    def disabled_input(self):
        self.field = BooleanField(writable=lambda field: False)
        self.expects_disabled_class = True

    @scenario
    def enabled_input(self):
        self.field = BooleanField(writable=lambda field: True)
        self.expects_disabled_class = False


@with_fixtures(WebFixture, DisabledScenarios)
def test_choice_disabled_state(web_fixture, disabled_scenarios):
    """Visible cues are inserted to indicate that inputs are disabled. """
    fixture = disabled_scenarios

    form = Form(web_fixture.view, 'test')
    field = fixture.field
    field.bind('field', fixture)

    container = Div(web_fixture.view).use_layout(ChoicesLayout())
    container.layout.add_choice(PrimitiveCheckboxInput(form, field))

    [checkbox_container] = container.children
    [checkbox_input, label] = checkbox_container.children
    checkbox_container_classes = checkbox_container.get_attribute('class').split(' ')
    if fixture.expects_disabled_class:
        assert 'disabled' in checkbox_container_classes
        assert checkbox_input.html_representation.get_attribute('disabled') == 'disabled'
    else:
        assert 'disabled' not in checkbox_container_classes
        with expected(KeyError):
            checkbox_input.html_representation.get_attribute('disabled')


class RadioButtonFixture(ChoicesFixture):
    def new_field(self):
        choices = [Choice(1, Field(label='One')),
                   Choice(2, Field(label='Two'))]
        field = ChoiceField(choices)
        field.bind('field', self)
        return field


@with_fixtures(RadioButtonFixture)
def test_radio_button_basics(radio_button_fixture):
    """A RadioButtonSelectInput consists of a labelled radio button for each choice, rendered stacked on one another."""
    fixture = radio_button_fixture

    stacked_radio = RadioButtonSelectInput(fixture.form, fixture.field)
    [container] = stacked_radio.children
    [choice1_container, choice2_container] = container.children

    def check_choice_container_details(choice_container, expected_choice_text, expected_button_value):
        choice_container_classes = choice_container.get_attribute('class').split(' ')
        assert 'custom-control' in choice_container_classes
        assert 'custom-radio' in choice_container_classes
        [primitive_radio_button, label] = choice_container.children
        assert label.tag_name == 'label'
        [choice_text_node] = label.children
        assert primitive_radio_button.value == expected_button_value
        assert choice_text_node.value == expected_choice_text

    check_choice_container_details(choice1_container, 'One', '1')
    check_choice_container_details(choice2_container, 'Two', '2')


@with_fixtures(RadioButtonFixture)
def test_radio_button_layout(radio_button_fixture):
    """To make a RadioButtonSelectInput inline, supply a suitable ChoicesLayout"""
    fixture = radio_button_fixture

    radio_input = RadioButtonSelectInput(fixture.form, fixture.field, contents_layout=ChoicesLayout(inline=True))
    assert radio_input.contents_layout.inline

    choice_container = radio_input.children[0].children[0]
    assert 'custom-control-inline' in choice_container.get_attribute('class').split(' ')


@with_fixtures(RadioButtonFixture)
def test_radio_button_label_as_legend(radio_button_fixture):
    """A FormLayout renders a RadioButtonSelectInput in a FieldSet with its label in the Legend."""
    fixture = radio_button_fixture

    form = fixture.form
    form.use_layout(FormLayout())
    inlined_radio = RadioButtonSelectInput(form, fixture.field)
    fixture.form.layout.add_input(inlined_radio)

    field_set = form.children[-1]
    assert isinstance(field_set, FieldSet)
    assert 'form-group' in field_set.get_attribute('class').split(' ')

    [label_widget, radio_input_in_form] = field_set.children
    assert label_widget.tag_name == 'legend'
    assert 'col-form-label' in label_widget.get_attribute('class')
    assert radio_input_in_form is inlined_radio


@with_fixtures(WebFixture)
def test_button_layouts(web_fixture):
    """A ButtonLayout can be be used on a Button to customise various visual effects."""

    event = Event(label='click me')
    event.bind('event', web_fixture)
    form = Form(web_fixture.view, 'test')
    form.define_event_handler(event)

    # Case: the defaults
    button = Button(form, event)

    tester = WidgetTester(button)
    [button] = tester.xpath(XPath.button_labelled('click me'))
    assert button.attrib['class'] == 'btn btn-secondary reahl-primitiveinput'

    # Case: possible effects
    form = Form(web_fixture.view, 'test')
    form.define_event_handler(event)
    button = Button(form, event, style='secondary', outline=True, size='sm', active=True, wide=True, text_wrap=False)

    tester = WidgetTester(button)
    [button] = tester.xpath(XPath.button_labelled('click me'))
    assert button.attrib['class'] == 'active btn btn-block btn-outline-secondary btn-sm reahl-primitiveinput text-nowrap'


@with_fixtures(WebFixture)
def test_button_layouts_on_anchors(web_fixture):
    """A ButtonLayout can also be used to make an A (anchor) look like a button."""

    anchor = A(web_fixture.view, href=Url('/an/href'), description='link text').use_layout(ButtonLayout())
    tester = WidgetTester(anchor)
    [rendered_anchor] = tester.xpath(XPath.link().with_text('link text'))
    assert rendered_anchor.attrib['class'] == 'btn btn-secondary'
    assert 'aria-disabled' not in rendered_anchor.attrib
    assert 'tabindex' not in rendered_anchor.attrib

    anchor = A(web_fixture.view, href=Url('/an/href'), description='link text', write_check=lambda: False).use_layout(ButtonLayout())
    tester = WidgetTester(anchor)
    [rendered_anchor] = tester.xpath(XPath.link().with_text('link text'))
    assert rendered_anchor.attrib['class'] == 'btn btn-secondary disabled'
    assert rendered_anchor.attrib['aria-disabled'] == 'true'
    assert rendered_anchor.attrib['tabindex'] == '-1'


@with_fixtures(WebFixture)
def test_button_layouts_on_disabled_anchors(web_fixture):
    """Disabled A's are marked with a class so Bootstrap can style them appropriately."""
    def can_write():
        return False

    anchor = A(web_fixture.view, href=Url('/an/href'), description='link text', write_check=can_write)
    anchor.use_layout(ButtonLayout())

    tester = WidgetTester(anchor)
    [rendered_anchor] = tester.xpath(XPath.link().with_text('link text'))
    assert rendered_anchor.attrib['class'] == 'btn btn-secondary disabled'



@with_fixtures(WebFixture)
def test_alert_for_domain_exception(web_fixture):
    """FormLayout can be used to add an Alert with error messages to a form. This includes a 'Reset input'
       button which clears the form input.
    """

    class ModelObject:
        fields = ExposedNames()
        fields.some_field = lambda i: Field(label='Some field', default='not changed')

        events = ExposedNames()
        events.submit_break = lambda i: Event(label='Submit', action=Action(i.always_break))

        def always_break(self):
            raise ValidationException(message='designed to break')

    class MyForm(Form):
        def __init__(self, view):
            super().__init__(view, 'myform')
            self.use_layout(FormLayout())
            model_object = ModelObject()

            if self.exception:
                self.layout.add_alert_for_domain_exception(self.exception)

            self.layout.add_input(TextInput(self, model_object.fields.some_field))

            self.define_event_handler(model_object.events.submit_break)
            self.add_child(Button(self, model_object.events.submit_break))


    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    browser.open('/')

    browser.type(XPath.input_labelled('Some field'), 'some input given')
    browser.click(XPath.button_labelled('Submit'))

    alert = XPath.div().including_class('alert')
    
    assert browser.is_element_present(alert)
    assert browser.get_text(alert) == 'designed to break'

    assert browser.get_value(XPath.input_labelled('Some field')) == 'some input given'
    browser.click(XPath.button_labelled('Reset input'))

    assert not browser.is_element_present(alert)
    assert browser.get_value(XPath.input_labelled('Some field')) == 'not changed'

