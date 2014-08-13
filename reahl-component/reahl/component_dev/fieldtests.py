# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
# -*- encoding: utf-8 -*-
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
import six
import datetime
import functools

from nose.tools import istest
from reahl.tofu import  Fixture, test, scenario
from reahl.stubble import EmptyStub, stubclass
from reahl.tofu import vassert, expected, NoException

from reahl.component.context import ExecutionContext
from reahl.component.exceptions import ProgrammerError, IsInstance, IsCallable, IncorrectArgumentError
from reahl.component.modelinterface import Field, FieldIndex, ReahlFields, exposed, Event,\
                             EmailField, PasswordField, BooleanField, IntegerField, \
                             DateField, DateConstraint, \
                             ValidationConstraint, RequiredConstraint, MinLengthConstraint, \
                             MaxLengthConstraint, PatternConstraint, AllowedValuesConstraint, \
                             EqualToConstraint, RemoteConstraint, IntegerConstraint, \
                             MaxValueConstraint, MinValueConstraint, Action, AdaptedMethod, secured,\
                             AccessRightsConstraint, Choice, ChoiceGroup, ChoiceField, MultiChoiceConstraint, MultiChoiceField,\
                             FileField, SingleFileConstraint, UploadedFile, FileSizeConstraint, \
                             MimeTypeConstraint, MaxFilesConstraint, SmallerThanConstraint, GreaterThanConstraint

class FieldMixin(object):
    def new_model_object(self):
        obj = EmptyStub()
        obj.an_attribute = 'field value'
        return obj
    
    def new_field(self, cls=Field, name='an_attribute', label='the label'):
        field = cls(label=label)
        field.bind(name, self.model_object)
        return field


class FieldFixture(Fixture, FieldMixin):
    pass

