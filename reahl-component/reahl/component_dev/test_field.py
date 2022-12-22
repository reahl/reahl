# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


import datetime
import functools

from reahl.tofu import Fixture, scenario, expected, NoException, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import EmptyStub

from reahl.component.context import ExecutionContext
from reahl.component.exceptions import ProgrammerError, IsInstance, IsCallable, IncorrectArgumentError
from reahl.component.modelinterface import Field, FieldIndex, ExposedNames, exposed, Event, \
    EmailField, PasswordField, BooleanField, IntegerField, \
    DateField, DateConstraint, \
    ValidationConstraint, RequiredConstraint, MinLengthConstraint, \
    MaxLengthConstraint, PatternConstraint, AllowedValuesConstraint, \
    EqualToConstraint, IntegerConstraint, \
    MaxValueConstraint, MinValueConstraint, Action, secured, \
    AccessRightsConstraint, Choice, ChoiceGroup, ChoiceField, MultiChoiceConstraint, \
    MultiChoiceField, \
    FileField, SingleFileConstraint, UploadedFile, FileSizeConstraint, \
    MimeTypeConstraint, MaxFilesConstraint, SmallerThanConstraint, GreaterThanConstraint

from reahl.dev.fixtures import ReahlSystemFixture
from reahl.component_dev.test_i18n import LocaleContextStub

@uses(reahl_system_fixture = ReahlSystemFixture) # For a context
class FieldFixture(Fixture):
    def new_model_object(self):
        obj = EmptyStub()
        obj.an_attribute = 'field value'
        return obj

    def new_field(self, cls=Field, name='an_attribute', label='the label', default=None, readable=None, writable=None):
        field = cls(label=label, default=default, readable=readable, writable=writable)
        field.bind(name, self.model_object)
        return field


@with_fixtures(FieldFixture)
def test_marshalling(fixture):
    """A Field marshalls a string representation of some input to a python object which is then set as
       an attribute on the model object to which the Field is bound to. (A Field also unmarshalls such an attribute)."""


    # How the marshalling is programmed
    class MyField(Field):
        def parse_input(self, unparsed_input):
            if unparsed_input == 'one': return 1
            return 0

        def as_input(self):
            if self.get_model_value() == 1: return 'one'
            return 'zero'

    field = fixture.new_field(cls=MyField)

    # From string to python object
    field.from_input('one')
    assert fixture.model_object.an_attribute == 1

    # From python object back to string
    fixture.model_object.an_attribute = 0
    assert field.as_input() == 'zero'


@with_fixtures(FieldFixture)
def test_validation(fixture):
    """Field input is validated by means of Constraints added to the field. Such validation
       happens in two places: validation of the string input, and validation based on the
       parsed python object."""


    # For testing, we just use a simple one-way marshalling field from string to int
    class MyField(Field):
        def parse_input(self, unparsed_input):
            return int(unparsed_input)

    field = fixture.new_field(cls=MyField)

    # How a validation_constraint is coded that checks the raw string input
    class StringLevelConstraint(ValidationConstraint):
        name = 'stringlevel'
        def validate_input(self, unparsed_input):
            if unparsed_input not in ('1', '2'):
                raise self

    # How a validation_constraint is coded that checks the final python object
    class PythonLevelConstraint(ValidationConstraint):
        name = 'pythonlevel'
        def validate_parsed_value(self, parsed_value):
            if parsed_value > 1:
                raise self

    # How constraints are added to the field
    field.add_validation_constraint(StringLevelConstraint(''))
    field.add_validation_constraint(PythonLevelConstraint(''))

    # Input passing both constraints work as expected
    with expected(NoException):
        field.from_input('1')
        assert fixture.model_object.an_attribute == 1

        # Input failing either validation_constraint result in the appropriate validation_constraint being raised
    with expected(StringLevelConstraint):
        field.from_input('unparsable string')
    with expected(PythonLevelConstraint):
        field.from_input('2')

    # If multiple constraints fail, the first one (in order added to the field) is the one reported
    field.add_validation_constraint(AllowedValuesConstraint([]))
    with expected(StringLevelConstraint):
        field.from_input('unparsable string')


@with_fixtures(FieldFixture)
def test_field_metadata(fixture):
    """Fields provide metadata about their contents"""

    field = Field(default=2, required=False, label='A field')
    field.bind('fieldname', fixture.model_object)

    assert field.label == 'A field'
    assert not field.required
    assert field.variable_name == 'fieldname'
    assert field.get_model_value() == 2


@with_fixtures(FieldFixture)
def test_constraint_message(fixture):
    """Each validation_constraint has a customisable error message which can make use of the label supplied by
       the Field it is added to, or any other attribute of the ValidationConstraint itself."""


    class MyConstraint(ValidationConstraint):
        name = 'myconstraint'
        one_attr = 'boerpampoene'
        another_attr = 20091124

    # The message template is given when constructed
    validation_constraint = MyConstraint('Bob âte $missing_attr $one_attr on $another_attr $label')
    fixture.field.add_validation_constraint(validation_constraint)

    # The validation_constraint gets its label from its field
    assert validation_constraint.label == fixture.field.label

    # How the template is filled with attributes (and missing ones)
    expected = 'Bob âte $missing_attr boerpampoene on 20091124 the label'
    assert validation_constraint.message == expected