@istest
class FieldTests(object):
    @test(FieldFixture)
    def marshalling(self, fixture):
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
        vassert( fixture.model_object.an_attribute == 1 )

        # From python object back to string
        fixture.model_object.an_attribute = 0
        vassert( field.as_input() == 'zero' )


    @test(FieldFixture)
    def validation(self, fixture):
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
            vassert( fixture.model_object.an_attribute == 1 )

        # Input failing either validation_constraint result in the appropriate validation_constraint being raised
        with expected(StringLevelConstraint):
            field.from_input('unparsable string')
        with expected(PythonLevelConstraint):
            field.from_input('2')

        # If multiple constraints fail, the first one (in order added to the field) is the one reported
        field.add_validation_constraint(AllowedValuesConstraint([]))
        with expected(StringLevelConstraint):
            field.from_input('unparsable string')

    @test(FieldFixture)
    def field_metadata(self, fixture):
        """Fields provide metadata about their contents"""
        field = Field(default=2, required=True, label='A field')
        field.bind('fieldname', fixture.model_object)
        
        vassert( field.label == 'A field' )
        vassert( field.required )
        vassert( field.variable_name == 'fieldname' )  
        vassert( field.get_model_value() == 2 )

    @test(FieldFixture)
    def constraint_message(self, fixture):
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
        vassert( validation_constraint.label == fixture.field.label )

        # How the template is filled with attributes (and missing ones)
        expected = 'Bob âte $missing_attr boerpampoene on 20091124 the label'
        vassert( validation_constraint.message == expected )

    @test(Fixture)
    def meaning_of_required(self, fixture):
        """Making a Field required means adding a RequiredConstraint to it"""
        # Case: construction with default value for required
        field = Field()
        vassert( not field.required )       

        # Case: construction with required=True
        field = Field(required=True)
        vassert( field.required )
        vassert( field.get_validation_constraint_named(RequiredConstraint.name) )      
    

    @test(Fixture)
    def getting_modified_copy(self, fixture):
        """It is possible to get a modified copy of an existing field if you want to link it with 
           different constraints on a different input"""
        other_constraint = ValidationConstraint('Other error')
        other_constraint.name = 'other'
        field = Field()
        field.add_validation_constraint(other_constraint)

        # Getting a copy
        new_field = field.copy()
        vassert( new_field is not field )
        vassert( new_field.name == field.name )
        vassert( new_field.storage_object == field.storage_object )
        vassert( new_field.default == field.default )
        vassert( new_field.label == field.label )
        copied_other_constraint = new_field.get_validation_constraint_named(other_constraint.name)
        vassert( copied_other_constraint.field is new_field )
        new_validation_constraints = [i.__class__ for i in new_field.validation_constraints]
        old_validation_constraints = [i.__class__ for i in field.validation_constraints]
        vassert( new_validation_constraints == old_validation_constraints )
        vassert( new_field.validation_constraints != field.validation_constraints )
        vassert( new_field.validation_constraints is not field.validation_constraints )

        vassert( new_field.access_rights is not field.access_rights )
        vassert( new_field.access_rights.readable is field.access_rights.readable )
        vassert( new_field.access_rights.writable is field.access_rights.writable )

        # Getting a required copy
        vassert( not field.required )
        required_field = field.as_required(required_message='new required message')
        vassert( required_field.required )
        required = required_field.get_validation_constraint_named(RequiredConstraint.name)
        vassert( required.error_message.template == 'new required message' )

        # Getting copy that's not required
        field.make_required('')
        vassert( field.required )
        optional_field = field.as_optional()
        vassert( not optional_field.required )

        # Getting copy with a ValidationConstraint of certain type removed
        vassert( field.required )
        more_lax_field = field.as_without_validation_constraint(RequiredConstraint)
        vassert( not more_lax_field.required )
        
        # Getting copy with a new ValidationConstraint added
        field.make_optional()
        vassert( not field.required )
        more_strict_field = field.as_with_validation_constraint(RequiredConstraint())
        vassert( more_strict_field.required )
        

    @test(Fixture)
    def helpers_for_fields(self, fixture):
        """The @exposed decorator makes it simpler to bind Fields to an object."""
        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.field1 = IntegerField()
                fields.field2 = BooleanField()

        model_object = ModelObject()

        vassert( model_object.fields is model_object.fields )
        vassert( model_object.fields.field1.bound_to is model_object )
        vassert( model_object.fields.field2.bound_to is model_object )

    @test(Fixture)
    def helpers_for_fields2(self, fixture):
        """The ReahlFields class is an alternative way to make it simpler to bind Fields to an object.
           This reads a bit nicer, BUT does not currently play well with internationalising strings."""
        class ModelObject(object):
            fields = ReahlFields()
            fields.field1 = IntegerField()
            fields.field2 = BooleanField()

        class InheritingModelObject(ModelObject):
            fields = ReahlFields()
            fields.field3 = IntegerField()

        model_object = ModelObject()

        vassert( model_object.fields is model_object.fields )
        vassert( model_object.fields.field1.bound_to is model_object )
        vassert( model_object.fields.field2.bound_to is model_object )

        inheriting_object = InheritingModelObject()
        
        vassert( inheriting_object.fields is not model_object.fields )
        vassert( inheriting_object.fields is inheriting_object.fields )
        vassert( inheriting_object.fields.field1.bound_to is inheriting_object )
        vassert( inheriting_object.fields.field2.bound_to is inheriting_object )
        vassert( inheriting_object.fields.field3.bound_to is inheriting_object )

    @test(Fixture)
    def re_binding_behaviour_of_field_index(self, fixture):
        """FieldIndexes wont bind a field if it already is bound."""
        model_object1 = EmptyStub()
        model_object2 = EmptyStub()
        bound_field = Field()
        bound_field.bind('bound_field', model_object2)

        vassert( bound_field.is_bound )
        vassert( bound_field.bound_to is model_object2 )
        index = FieldIndex(model_object1)
        index.new_name_for_bound_field = bound_field
        vassert( index.new_name_for_bound_field.name is 'bound_field' )
        vassert( bound_field.bound_to is model_object2 )

    @test(Fixture)
    def helpers_for_events(self, fixture):
        """The @exposed decorator makes it simpler to collect Events on an object similar to how it is used for Fields."""
        class ModelObject(object):
            @exposed
            def events(self, fields):
                fields.event1 = Event()
                fields.event2 = Event()

        model_object = ModelObject()

        vassert( model_object.events is model_object.events )
        vassert( model_object.events.event1.bound_to is model_object.events.event1 )
        vassert( model_object.events.event2.bound_to is model_object.events.event2 )

        vassert( model_object.events.event1.name == 'event1' )

    @test(Fixture)
    def helpers_for_events2(self, fixture):
        """The @exposed decorator can be used to get FakeEvents at a class level, provided the valid Event names are specified."""
        class ModelObject(object):
            @exposed('event1')
            def events(self, fields):
                fields.event1 = Event()
                fields.event2 = Event()

        vassert( ModelObject.events.event1.name == 'event1' )

        with expected(AttributeError):
            ModelObject.events.nonevent

    @test(Fixture)
    def helpers_for_events3(self, fixture):
        """An Event has to be created for each of the names listed to the @exposed decorator, else an error is raised."""
        class ModelObject(object):
            @exposed('event1', 'forgotten')
            def events(self, fields):
                fields.event1 = Event()
                fields.event2 = Event()

        def check_exc(exc):
            vassert( six.text_type(exc).startswith('You promised to instantiate') )
        with expected(ProgrammerError, test=check_exc):
            ModelObject().events

    @test(Fixture)
    def events(self, fixture):
        """An Event defines a signal that can be sent to the system, with the intention to
           possibly trigger the execution of an Action by the system. Metadata, such as what
           a human might label the Event, is also specified."""
        
        class ModelObject(object):
            @exposed
            def events(self, events):
                events.an_event = Event(action=Action(self.do_something), label='human readable label')
                
            def do_something(self):
                self.something_done = True

        model_object = ModelObject()
        event = model_object.events.an_event.with_arguments()
        event.from_input(event.as_input())
        event.fire()

        vassert( model_object.something_done )
        vassert( model_object.events.an_event.label == 'human readable label' )

    @test(Fixture)
    def arguments_to_actions(self, fixture):
        """Arguments can be defined on an Event in order to be able to pass them to the linked Action 
           as args or kwargs as specified by the Action."""

        expected_arg = 123
        expected_kwarg = 45

        class ModelObject(object):
            @exposed
            def events(self, events):
                events.an_event = Event(one_argument=IntegerField(required=True),
                                        another_argument=IntegerField(),
                                        unused_argument=IntegerField(),
                                        action=Action(self.do_something,
                                                      ['one_argument'],
                                                      dict(a_kwarg='another_argument')))
                
            def do_something(self, an_arg, a_kwarg=None):
                self.passed_an_arg = an_arg
                self.passed_a_kwarg = a_kwarg

        model_object = ModelObject()
        event = model_object.events.an_event.with_arguments(one_argument=123, another_argument=45, unused_argument=678)
        event.from_input(event.as_input())
        event.fire()

        vassert( model_object.passed_an_arg is expected_arg )
        vassert( model_object.passed_a_kwarg is expected_kwarg )


    @test(Fixture)
    def arguments_to_event(self, fixture):
        """Only Action objects can be sent as action= when creating an Event. The arguments passed to readable and writable
           should be callable objects with correct signature."""

        # action=
        with expected(IsInstance):
            Event(action=EmptyStub())

        def check_exc(expected_message, ex):
            message = six.text_type(ex).split(':')[1][1:]
            vassert( message.startswith(expected_message) )

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


    @test(Fixture)
    def event_security(self, fixture):
        """If an Event specifies an Action, the access controls of the Action are
           used for access to the Event as well."""
        class ModelObject(object):
            allow_read_flag = True
            allow_write_flag = True
            def allow_read(self):
                return self.allow_read_flag

            def allow_write(self):
                return self.allow_write_flag

            @secured( read_check=allow_read, write_check=allow_write )
            def do_something(self):
                pass

            @exposed
            def events(self, events):
                events.an_event = Event(action=Action(self.do_something))


        model_object = ModelObject()
        event = model_object.events.an_event.with_arguments()
        event.from_input(event.as_input())
        
        event.fire()
        
        vassert( event.can_read() )
        vassert( event.can_write() )

        model_object.allow_read_flag = False
        vassert( not event.can_read() )

        model_object.allow_write_flag = False
        vassert( not event.can_write() )

        with expected(ProgrammerError):
            event.fire()



    @test(Fixture)
    def event_security2(self, fixture):
        """If an Event does not specify an Action, then Actions can be passed for its readable and writable."""
        class ModelObject(object):
            allow_read_flag = True
            allow_write_flag = True
            def allow_read(self):
                return self.allow_read_flag

            def allow_write(self):
                return self.allow_write_flag

            @exposed
            def events(self, events):
                events.an_event = Event(readable=Action(self.allow_read),
                                        writable=Action(self.allow_write))

        model_object = ModelObject()
        event = model_object.events.an_event.with_arguments()

        vassert( event.can_read() )
        vassert( event.can_write() )

        model_object.allow_read_flag = False
        vassert( not event.can_read() )

        model_object.allow_write_flag = False
        vassert( not event.can_write() )

    @test(Fixture)
    def event_security_action_and_rw(self, fixture):
        """Supply either an action or a readable/writable to an Event, but not both."""

        def do_nothing(): pass

        with expected(ProgrammerError):
            Event(action=Action(do_nothing), readable=Action(do_nothing))
        with expected(ProgrammerError):
            Event(action=Action(do_nothing), writable=Action(do_nothing))

    @test(Fixture)
    def receiving_events(self, fixture):
        """An Event is said to have occurred if it received a querystring containing its arguments from user input.
           An Event can only be fired if it occurred."""

        class ModelObject(object):
            @exposed
            def events(self, events):
                events.an_event = Event(an_argument=IntegerField())

        model_object = ModelObject()
        event = model_object.events.an_event.with_arguments(an_argument=123)
        
        vassert( event.default == {'an_argument': 123} )
        vassert( not hasattr(event, 'arguments') )
        vassert( not event.occurred )
        with expected(ProgrammerError):
            event.fire()
        
        event.from_input('?an_argument=123')
        vassert( event.arguments == {'an_argument': 123} )
        vassert( event.occurred )
        with expected(NoException):
            event.fire()


    class Scenarios(Fixture):
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

    @test(Scenarios)
    def security_of_receiving_events(self, fixture):
        """An Event can only occur if BOTH its access restrictions are allowed."""

        class ModelObject(object):
            def allow_read(self):
                return fixture.allow_read
            def allow_write(self):
                return fixture.allow_write
            @exposed
            def events(self, events):
                events.an_event = Event(readable=Action(self.allow_read), writable=Action(self.allow_write))

        model_object = ModelObject()
        event = model_object.events.an_event
        
        vassert( not event.occurred )
        with expected(fixture.expected_exception):
            event.from_input('?')
        vassert( event.occurred is fixture.expected_occurred )