@with_fixtures(FieldFixture)
def test_meaning_of_required(fixture):
    """Making a Field required means adding a RequiredConstraint to it"""
    # Case: construction with default value for required

    field = Field()
    assert not field.required

    # Case: construction with required=True
    field = Field(required=True)
    assert field.required
    assert field.get_validation_constraint_named(RequiredConstraint.name)


@with_fixtures(FieldFixture)
def test_getting_modified_copy(fixture):
    """It is possible to get a modified copy of an existing field if you want to link it with
       different constraints on a different input"""

    other_constraint = ValidationConstraint('Other error')
    other_constraint.name = 'other'
    field = Field()
    field.add_validation_constraint(other_constraint)
    model_object = EmptyStub()
    field.bind('field_name', model_object)

    # Getting a copy
    new_field = field.copy()
    assert new_field is not field
    assert new_field.name == field.name
    assert new_field.storage_object == field.storage_object
    assert new_field.default == field.default
    assert new_field.label == field.label
    copied_other_constraint = new_field.get_validation_constraint_named(other_constraint.name)
    assert copied_other_constraint.field is new_field
    new_validation_constraints = [i.__class__ for i in new_field.validation_constraints]
    old_validation_constraints = [i.__class__ for i in field.validation_constraints]
    assert new_validation_constraints == old_validation_constraints
    assert new_field.validation_constraints != field.validation_constraints
    assert new_field.validation_constraints is not field.validation_constraints

    assert new_field.access_rights is not field.access_rights
    assert new_field.access_rights.readable is field.access_rights.readable
    assert new_field.access_rights.writable is field.access_rights.writable

    # Getting a required copy
    assert not field.required
    required_field = field.as_required(required_message='new required message')
    assert required_field.required
    required = required_field.get_validation_constraint_named(RequiredConstraint.name)
    assert required.error_message.template == 'new required message'

    # Getting copy that's not required
    field.make_required('')
    assert field.required
    optional_field = field.as_optional()
    assert not optional_field.required

    # Getting copy with a ValidationConstraint of certain type removed
    assert field.required 
    more_lax_field = field.without_validation_constraint(RequiredConstraint)
    assert not more_lax_field.required 

    # Getting copy with a new ValidationConstraint added
    field.make_optional()
    assert not field.required 
    more_strict_field = field.with_validation_constraint(RequiredConstraint())
    assert more_strict_field.required 

    # Getting copy with a new label
    assert field.label != 'new label'
    differently_labelled_field = field.with_label('new label')
    assert differently_labelled_field.label == 'new label'
    

def test_global_state():
    """A Field can store its data in a global dict so that it can be recreated later with the same underlying data."""
    with ExecutionContext():
        state_dict = {}
        a = Field()
        a.bind('x', a)

        a.input_status = EmptyStub()
        a.validation_error = EmptyStub()
        a.user_input = EmptyStub()
        a.parsed_input = EmptyStub()

        a.activate_global_field_data_store(state_dict)

        a.initial_value = EmptyStub()

        b = Field()
        b.bind('x', b)

        assert a.initial_value is not b.initial_value
        assert a.input_status  is not b.input_status
        assert a.validation_error is not b.validation_error
        assert a.user_input  is not b.user_input
        assert a.parsed_input is not b.parsed_input

        b.activate_global_field_data_store(state_dict)

        assert a.initial_value is b.initial_value
        assert a.input_status  is b.input_status
        assert a.validation_error is b.validation_error
        assert a.user_input  is b.user_input
        assert a.parsed_input is b.parsed_input


def test_when_initial_value_is_read():
    """The initial_value of a Field is set upon first activate_global_field_data_store"""
    with ExecutionContext():
        state_dict = {}
        a = Field()
        a.bind('x', a)
        a.x = 'initial value for a'

        assert not a.initial_value

        a.activate_global_field_data_store(state_dict)

        assert a.initial_value == a.x

        a.x = 'changed value'
        a.activate_global_field_data_store(state_dict)

        assert a.initial_value != a.x


def test_default_and_required_error():
    """Default and required cannot be both set."""
    with ExecutionContext():
        with expected(ProgrammerError, test='Both required and default are provided.'
                                            ' Default is only used when no value is provided by the user.'
                                            ' Required prevents this from happening.'):
            Field(required=True, default='something')


def test_namespaces():
    with ExecutionContext():
        state_dict = {}
        a = Field()
        a.bind('x', a)

        # Case: namespaces change the name of the Field
        b = a.in_namespace('deeper')

        assert a.name == 'x'
        assert b.name == 'deeper-x'

        # Case: namespaces can be nested
        c = b.in_namespace('even')
        assert c.name == 'even-deeper-x'

        # Case: a Field *in* different namespace, but made from another share the same data
        a.initial_value = EmptyStub()
        a.input_status = EmptyStub()
        a.validation_error = EmptyStub()
        a.user_input = EmptyStub()
        a.parsed_input = EmptyStub()

        assert a.initial_value is b.initial_value is c.initial_value
        assert a.input_status  is b.input_status is c.input_status
        assert a.validation_error is b.validation_error is c.validation_error
        assert a.user_input  is b.user_input is c.user_input
        assert a.parsed_input is b.parsed_input is c.parsed_input


@with_fixtures(FieldFixture)
def test_helpers_for_fields_deprecated(fixture):
    """The @exposed decorator makes it simpler to bind Fields to an object."""

    class ModelObject:
        @exposed
        def fields(self, fields):
            fields.field1 = IntegerField()
            fields.field2 = BooleanField()

    model_object = ModelObject()

    assert model_object.fields is model_object.fields
    assert model_object.fields.field1.bound_to is model_object
    assert model_object.fields.field2.bound_to is model_object

    
@with_fixtures(FieldFixture)
def test_helpers_for_fields(fixture):
    """Use ExposedNames to automatically bind a number of Fields to instances of a given class."""

    class ModelObject:
        fields = ExposedNames()
        fields.field1 = lambda i: IntegerField()
        fields.field2 = lambda i: BooleanField()

    model_object = ModelObject()
    assert model_object.fields is model_object.fields
    assert model_object.fields.field1.bound_to is model_object
    assert model_object.fields.field2.bound_to is model_object


    
@with_fixtures(FieldFixture)
def test_helpers_for_fields_delayed(fixture):
    """Creation of an individual Field is delayed until it is accessed, and you can make use of instance data or internationalised strings when you create it."""

    class ModelObject:
        def __init__(self, name):
            self.name = name

        fields = ExposedNames()
        fields.field1 = lambda i: IntegerField(label=i.name)
        fields.field2 = lambda i: BooleanField(label=i.name)
        
    model_object = ModelObject('john')
    field1 = model_object.fields.field1
    model_object.name = 'name subsequently changed'
    field2 = model_object.fields.field2
    
    assert field1.label == 'john'
    assert field2.label == 'name subsequently changed'

    assert model_object.fields.field1 is field1
    assert model_object.fields.field2 is field2

    

@with_fixtures(FieldFixture)
def test_helpers_for_fields_inheritance(fixture):
    """The Fields on different ExposedNames instances with the name in an inheritance hierarchy are merged 
       to create the resultant FieldIndex on an instance."""

    class ModelObject:
        fields = ExposedNames()
        fields.field1 = lambda i: IntegerField()
        fields.field2 = lambda i: BooleanField()

    class InheritingModelObject(ModelObject):
        fields = ExposedNames()
        fields.field3 = lambda i: IntegerField()

    model_object = ModelObject()

    assert model_object.fields is model_object.fields
    assert model_object.fields.field1.bound_to is model_object
    assert model_object.fields.field2.bound_to is model_object

    inheriting_object = InheritingModelObject()

    assert inheriting_object.fields is not model_object.fields
    assert inheriting_object.fields is inheriting_object.fields
    assert inheriting_object.fields.field1.bound_to is inheriting_object
    assert inheriting_object.fields.field2.bound_to is inheriting_object
    assert inheriting_object.fields.field3.bound_to is inheriting_object
    

@with_fixtures(FieldFixture)
def test_re_binding_behaviour_of_field_index(fixture):
    """FieldIndexes wont bind a field if it already is bound."""

    model_object1 = EmptyStub()
    model_object2 = EmptyStub()
    bound_field = Field()
    bound_field.bind('bound_field', model_object2)

    assert bound_field.is_bound
    assert bound_field.bound_to is model_object2
    index = FieldIndex(model_object1)
    index.new_name_for_bound_field = bound_field
    assert index.new_name_for_bound_field.name is 'bound_field'
    assert bound_field.bound_to is model_object2


@with_fixtures(FieldFixture)
def test_helpers_for_events_deprecated(fixture):
    """The @exposed decorator makes it simpler to collect Events on an object similar to how it is used for Fields."""

    class ModelObject:
        @exposed
        def events(self, fields):
            fields.event1 = Event()
            fields.event2 = Event()

    model_object = ModelObject()

    assert model_object.events is model_object.events
    assert model_object.events.event1.bound_to is model_object.events.event1
    assert model_object.events.event2.bound_to is model_object.events.event2

    assert model_object.events.event1.name == 'event1'


@with_fixtures(FieldFixture)
def test_helpers_for_events2_deprecated(fixture):
    """The @exposed decorator can be used to get FakeEvents at a class level, provided the valid Event names are specified."""

    class ModelObject:
        @exposed('event1')
        def events(self, fields):
            fields.event1 = Event()
            fields.event2 = Event()

    assert ModelObject.events.event1.name == 'event1'

    with expected(AttributeError):
        ModelObject.events.nonevent

        
@with_fixtures(FieldFixture)
def test_helpers_for_events_class_side(fixture):
    """The ExposedNames of a class can be accessed class side to yield objects that implement a partial Field/Event interface (implements .name only)."""

    class ModelObject:
        events = ExposedNames()
        events.event1 = lambda i: Event()
        events.event2 = lambda i: Event()

    assert ModelObject.events.event1.name == 'event1'

    with expected(AttributeError):
        ModelObject.events.nonevent


        

@with_fixtures(FieldFixture)
def test_helpers_for_events3_deprecated(fixture):
    """An Event has to be created for each of the names listed to the @exposed decorator, else an error is raised."""

    class ModelObject:
        @exposed('event1', 'forgotten')
        def events(self, fields):
            fields.event1 = Event()
            fields.event2 = Event()

    with expected(ProgrammerError, test='You promised to instantiate.*'):
        ModelObject().events


@with_fixtures(FieldFixture)
def test_events_deprecated(fixture):
    """An Event defines a signal that can be sent to the system, with the intention to
       possibly trigger the execution of an Action by the system. Metadata, such as what
       a human might label the Event, is also specified."""

    class ModelObject:
        @exposed
        def events(self, events):
            events.an_event = Event(action=Action(self.do_something), label='human readable label')

        def do_something(self):
            self.something_done = True

    model_object = ModelObject()
    event = model_object.events.an_event.with_arguments()
    event.from_input(event.as_input())
    event.fire()

    assert model_object.something_done
    assert model_object.events.an_event.label == 'human readable label'
    