@istest
class SpecificConstraintTests(object):
    @test(Fixture)
    def required_constraint(self, fixture):
        selector = 'find me'
        required_constraint = RequiredConstraint(selector_expression=selector)
        
        #selector is returned as parameter
        vassert( required_constraint.parameters == selector )
        
        #case: no input 
        with expected(RequiredConstraint):
            required_constraint.validate_input('')
        with expected(RequiredConstraint):
            required_constraint.validate_input(None)
        #just spaces
        space=' '                              
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

    @test(Fixture)
    def min_length_constraint(self, fixture):
        min_required_length = 5
        min_length_constraint = MinLengthConstraint(min_length=min_required_length)
        
        #min length is returned as parameter
        vassert( min_length_constraint.parameters == '%s' % min_required_length )
        
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
                        

    @test(Fixture)
    def max_length_constraint(self, fixture):
        max_allowed_length = 5
        max_length_constraint = MaxLengthConstraint(max_length=max_allowed_length)
        
        #max length is returned as parameter
        vassert( max_length_constraint.parameters == '%s' % max_allowed_length )
        
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


    @test(Fixture)
    def pattern_constraint(self, fixture):
        allow_pattern = '(ab)+'
        pattern_constraint = PatternConstraint(pattern=allow_pattern)
        
        #pattern is returned as parameter
        vassert( pattern_constraint.parameters == allow_pattern )
        
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
        
        
    @test(Fixture)
    def allowed_values_constraint(self, fixture):
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

    @test(Fixture)
    def equal_to_constraint(self, fixture):
        other_field = Field(label='other')
        equal_to_constraint = EqualToConstraint(other_field, '$label, $other_label')
        other_field.set_user_input('should be equal to this string', ignore_validation=True)

        #case: valid input
        with expected(NoException):
            equal_to_constraint.validate_parsed_value('should be equal to this string' )

        #case: invalid input
        with expected(EqualToConstraint):
            equal_to_constraint.validate_parsed_value('this is not equal')

    @test(Fixture)
    def smaller_than_constraint(self, fixture):
        other_field = IntegerField(label='other')
        smaller_than_constraint = SmallerThanConstraint(other_field, '$label, $other_label')
        other_field.set_user_input('5', ignore_validation=True)

        #case: valid input
        with expected(NoException):
            smaller_than_constraint.validate_parsed_value( 4 )

        #case: invalid input
        with expected(SmallerThanConstraint):
            smaller_than_constraint.validate_parsed_value( 5 )

    @test(Fixture)
    def greater_than_constraint(self, fixture):
        other_field = IntegerField(label='other')
        greater_than_constraint = GreaterThanConstraint(other_field, '$label, $other_label')
        other_field.set_user_input('5', ignore_validation=True)

        #case: valid input
        with expected(NoException):
            greater_than_constraint.validate_parsed_value( 6 )

        #case: invalid input
        with expected(GreaterThanConstraint):
            greater_than_constraint.validate_parsed_value( 5 )