@with_fixtures(FieldFixture)
def test_events(fixture):
    """An Event defines a signal that can be sent to the system, with the intention to
       possibly trigger the execution of an Action by the system. Metadata, such as what
       a human might label the Event, is also specified."""

    class ModelObject:
        events = ExposedNames()
        events.an_event = lambda i: Event(action=Action(i.do_something), label='human readable label')

        def do_something(self):
            self.something_done = True

    model_object = ModelObject()
    event = model_object.events.an_event.with_arguments()
    event.from_input(event.as_input())
    event.fire()

    assert model_object.something_done
    assert model_object.events.an_event.label == 'human readable label'


@with_fixtures(FieldFixture)
def test_arguments_to_actions(fixture):
    """Arguments can be defined on an Event in order to be able to pass them to the linked Action
       as args or kwargs as specified by the Action."""


    expected_arg = 123
    expected_kwarg = 45

    class ModelObject:
        events = ExposedNames()
        events.an_event = lambda i: Event(one_argument=IntegerField(required=True),
                                          another_argument=IntegerField(),
                                          unused_argument=IntegerField(),
                                          action=Action(i.do_something,
                                                        ['one_argument'],
                                                        dict(a_kwarg='another_argument')))

        def do_something(self, an_arg, a_kwarg=None):
            self.passed_an_arg = an_arg
            self.passed_a_kwarg = a_kwarg

    model_object = ModelObject()
    event = model_object.events.an_event.with_arguments(one_argument=123, another_argument=45, unused_argument=678)
    event.from_input(event.as_input())
    event.fire()

    assert model_object.passed_an_arg is expected_arg
    assert model_object.passed_a_kwarg is expected_kwarg


@with_fixtures(FieldFixture)
def test_arguments_to_event(fixture):
    """Only Action objects can be sent as action= when creating an Event. The arguments passed to readable and writable
       should be callable objects with correct signature."""


    # action=
    with expected(IsInstance):
        Event(action=EmptyStub())

    def check_exc(expected_message, ex):
        message = str(ex).split(':')[1][1:]
        assert message.startswith(expected_message)

        # readable/writable are callable
    with expected(IsCallable, test=functools.partial(check_exc, 'readable should be a callable object')):
        Event(readable=EmptyStub())
    with expected(IsCallable, test=functools.partial(check_exc, 'writable should be a callable object')):
        Event(writable=EmptyStub())

    # readable/writable have correct signature
    def do_nothing(a, b, c, d): pass
    with expected(IncorrectArgumentError):
        Event(readable=do_nothing)
    with expected(IncorrectArgumentError):
        Event(writable=do_nothing)


class ActionScenarios(Fixture):
    @scenario
    def action_method(self):
        class ModelObject:
            allow_read_flag = True
            allow_write_flag = True
            def allow_read(self):
                return self.allow_read_flag

            def allow_write(self):
                return self.allow_write_flag

            @secured( read_check=allow_read, write_check=allow_write )
            def do_something(self):
                pass

            events = ExposedNames()
            events.an_event = lambda i: Event(action=Action(i.do_something))
            
        self.model_object = ModelObject()
        self.rights_flags = self.model_object

    @scenario
    def action_function(self):
        self.allow_read_flag = True
        self.allow_write_flag = True

        def allow_read():
            return self.allow_read_flag

        def allow_write():
            return self.allow_write_flag

        @secured( read_check=allow_read, write_check=allow_write )
        def do_something():
            pass

        class ModelObject:
            events = ExposedNames()
            events.an_event = lambda i: Event(action=Action(do_something))
        self.model_object = ModelObject()
        self.rights_flags = self


@with_fixtures(FieldFixture, ActionScenarios)
def test_event_security(field_fixture, action_scenarios):
    """If an Event specifies an Action, the access controls of the Action are
       used for access to the Event as well."""

    fixture = action_scenarios

    event = fixture.model_object.events.an_event.with_arguments()
    event.from_input(event.as_input())

    event.fire()

    assert event.can_read()
    assert event.can_write()

    fixture.rights_flags.allow_read_flag = False
    assert not event.can_read()

    fixture.rights_flags.allow_write_flag = False
    assert not event.can_write()

    with expected(ProgrammerError):
        event.fire()


@with_fixtures(FieldFixture)
def test_event_security2(fixture):
    """If an Event does not specify an Action, then Actions can be passed for its readable and writable."""

    class ModelObject:
        def __init__(self):
            self.allow_read_flag = True
            self.allow_write_flag = True
            
        def allow_read(self):
            return self.allow_read_flag
        
        def allow_write(self):
            return self.allow_write_flag

        events = ExposedNames()
        events.an_event = lambda i: Event(readable=Action(i.allow_read),
                                          writable=Action(i.allow_write))

    model_object = ModelObject()
    event = model_object.events.an_event.with_arguments()

    assert event.can_read()
    assert event.can_write()

    model_object.allow_read_flag = False
    assert not event.can_read()

    model_object.allow_write_flag = False
    assert not event.can_write()


def test_event_security_action_and_rw():
    """Supply either an action or a readable/writable to an Event, but not both."""

    def do_nothing(): pass

    with expected(ProgrammerError):
        Event(action=Action(do_nothing), readable=Action(do_nothing))
    with expected(ProgrammerError):
        Event(action=Action(do_nothing), writable=Action(do_nothing))


@with_fixtures(FieldFixture)
def test_receiving_events(fixture):
    """An Event is said to have occurred if it received a querystring containing its arguments from user input.
       An Event can only be fired if it occurred."""

    class ModelObject:
        events = ExposedNames()
        events.an_event = lambda i: Event(an_argument=IntegerField())

    model_object = ModelObject()
    event = model_object.events.an_event.with_arguments(an_argument=123)

    assert event.default == {'an_argument': 123}
    assert not hasattr(event, 'arguments')
    assert not event.occurred
    with expected(ProgrammerError):
        event.fire()

    event.from_input('?an_argument=123')
    assert event.arguments == {'an_argument': 123}
    assert event.occurred
    with expected(NoException):
        event.fire()


class AllowedScenarios(Fixture):
    @scenario
    def both_disallowed(self):
        self.allow_read = False
        self.allow_write = False
        self.expected_occurred = False
        self.expected_exception = AccessRightsConstraint
    @scenario
    def read_allowed(self):
        self.allow_read = True
        self.allow_write = False
        self.expected_occurred = False
        self.expected_exception = AccessRightsConstraint
    @scenario
    def write_allowed(self):
        self.allow_read = False
        self.allow_write = True
        self.expected_occurred = False
        self.expected_exception = AccessRightsConstraint
    @scenario
    def both_allowed(self):
        self.allow_read = True
        self.allow_write = True
        self.expected_occurred = True
        self.expected_exception = NoException


@with_fixtures(FieldFixture, AllowedScenarios)
def test_security_of_receiving_events(field_fixture, allowed_scenarios):
    """An Event can only occur if BOTH its access restrictions are allowed."""


    fixture = allowed_scenarios

    class ModelObject:
        def allow_read(self):
            return fixture.allow_read
        def allow_write(self):
            return fixture.allow_write
        events = ExposedNames()
        events.an_event = lambda i: Event(readable=Action(i.allow_read), writable=Action(i.allow_write))

    model_object = ModelObject()
    event = model_object.events.an_event

    assert not event.occurred
    with expected(fixture.expected_exception):
        event.from_input('?')
    assert event.occurred is fixture.expected_occurred


@with_fixtures(FieldFixture)
def test_required_constraint(fixture):
    selector = 'find me'
    required_constraint = RequiredConstraint(dependency_expression=selector)

    #selector is returned as parameter
    assert required_constraint.parameters == selector

    #case: no input
    with expected(RequiredConstraint):
        required_constraint.validate_input('')
    with expected(RequiredConstraint):
        required_constraint.validate_input(None)
    #just spaces
    space = ' '
    with expected(RequiredConstraint):
        required_constraint.validate_input(space)
    with expected(RequiredConstraint):
        required_constraint.validate_input(space*56)

    #case: input
    with expected(NoException):
        required_constraint.validate_input(' something valid    ')
    with expected(NoException):
        required_constraint.validate_input('sômething else that_is_valid')
    with expected(NoException):
        required_constraint.validate_input('.')


@with_fixtures(FieldFixture)
def test_min_length_constraint(fixture):

    min_required_length = 5
    min_length_constraint = MinLengthConstraint(min_length=min_required_length)

    #min length is returned as parameter
    assert min_length_constraint.parameters == '%s' % min_required_length

    #case: just enough characters, exact number of
    with expected(NoException):
        min_length_constraint.validate_input('⁵'*min_required_length)

    #case: more than enough
    with expected(NoException):
        min_length_constraint.validate_input('ê'*(min_required_length+1))

    #case: just not enough characters
    with expected(MinLengthConstraint):
        min_length_constraint.validate_input('ś'*(min_required_length-1))

    #case: empty string
    with expected(MinLengthConstraint):
        min_length_constraint.validate_input('')


@with_fixtures(FieldFixture)
def test_max_length_constraint(fixture):

    max_allowed_length = 5
    max_length_constraint = MaxLengthConstraint(max_length=max_allowed_length)

    #max length is returned as parameter
    assert max_length_constraint.parameters == '%s' % max_allowed_length

    #case: just enough characters, exact number of
    with expected(NoException):
        max_length_constraint.validate_input('⁵'*max_allowed_length)

    #case: less than max
    with expected(NoException):
        max_length_constraint.validate_input('⁵'*(max_allowed_length-1))

    #case: nothing
    with expected(NoException):
        max_length_constraint.validate_input('')

    #case: just too much
    with expected(MaxLengthConstraint):
        max_length_constraint.validate_input('ś'*(max_allowed_length+1))


@with_fixtures(FieldFixture)
def test_pattern_constraint(fixture):

    allow_pattern = '(ab)+'
    pattern_constraint = PatternConstraint(pattern=allow_pattern)

    #pattern is returned as parameter
    assert pattern_constraint.parameters == allow_pattern

    #case: valid
    valid_input = 'ababab'
    with expected(NoException):
        pattern_constraint.validate_input(valid_input )

    #case invalid
    with expected(PatternConstraint):
        pattern_constraint.validate_input('aba')

    #case: faulty pattern
    faulty_pattern_constraint = PatternConstraint(pattern='??????')
    with expected(ProgrammerError):
        faulty_pattern_constraint.validate_input(valid_input)


@with_fixtures(FieldFixture)
def test_allowed_values_constraint(fixture):

    allowed_values=['a','b']
    allowed_values_constraint = AllowedValuesConstraint(allowed_values=allowed_values)

    #case: valid input
    valid_input = allowed_values[1]
    with expected(NoException):
        allowed_values_constraint.validate_input(valid_input)

    #case: invalid input
    invalid_input = 'ba'
    assert invalid_input not in allowed_values
    with expected(AllowedValuesConstraint):
        allowed_values_constraint.validate_input(invalid_input)