@istest
class SpecificFieldsTests(object):
    @test(Fixture)
    def email_validation(self, fixture):
        field = EmailField()
        
        # Case: invalid
        invalid_addresses = ['somethingWithoutTheAt', '@somethingThatBeginsWithTheAT',
                                      'somethingThatEndsWithTheAt@', '@' ,None]
        for address in invalid_addresses:
            with expected(PatternConstraint):
                field.set_user_input(address)
            vassert( field.validation_error is field.get_validation_constraint_named('pattern') )

        # Case: valid
        valid_addresses = ['someone@home.co.za', 'something@somewhere.com', 'j@j.ca']
        for address in valid_addresses:
            with expected(NoException):
                field.set_user_input(address, ignore_validation=True)
            vassert( not field.validation_error )

    @test(Fixture)
    def password_validation(self, fixture):
        field = PasswordField()
        
        # Case: invalid
        with expected(MinLengthConstraint):
            field.set_user_input('123')
        vassert( field.validation_error is field.get_validation_constraint_named('minlength') )
        with expected(MaxLengthConstraint):
            field.set_user_input('1'*21)
        vassert( field.validation_error is field.get_validation_constraint_named('maxlength') )

        # Case: valid
        with expected(NoException):
            field.set_user_input('my passwôrd')
        vassert( not field.validation_error )

    @test(Fixture)
    def password_access(self, fixture):
        """A PasswordField is world writable, but not readable by anyone."""

        field = PasswordField()
        field.bind('password_field', fixture)
        vassert( not field.can_read() )
        vassert( field.can_write() )

    @test(Fixture)
    def boolean_validation(self, fixture):
        obj = EmptyStub()
        field = BooleanField()
        field.bind('boolean_attribute', obj)
        
        # Case: invalid
        invalid_boolean_name = ['negative', 'affirmative', '+', '-', None]
        for boolean_candidate in invalid_boolean_name:
            with expected(AllowedValuesConstraint):
                field.set_user_input(boolean_candidate)
            vassert( field.validation_error is field.get_validation_constraint_named('pattern') )

        # Case: valid
        field.from_input('on')
        vassert( obj.boolean_attribute is True )
        vassert( field.as_input() == 'on' )
        field.from_input('off')
        vassert( obj.boolean_attribute is False )
        vassert( field.as_input() == 'off' )

        # Case: required means True for BooleanField
        field = BooleanField(required=True)
        field.bind('boolean_attribute', obj)
        with expected(AllowedValuesConstraint):
            field.set_user_input('off')        
        vassert( field.validation_error is field.get_validation_constraint_named('pattern') )
        with expected(NoException):
            field.from_input('on')

    @test(Fixture)
    def boolean_i18n(self, fixture):
        @stubclass(ExecutionContext)
        class AfrikaansContext(ExecutionContext):
            @property
            def interface_locale(self):
                return 'af'
            
        with AfrikaansContext():
            obj = EmptyStub()
            field = BooleanField()
            field.bind('boolean_attribute', obj)

            # Case: valid
            field.from_input('aan')
            vassert( obj.boolean_attribute is True )
            vassert( field.as_input() == 'aan' )
            field.from_input('af')
            vassert( obj.boolean_attribute is False )
            vassert( field.as_input() == 'af' )


    @test(Fixture)
    def integer_validation(self, fixture):
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


    @test(Fixture)
    def basic_marshalling(self, fixture):
        field = Field()
        obj = EmptyStub()
        field.bind('value', obj)

        # From input
        field.from_input('abc')
        vassert( obj.value == 'abc' )

        # As input
        obj.value = 'def'
        vassert( field.as_input() == 'def' )

        # As input - corner case
        obj.value = ''
        vassert( field.as_input() == '' )

    @test(Fixture)
    def integer_marshalling(self, fixture):
        field = IntegerField()
        obj = EmptyStub()
        field.bind('integer_value', obj)

        # From input
        field.from_input('5')
        vassert( obj.integer_value is 5 )

        # As input
        obj.integer_value = 6
        vassert( field.as_input() == '6' )

        # As input - corner case
        obj.integer_value = 0
        vassert( field.as_input() == '0' )

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
            self.input_to_value_map = {'1': 1, '2': '2'}
            self.expected_validation_constraint = AllowedValuesConstraint

        @scenario
        def grouped_choices(self):
            self.all_choices = [Choice(1, IntegerField(label='One')), 
                                Choice('2', Field(label='Two'))]
            self.groups = [ChoiceGroup('', self.all_choices)]
            self.choices = self.groups
            self.valid_inputs = ['1', '2']
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
            self.input_to_value_map = {('1',): [1], ('1', '2'): [1,2]}
            self.expected_validation_constraint = MultiChoiceConstraint

    @test(ChoiceFixture)
    def choice_querying(self, fixture):
        """A ChoiceField maintains a list of the Choices and Groups it was constructed with."""
        field = fixture.field
        
        vassert( field.groups == fixture.groups )
        vassert( field.flattened_choices == fixture.all_choices )


    @test(ChoiceFixture)
    def choice_validation(self, fixture):
        """Input for a ChoiceField is valid only if it matches one of its Choices."""
        field = fixture.field

        # Case invalid
        with expected(fixture.expected_validation_constraint):
            field.set_user_input('sdfdf')

        # Case valid
        for i in fixture.valid_inputs:
            with expected(NoException):
                field.set_user_input(i)


    @test(ChoiceFixture)
    def choice_field_marshalling(self, fixture):
        """Input for a ChoiceField is marshalled differently, depending on the Field specified for the Choice matching the input."""
        field = fixture.field
        obj = fixture.model_object
        
        # From input
        for valid_input, value in fixture.input_to_value_map.items():
            field.from_input(valid_input)
            vassert( obj.choice_value == value )

        # As input
        for expected_input, value in fixture.input_to_value_map.items():
            obj.choice_value = value
            if isinstance(expected_input, tuple):
                expected_input = list(expected_input)
            vassert( field.as_input() == expected_input )


    @test(FieldFixture)
    def file_marshalling(self, fixture):
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
        vassert( obj.file_value == files[0] )

        obj.file_value = files[0]
        vassert( field.as_input() == '' )

        # Multiple files
        field = FileField(allow_multiple=True)
        field.bind('file_value', obj)

        field.from_input(files)
        vassert( obj.file_value == files )

        obj.file_value = files
        vassert( field.as_input() == '' )

    @test(FieldFixture)
    def file_validation(self, fixture):
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

    @test(FieldFixture)
    def file_validation_size(self, fixture):
        """A FileField can also limit the size if files uploaded.
        """

        field = FileField(allow_multiple=True, max_size_bytes=100)
        obj = fixture.model_object
        field.bind('file_value', obj)

        files = [UploadedFile('file1', EmptyStub(), '', 100), UploadedFile('file2', EmptyStub(), '', 50)]
        with expected(NoException):
            field.set_user_input(files)

        files = [UploadedFile('file1', EmptyStub(), '', 100), UploadedFile('file2', EmptyStub(), '', 200)]
        with expected(FileSizeConstraint):
            field.set_user_input(files)

    @test(FieldFixture)
    def file_validation_mime_type(self, fixture):
        """A FileField can also limit the mimetype of files allowed to be uploaded.
        """

        field = FileField(allow_multiple=True, accept=['text/*'])
        obj = fixture.model_object
        field.bind('file_value', obj)

        files = [UploadedFile('file1', EmptyStub(), 'text/html', 100), UploadedFile('file2', EmptyStub(), 'text/xml', 50)]
        with expected(NoException):
            field.set_user_input(files)

        files = [UploadedFile('file1', EmptyStub(), 'text/html', 100), UploadedFile('file2', EmptyStub(), 'application/java', 200)]
        with expected(MimeTypeConstraint):
            field.set_user_input(files)

    @test(FieldFixture)
    def file_validation_max_files(self, fixture):
        """A maximum can be placed upon the number of files that may be uploaded.
        """

        field = FileField(allow_multiple=True, max_files=1)
        obj = fixture.model_object
        field.bind('file_value', obj)

        files = [UploadedFile('file1', EmptyStub(), '', 100)]
        with expected(NoException):
            field.set_user_input(files)

        files = [UploadedFile('file1', EmptyStub(), '', 100), UploadedFile('file2', EmptyStub(), '', 200)]
        with expected(MaxFilesConstraint):
            field.set_user_input(files)


    @test(FieldFixture)
    def date_marshalling(self, fixture):
        """A DateField marshalls human readable date representation to a datetime.date object.
           (It tolerates non-precise input.)
        """

        field = DateField()
        obj = fixture.model_object
        
        field.bind('date_value', obj)
        
        # From input
        for input_string in ['10 November 2012', '10/11/2012']:
            field.from_input(input_string)
            vassert( obj.date_value == datetime.date(2012, 11, 10) )

        # As input
        obj.date_value = datetime.date(2010, 11, 10)
        actual_output = field.as_input()
        vassert( actual_output == '10 Nov 2010' )

    @test(FieldFixture)
    def date_validation(self, fixture):
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