@with_fixtures(FieldFixture)
def test_equal_to_constraint(fixture):

    other_field = Field(label='other')
    equal_to_constraint = EqualToConstraint(other_field, '$label, $other_label')
    other_field.set_user_input('should be equal to this string', ignore_validation=True)

    #case: valid input
    with expected(NoException):
        equal_to_constraint.validate_parsed_value('should be equal to this string' )

    #case: invalid input
    with expected(EqualToConstraint):
        equal_to_constraint.validate_parsed_value('this is not equal')


@with_fixtures(FieldFixture)
def test_smaller_than_constraint(fixture):

    other_field = IntegerField(label='other')
    smaller_than_constraint = SmallerThanConstraint(other_field, '$label, $other_label')
    other_field.set_user_input('5', ignore_validation=True)

    #case: valid input
    with expected(NoException):
        smaller_than_constraint.validate_parsed_value( 4 )

    #case: invalid input
    with expected(SmallerThanConstraint):
        smaller_than_constraint.validate_parsed_value( 5 )


@with_fixtures(FieldFixture)
def test_greater_than_constraint(fixture):

    other_field = IntegerField(label='other')
    greater_than_constraint = GreaterThanConstraint(other_field, '$label, $other_label')
    other_field.set_user_input('5', ignore_validation=True)

    #case: valid input
    with expected(NoException):
        greater_than_constraint.validate_parsed_value( 6 )

    #case: invalid input
    with expected(GreaterThanConstraint):
        greater_than_constraint.validate_parsed_value( 5 )


@with_fixtures(FieldFixture)
def test_email_validation(fixture):

    field = EmailField()

    # Case: invalid
    invalid_addresses = ['somethingWithoutTheAt', '@somethingThatBeginsWithTheAT',
                         'somethingThatEndsWithTheAt@', '@', None]
    for address in invalid_addresses:
        with expected(PatternConstraint):
            field.set_user_input(address)
        assert field.validation_error is field.get_validation_constraint_named('pattern')

        # Case: valid
    valid_addresses = ['someone@home.co.za', 'something@somewhere.com', 'j@j.ca']
    for address in valid_addresses:
        with expected(NoException):
            field.set_user_input(address, ignore_validation=True)
        assert not field.validation_error


@with_fixtures(FieldFixture)
def test_password_validation(fixture):

    field = PasswordField()

    # Case: invalid
    with expected(MinLengthConstraint):
        field.set_user_input('123')
    assert field.validation_error is field.get_validation_constraint_named('minlength')
    with expected(MaxLengthConstraint):
        field.set_user_input('1'*21)
    assert field.validation_error is field.get_validation_constraint_named('maxlength')

    # Case: valid
    with expected(NoException):
        field.set_user_input('my passwôrd')
    assert not field.validation_error


@with_fixtures(FieldFixture)
def test_password_access(fixture):
    """A PasswordField is world writable, but not readable by anyone."""

    field = PasswordField()
    field.bind('password_field', EmptyStub())
    assert not field.can_read()
    assert field.can_write()


@with_fixtures(FieldFixture)
def test_boolean_validation(fixture):

    obj = EmptyStub()
    field = BooleanField()
    field.bind('boolean_attribute', obj)

    # Case: invalid
    invalid_boolean_name = ['negative', 'affirmative', '+', '-', None]
    for boolean_candidate in invalid_boolean_name:
        with expected(AllowedValuesConstraint):
            field.set_user_input(boolean_candidate)
        assert field.validation_error is field.get_validation_constraint_named('pattern')

        # Case: valid
    field.from_input('on')
    assert obj.boolean_attribute is True
    assert field.as_input() == 'on'
    field.from_input('off')
    assert obj.boolean_attribute is False
    assert field.as_input() == 'off'

    # Case: required means True for BooleanField
    field = BooleanField(required=True)
    field.bind('boolean_attribute', obj)
    with expected(AllowedValuesConstraint):
        field.set_user_input('off')
    assert field.validation_error is field.get_validation_constraint_named('pattern')
    with expected(NoException):
        field.from_input('on')


def test_boolean_i18n():
    with LocaleContextStub(locale='af') as context:

        obj = EmptyStub()
        field = BooleanField()
        field.bind('boolean_attribute', obj)

        # Case: valid
        field.from_input('aan')
        assert obj.boolean_attribute is True
        assert field.as_input() == 'aan'
        field.from_input('af')
        assert obj.boolean_attribute is False
        assert field.as_input() == 'af'


@with_fixtures(FieldFixture)
def test_integer_validation(fixture):

    field = IntegerField()

    # Case invalid
    with expected(IntegerConstraint):
        field.set_user_input('sdfdf')

    # Case valid
    with expected(NoException):
        field.set_user_input('3')

    # Case Max
    field = IntegerField(max_value=4)
    with expected(MaxValueConstraint):
        field.set_user_input('5')

    # Case Min
    field = IntegerField(min_value=4)
    with expected(MinValueConstraint):
        field.set_user_input('3')


@with_fixtures(FieldFixture)
def test_basic_marshalling(fixture):

    field = Field()
    obj = EmptyStub()
    field.bind('value', obj)

    # From input
    field.from_input('abc')
    assert obj.value == 'abc'

    # As input
    obj.value = 'def'
    assert field.as_input() == 'def'

    # As input - corner case
    obj.value = ''
    assert field.as_input() == ''


@with_fixtures(FieldFixture)
def test_integer_marshalling(fixture):

    field = IntegerField()
    obj = EmptyStub()
    field.bind('integer_value', obj)

    # From input
    field.from_input('5')
    assert obj.integer_value is 5

    # As input
    obj.integer_value = 6
    assert field.as_input() == '6'

    # As input - corner case
    obj.integer_value = 0
    assert field.as_input() == '0'


@uses(field_fixture=FieldFixture)
class ChoiceFixture(Fixture):
    def new_field(self, field_class=None):
        field_class = field_class or ChoiceField
        field = field_class(self.choices)
        field.bind('choice_value', self.model_object)
        return field

    def new_model_object(self):
        return EmptyStub()

    @scenario
    def plain_choices(self):
        self.all_choices = [Choice(1, IntegerField(label='One')),
                            Choice('2', Field(label='Two'))]
        self.choices = self.all_choices
        self.groups = []
        self.valid_inputs = ['1', '2']
        self.invalid_input = 'not an valid option'
        self.input_to_value_map = {'1': 1, '2': '2'}
        self.expected_validation_constraint = AllowedValuesConstraint

    @scenario
    def grouped_choices(self):
        self.all_choices = [Choice(1, IntegerField(label='One')),
                            Choice('2', Field(label='Two'))]
        self.groups = [ChoiceGroup('', self.all_choices)]
        self.choices = self.groups
        self.valid_inputs = ['1', '2']
        self.invalid_input = 'not an valid option'
        self.input_to_value_map = {'1': 1, '2': '2'}
        self.expected_validation_constraint = AllowedValuesConstraint

    @scenario
    def multi_choices(self):
        self.all_choices = [Choice(1, IntegerField(label='One')),
                            Choice(2, IntegerField(label='Two')),
                            Choice(3, IntegerField(label='Three'))]
        self.groups = []
        self.choices = self.all_choices
        self.field = self.new_field(MultiChoiceField)

        self.valid_inputs = [('1',), ['1', '2']]
        self.invalid_input = ['not an valid option', '1']
        self.input_to_value_map = {('1',): [1], ('1', '2'): [1, 2]}
        self.expected_validation_constraint = MultiChoiceConstraint

    @scenario
    def multi_choices_required(self):
        self.all_choices = [Choice(1, IntegerField(label='One'))]
        self.groups = []
        self.choices = self.all_choices
        field = self.new_field(MultiChoiceField)
        self.field = field.with_validation_constraint(RequiredConstraint())

        self.valid_inputs = [('1',), ['1']]
        self.invalid_input = []
        self.input_to_value_map = {('1',): [1]}
        self.expected_validation_constraint = RequiredConstraint


@with_fixtures(ChoiceFixture)
def test_choice_querying(choice_fixture):
    """A ChoiceField maintains a list of the Choices and Groups it was constructed with."""

    fixture = choice_fixture

    field = fixture.field

    assert field.groups == fixture.groups
    assert field.flattened_choices == fixture.all_choices


@with_fixtures(ChoiceFixture)
def test_choice_validation(choice_fixture):
    """Input for a ChoiceField is valid only if it matches one of its Choices."""

    fixture = choice_fixture
    field = fixture.field

    # Case invalid
    with expected(fixture.expected_validation_constraint):
        field.set_user_input(fixture.invalid_input)

    # Case valid
    for i in fixture.valid_inputs:
        with expected(NoException):
            field.set_user_input(i)


@with_fixtures(ChoiceFixture)
def test_choice_field_marshalling(choice_fixture):
    """Input for a ChoiceField is marshalled differently, depending on the Field specified for the Choice matching the input."""

    fixture = choice_fixture
    field = fixture.field
    obj = fixture.model_object

    # From input
    for valid_input, value in fixture.input_to_value_map.items():
        field.from_input(valid_input)
        assert obj.choice_value == value

        # As input
    for expected_input, value in fixture.input_to_value_map.items():
        obj.choice_value = value
        if isinstance(expected_input, tuple):
            expected_input = list(expected_input)
        assert field.as_input() == expected_input


@with_fixtures(ReahlSystemFixture) # For a context
def test_unique_choices(fixture):
    """All choices must have unique values."""
    duplicate_choices = [Choice(1, IntegerField(label='One')),
                         Choice(1, IntegerField(label='Two')),
                         Choice(3, IntegerField(label='Three'))]
    with expected(ProgrammerError, test='Duplicate choices are not allowed'):
        ChoiceField(duplicate_choices).flattened_choices

@uses(system_fixture=ReahlSystemFixture)
class ChoiceScenarios(Fixture):
    @scenario
    def single_choice(self):
        self.field_class = ChoiceField
    
    @scenario
    def multi_choice(self):
        self.field_class = MultiChoiceField


@with_fixtures(ChoiceScenarios)
def test_choice_querying(fixture):
    """The Choices of a ChoiceField can be delayed to after its construction."""

    model_object = EmptyStub()

    current_choices = [Choice(1, IntegerField(label='One')),
                       Choice('2', Field(label='Two'))]
    def choices_getter():
        return current_choices
    field = fixture.field_class(choices_getter)
    field.bind('choice_value', model_object)

#   assert [i.value for i in field.flattened_choices] == [1, '2']  # In the fake world of tests, grouped_choices is memoized, so cached...we can only call it once.

    current_choices = [Choice(4, IntegerField(label='Four'))]

    assert [i.value for i in field.flattened_choices] == [4]

    

@with_fixtures(FieldFixture)
def test_file_marshalling(fixture):
    """A FileField receives as input a list of UploadedFile objects.  Its marshalling job consists
       of merely changing such a list into a single value, or returning it as is depending on
       the setting of its allow_multiple flag.
    """


    field = FileField()
    obj = fixture.model_object
    field.bind('file_value', obj)

    files = [EmptyStub(), EmptyStub()]

    # Single file only
    field.from_input(files[:1])
    assert obj.file_value == files[0]

    obj.file_value = files[0]
    assert field.as_input() == ''

    # Multiple files
    field = FileField(allow_multiple=True)
    field.bind('file_value', obj)

    field.from_input(files)
    assert obj.file_value == files

    obj.file_value = files
    assert field.as_input() == ''


@with_fixtures(FieldFixture)
def test_file_validation(fixture):
    """A FileField needs to check that the right number of files were submitted, depending on the
       setting of allow_multiple and/or required.
    """

    field = FileField()
    obj = fixture.model_object
    field.bind('file_value', obj)

    files = [EmptyStub(), EmptyStub()]

    # Single file only
    with expected(SingleFileConstraint):
        field.set_user_input(files)

    with expected(NoException):
        field.set_user_input(files[:1])

    # Single file that is required
    field = FileField(required=True)
    field.bind('file_value', obj)

    with expected(NoException):
        field.set_user_input(files[:1])

    with expected(RequiredConstraint):
        field.set_user_input([])

    # Multiple files
    field = FileField(allow_multiple=True)
    field.bind('file_value', obj)

    with expected(NoException):
        field.set_user_input(files)


@with_fixtures(FieldFixture)
def test_file_validation_size(fixture):
    """A FileField can also limit the size if files uploaded.
    """


    field = FileField(allow_multiple=True, max_size_bytes=100)
    obj = fixture.model_object
    field.bind('file_value', obj)

    files = [UploadedFile('file1', b'.'*100, ''), UploadedFile('file2', b'.'*50, '')]
    with expected(NoException):
        field.set_user_input(files)

    files = [UploadedFile('file1', b'.'*100, ''), UploadedFile('file2', b'.'*200, '')]
    with expected(FileSizeConstraint):
        field.set_user_input(files)


@with_fixtures(FieldFixture)
def test_file_validation_mime_type(fixture):
    """A FileField can also limit the mimetype of files allowed to be uploaded.
    """


    field = FileField(allow_multiple=True, accept=['text/*'])
    obj = fixture.model_object
    field.bind('file_value', obj)

    files = [UploadedFile('file1', b'stuff 1', 'text/html'), UploadedFile('file2', b'stuff 2', 'text/xml')]
    with expected(NoException):
        field.set_user_input(files)

    files = [UploadedFile('file1', b'stuff 3', 'text/html'), UploadedFile('file2', b'stuff 4', 'application/java')]
    with expected(MimeTypeConstraint):
        field.set_user_input(files)


@with_fixtures(FieldFixture)
def test_file_validation_max_files(fixture):
    """A maximum can be placed upon the number of files that may be uploaded.
    """


    field = FileField(allow_multiple=True, max_files=1)
    obj = fixture.model_object
    field.bind('file_value', obj)

    files = [UploadedFile('file1', b'stuff 1', '')]
    with expected(NoException):
        field.set_user_input(files)

    files = [UploadedFile('file1', b'stuff 2', ''), UploadedFile('file2', b'stuff 3', '')]
    with expected(MaxFilesConstraint):
        field.set_user_input(files)


@with_fixtures(FieldFixture)
def test_date_marshalling(fixture):
    """A DateField marshalls human readable date representation to a datetime.date object.
       (It tolerates non-precise input.)
    """


    field = DateField()
    obj = fixture.model_object

    field.bind('date_value', obj)

    # From input
    for input_string in ['10 November 2012', '10/11/2012']:
        field.from_input(input_string)
        assert obj.date_value == datetime.date(2012, 11, 10)

        # As input
    obj.date_value = datetime.date(2010, 11, 10)
    actual_output = field.as_input()
    assert actual_output == '10 Nov 2010'

@with_fixtures(FieldFixture)
def test_empty_date_value(fixture):
    """A DateField returns empty string when date is not provided.
    """

    field = DateField()
    obj = fixture.model_object

    field.bind('date_value', obj)

    field.from_input('')
    assert obj.date_value == None

    obj.date_value = None
    actual_output = field.as_input()
    assert actual_output == ''


@with_fixtures(FieldFixture)
def test_date_validation(fixture):
    """A DateField can validate its input based on a min or max value and expects fuzzy but sensible input."""


    field = DateField()
    obj = fixture.model_object

    field.bind('date_value', obj)

    # Case invalid
    with expected(DateConstraint):
        field.set_user_input('sdfdf')

    # Case valid
    with expected(NoException):
        field.set_user_input('13 Dec')

    limit_date = datetime.date(2012, 11, 13)
    before_limit = '12 Nov 2012'
    after_limit = '14 Nov 2012'

    # Case Max
    field = DateField(max_value=limit_date)
    with expected(MaxValueConstraint):
        field.set_user_input(after_limit)

    # Case Min
    field = DateField(min_value=limit_date)
    with expected(MinValueConstraint):
        field.set_user_input(before_limit)

