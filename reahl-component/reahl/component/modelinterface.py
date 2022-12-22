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

"""Facilities to govern user input and output, as well as what access the current user has to model objects."""


import io
import copy
import re
import fnmatch
import functools
import sre_constants
import urllib.parse
import warnings
from string import Template
import inspect
from contextlib import contextmanager
import json
from collections import OrderedDict

import dateutil.parser 
import babel.dates 
from babel.core import Locale
from babel.numbers import parse_decimal, format_number
from wrapt import FunctionWrapper, BoundFunctionWrapper


from reahl.component.decorators import deprecated, memoized
from reahl.component.i18n import Catalogue
from reahl.component.context import ExecutionContext
from reahl.component.exceptions import AccessRestricted, ProgrammerError, arg_checks, IsInstance, IsCallable, NotYetAvailable
from collections.abc import Callable



_ = Catalogue('reahl-component')

class ConstraintNotFound(Exception):
    pass

class ObjectDictAdapter:
    def __init__(self, wrapped_dict):
        self.wrapped_dict = wrapped_dict
    def __getattr__(self, name):
        try:
            return self.wrapped_dict[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        if name != 'wrapped_dict':
            self.wrapped_dict[name]=value
        else:
            super().__setattr__(name, value)


class FieldIndex:
    """A named collection of :class:`Field` instances applicable to an object. 
    
       Programmers should not construct this class, an instance is automatically created when accessing
       a :class:`ExposedNames` class attribute on an instance. (See :class:`ExposedNames` )

       When used in conjuction with :class:`Field`\s declared on a :class:`ExposedNames`, construction
       of an individual :class:`Field` is delayed until it is accessed on the the FieldIndex::

         def create_field(i):
             print('creating')
             return Field()
           
         class Person:
             fields = ExposedNames()
             fields.name = create_field
             fields.age = create_field

         person.fields.name # prints 'creating'
         person.fields.name # does not create it again
         person.fields.age  # prints 'creating'

       .. versionchanged:: 6.1
          Deprecated: an instance of this class is also passed to methods marked as @exposed. 
          (See :class:`ExposedDecorator` )

    """
    def __init__(self, storage_object):
        super().__init__()
        self.fields = {}
        self.field_factories = {}
        self.storage_object = storage_object

    def __setattr__(self, name, value):
        assert not isinstance(value, tuple)
        if isinstance(value, Field):
            self.fields[name] = value
            if not value.is_bound:
                value.bind(str(name), self.storage_object)

        if callable(value):
            self.field_factories[name] = (value, self.storage_object)
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        factory, storage_object = self.field_factories[name]
        field = factory(storage_object)
        if not field.is_bound:
            field.bind(name, storage_object)
        setattr(self, name, field)
        return field
        
    def set(self, name, value):
        return setattr(self, name, value)

    def keys(self):
        return list(self.fields.keys()) + [key for key in self.field_factories.keys() if key not in self.fields]

    def contains_instantiated_value(self, field):
        return field in self.fields.values()
        
    def instantiate_fields_from_factories(self):
        for name, (factory, storage_object) in self.field_factories.items():
            if name not in self.fields:
                field = factory(storage_object)
                if not field.is_bound:
                    field.bind(name, storage_object)
                setattr(self, name, field)
                
    def values(self):
        self.instantiate_fields_from_factories()
        return self.fields.values()

    def items(self):
        self.instantiate_fields_from_factories()
        return self.fields.items()

    def as_kwargs(self):
        return dict([(name, field.get_model_value()) for name, field in self.items()])

    def as_input_kwargs(self, qualify_names=True):
        if qualify_names:
            return dict([(field.name_in_input, field.as_input()) for field in self.values()])
        else:
            return dict([(field.name, field.as_input()) for field in self.values()])
    
    def accept_input(self, input_dict, ignore_validation=False):
        for name, field in self.items():
            field.from_disambiguated_input(input_dict, ignore_validation=ignore_validation)
            
    def update_from_other(self, other):
        if isinstance(other, dict):
            for name, value in other.items():
                setattr(self, name, value)
        else:
            self.fields.update(other.fields)
            for name, value in other.fields.items():
                setattr(self, name, value)
            self.field_factories.update(other.field_factories)

    def update_copies(self, other):
        if isinstance(other, dict):
            for name, value in other.items():
                setattr(self, name, value.copy())
        else:
            for name, value in other.fields.items():
                self.fields[name] = copied_value = value.copy()
                setattr(self, name, copied_value)
            self.field_factories.update(other.field_factories)

    def update_from_class(self, reahl_fields):
        items = reahl_fields.__dict__.items()
        for name, value in items:
            if callable(value):
                self.field_factories[name] = (value, self.storage_object)


class StandaloneFieldIndex(FieldIndex):
    @classmethod
    def from_list(cls, list_of_fields):
        i = cls()
        for field in list_of_fields:
            setattr(i, field.name, field)
        return i
        
    def __init__(self, backing_dict=None):
        backing_dict = backing_dict or {}
        super().__init__(ObjectDictAdapter(backing_dict))

    @property
    def backing_dict(self):
        return self.storage_object.wrapped_dict
    
    def accept_parsed(self, value_dict):
        self.backing_dict.update(value_dict)

    def validate_defaults(self):
        for field in self.fields.values():
            field.validate_default()

            
@deprecated('Please use :class:`ExposedNames` instead.')
class ExposedDecorator:
    """This class has the alias "exposed". Apply it as decorator to a method declaration to indicate that the method defines
       a number of Fields. The decorated method is passed an instance of :class:`FieldIndex` to which each Field should be assigned. 
       Each such Field is associated with an similarly named attribute on each instance of the current class.

       :param args: A list of names of Fields that will be defined by this method. This is used when accessing the
                    resultant FieldIndex on a class, instead of on an instance.

       .. versionchanged:: 6.1
          Deprecated: use :class:`ExposedNames` instead.
    """
    def __init__(self, *args):
        self.expected_event_names = []
        if isinstance(args[0], str):
            self.add_fake_events(args)
            self.func = None
        else:
            self.func = args[0]
            functools.update_wrapper(self, self.func)

    @property
    def name(self):
        return self.func.__name__

    def add_fake_events(self, event_names):
        events = []
        self.expected_event_names.extend(event_names)
        for name in event_names:
            event = FakeEvent(name)
            setattr(self, name, event)
            events.append(event)
        return events

    def __call__(self, func):
        self.func = func
        functools.update_wrapper(self, self.func)
        return self
        
    def __get__(self, instance, owner):
        if not instance:
            return self

        if not hasattr(instance, '__exposed__'):
            instance.__exposed__ = {}

        model_object = instance
        try:
            return instance.__exposed__[self]
        except KeyError:
            seen = []
            field_index = FieldIndex(model_object)
            for _class in reversed(model_object.__class__.mro()):
                if hasattr(_class, self.name):
                    exposed_declaration = getattr(_class, self.name)
                    if exposed_declaration not in seen:
                        seen.append(exposed_declaration)
                        if isinstance(exposed_declaration, ExposedDecorator):
                            exposed_declaration.func(model_object, field_index)
                        elif isinstance(exposed_declaration, ExposedNames):
                            field_index.update_from_class(exposed_declaration)
                        else:
                            raise ProgrammerError('%s on %s is not a ExposedNames or ExposedDecorator' % (self.name, _class))
            instance.__exposed__[self] = field_index

        self.func(model_object, field_index)

        if self.expected_event_names:
            declared_fields = set(field_index.keys())
            expected_fields = set(self.expected_event_names)
            missing_fields = expected_fields - declared_fields
            if missing_fields:
                raise ProgrammerError('You promised to instantiate "%s" in %s of %s but did not do so' % \
                                          (','.join(missing_fields), self.func, model_object))

        return field_index

    def __getattr__(self, name):
        raise AttributeError('%s has no attribute \'%s\' - did you perhaps write @exposed instead of @exposed(\'%s\')?' % \
                            (self, name, name))


exposed = ExposedDecorator


class FakeEvent:
    isEvent = True
    def __init__(self, name):
        self.name = name
        
class FieldFactory:
    @arg_checks(a_callable=IsCallable(args=(NotYetAvailable('i'),)))
    def __init__(self, name, a_callable):
        self.name = name
        self.callable = a_callable

    def __call__(self, storage_object):
        return self.callable(storage_object)

    
class ExposedNames:
    """Use ExposedNames to create a namespace on a class for the purpose of declaring
       all the Field or all the Event instances bound to an instance of that class.

       To create a namespace, assign an instance of ExposedNames to a class attribute named for
       the needed namespace (ie, `fields`). For each Field/Event needed, assign a callable 
       to an attributes on the ExposedNames.

       The callable will be passed a single argument: the instance of the class it will be bound to..
       It should return a Field or Event instance.

       For example::

          class Person:
              def __init__(self, name):
                  self.name = name
                  self.age = 0

              fields = ExposedNames()
              fields.age = lambda i: IntegerField(name='Age of %s' % i.name)

              events = ExposedNames()
              events.submit = lambda i: Event(Action(i.submit))

              def submit(self):
                  pass


       This is similar to how SqlAlchemy or Django ORM declare columns
       on a class which are used to save corresponding attributes of
       an instance to columns in a database table.

       For example, with SQLAlchemy you could have::

          class Person(Base):
             id = Column(Integer, primary_key=True)
             name = Column(String)
             age = Column(Integer)

       ExposedNames is different in that it allows you to declare your Fields or Events
       in a namespace of their own. ExposedNames can thus be used in conjunction with, say, 
       SQLAlchemy on the same instance::

          class Person(Base):
             id = Column(Integer)
             name = Column(String)
             age = Column(Integer)

             fields = ExposedNames()
             fields.name = lambda i: Field(label='Name')
             fields.age = lambda i: IntegerField(label='Age')

          p = Person()
          p.name = 'Jane'
          p.age = 25

          Session.save(p)  # Saves Jane/25 to database with some auto generated id
  
          assert p.fields.age.as_input() == '25'

          p.fields.age.from_input('28')  
          assert p.age == 28  # Which means since SqlAlchemy will save the age attribute, it will now save 28 to the database

      .. versionadded:: 6.1

    """
    def _find_name(self, cls):
        for name in dir(cls):
            if getattr(cls, name) is self:
                return name
        raise ProgrammerError('This should never happen')
    
    def __get__(self, instance, cls):
        if not instance:
            return self
        my_name = self._find_name(cls)

        idx = FieldIndex(instance)
        seen = []
        for class_ in reversed(cls.mro()):
            if hasattr(class_, my_name):
                exposed_declaration = getattr(class_, my_name)
                if exposed_declaration not in seen:
                    seen.append(exposed_declaration)
                    if isinstance(exposed_declaration, ExposedDecorator):
                        exposed_declaration.func(instance, idx)
                    elif isinstance(exposed_declaration, ExposedNames):
                        idx.update_from_class(exposed_declaration)
                    else:
                        raise ProgrammerError('%s on %s is not a ExposedNames or ExposedDecorator' % (my_name, class_))
                
        setattr(instance, my_name, idx)
        return idx

    def __setattr__(self, name, value):
        super().__setattr__(name, FieldFactory(name, value))
        

class ReadRights:
    def __init__(self, access_rights, field):
        self.field = field
        self.access_rights = access_rights

    def __call__(self):
        return self.access_rights.can_read(self.field)

    @property
    def is_specified(self):
        return self.access_rights.readable is not None


class AccessRights:
    def __init__(self, readable=None, writable=None):
        self.readable = readable
        self.writable = writable

    def get_bound_read_rights(self, field):
        return ReadRights(self, field)

    def has_right(self, right, field):
        if right is None:
            return True
        return right(field)
    
    def can_read(self, field):
        return self.has_right(self.readable, field)

    def can_write(self, field):
        return self.has_right(self.writable, field)

    def copy(self):
        return copy.copy(self)


class ValidationConstraint(Exception):
    """A ValidationConstraint is responsible for checking that a given value is deemed valid input. Each 
       ValidationConstraint only checks one aspect of the validity of a given Field. The ValidationConstraint
       first checks a string sent as user input, but can afterwards also validate the resultant Python object
       which was created based on such string input.
       
       :keyword error_message: The error message shat should be shown to a user if input failed this ValidationConstraint.
                             This error_message is a string containing a `PEP-292 <http://www.python.org/dev/peps/pep-0292/>`_
                             template. Attributes of the ValidationConstraint can be referred to by name in variable 
                             references of this template string.
    """
    is_remote = False
    name = ''  # A unique name for this type of constraint. Only one Constraint with a given name is allowed per Field.

    def __init__(self, error_message=None):
        error_message = error_message or _('$label is invalid')
        Exception.__init__(self)
        self.error_message = Template(error_message)
        self.field = None
        self.prepared_error_message = ''
    
    def __reduce__(self):
        self.prepared_error_message = self.label
        reduced = super().__reduce__()
        pickle_dict = reduced[2]
        del pickle_dict['field']
        return reduced

    def set_field(self, field):
        self.field = field

    def copy_for_field(self, field):
        new_copy = self.new_for_copy()
        new_copy.__dict__.update(self.__dict__)
        new_copy.set_field(field)
        return new_copy

    def new_for_copy(self):
        return self.__class__(self.error_message)
    
    def validate_input(self, unparsed_input):
        """Override this method to provide the custom logic of how this ValidationConstraint should check
           the given string for validity. If validation fails, this method should raise self.
        """
    
    def validate_parsed_value(self, parsed_value):
        """Override this method to provide the custom logic of how this ValidationConstraint should check
           the given Python object after it was created from initial input in string form. If validation 
           fails, this method should raise self.
        """

    def __getitem__(self, name):
        try:
            return getattr(self, name)
        except AttributeError:
            raise KeyError(name)
    
    @property
    def parameters(self):
        """Override this property to supply parameters for this ValidationConstraint. Parameters are used
           by user interface mechanics outside the scope of this module for implementation reasons.
        """
        return ''
        
    @property
    def message(self):
        """The message to display to a user if this ValidationConstraint is failed by some input."""
        return self.error_message.safe_substitute(self)

    @property
    def label(self):
        """The textual label displayed to users for the Field to which this ValidationConstraint is linked."""
        return self.prepared_error_message or (self.field.label if self.field else '')

    @property
    def value(self):
        """The current value which failed validation."""
        return self.field.user_input

    def __str__(self):
        return self.message



class RemoteConstraint(ValidationConstraint):
    """A ValidationConstraint which can only be executed on the server. Create a subclass of this class 
       and override `validate_input` and `validate_parsed_value`.
    
       :keyword error_message: (See :class:`ValidationConstraint`)
    """
    is_remote = True
    name = 'remote'
    def __init__(self, error_message=None):
        error_message = error_message or _('$label is not valid')
        super().__init__(error_message)


class AccessRightsConstraint(ValidationConstraint):
    def validate_input(self, unparsed_input):
        if not self.field.can_write():
            raise self


class ValidationConstraintList(list):
    def copy_for_field(self, field):
        new_list = ValidationConstraintList()
        for validation_constraint in self:
            constraint_copy = validation_constraint.copy_for_field(field)
            new_list.append(constraint_copy)
        return new_list

    def append(self, constraint):
        if constraint.name and self.has_constraint_named(constraint.name):
            message = 'You have already added %s, and are trying to add %s, both of which are named "%s". At present, you can only add one constraint per constraint name.'
            message = message % (repr(self.get_constraint_named(constraint.name)), repr(constraint), constraint.name)
            raise ProgrammerError(message)
        super().append(constraint)

    def has_constraint_named(self, name):
        return name in [validation_constraint.name for validation_constraint in self]

    def get_constraint_of_class(self, cls):
        for validation_constraint in self:
            if isinstance(validation_constraint, cls):
                return validation_constraint
        raise ConstraintNotFound(cls)

    def get_constraint_named(self, name):
        for validation_constraint in self:
            if validation_constraint.name == name:
                return validation_constraint
        raise ConstraintNotFound(name)

    def remove_constraint_named(self, name):
        validation_constraint = self.get_constraint_named(name)
        self.remove(validation_constraint)

    def validate_input(self, unparsed_input, ignore=None):
        for validation_constraint in self:
            if not (ignore and isinstance(validation_constraint, ignore)):
                validation_constraint.validate_input(unparsed_input)

    def validate_parsed(self, parsed_value, ignore=None):
        for validation_constraint in self:
            if not (ignore and isinstance(validation_constraint, ignore)):
                validation_constraint.validate_parsed_value(parsed_value)


class RequiredConstraint(ValidationConstraint):
    """The presence of this ValidationConstraint on a Field indicates that the Field is required.
    
       :keyword dependency_expression: RequiredConstraint is conditional upon this jquery selector expression matching more 
                                     than 0 elements. By default this matches all elements, making the RequiredConstraint 
                                     non-conditional.
       :keyword error_message: (See :class:`ValidationConstraint`)

       .. versionchanged:: 5.0
          Renamed selector_expression to dependency_expression.
    """
    name = 'required'
    empty_regex = re.compile('^ +$')

    def __init__(self, dependency_expression='*', error_message=None):
        error_message = error_message or _('$label is required')
        super().__init__(error_message)
        self.dependency_expression = dependency_expression

    @property
    def parameters(self):
        return self.dependency_expression

    def validate_input(self, unparsed_input):
        if isinstance(unparsed_input, str) and self.empty_regex.match(unparsed_input):
            raise self
        if not unparsed_input:
            raise self


class Comparison:
    def __init__(self, compare_function, error_message):
        self.compare_function = compare_function
        self.error_message = error_message
    
    def compare(self, one, other):
        return self.compare_function(one, other)


class ComparingConstraint(ValidationConstraint):
    def __init__(self, other_field, comparison):
        error_message = comparison.error_message 
        super().__init__(error_message)
        self.other_field = other_field
        self.comparison = comparison

    @property
    def other_label(self):
        return self.other_field.label
    
    @property
    def parameters(self):
        return self.other_field.name_in_input

    def validate_parsed_value(self, parsed_value):
        if not self.comparison.compare(parsed_value, self.other_field.parsed_input):
            raise self


class EqualToConstraint(ComparingConstraint):
    """A ValidationConstraint that requires the value of its Field to be equal to the value input into `other_field`.

       :param other_field: The Field whose value must be equal to the Field to which this ValidationConstraint is attached.
       :keyword error_message: (See :class:`ValidationConstraint`)
    """
    name = 'equalTo2'

    def __init__(self, other_field, error_message=None):
        def equal_to(one, other): return one == other
        equals = Comparison(equal_to, error_message or _('$label should be equal to $other_label'))
        super().__init__(other_field, equals)
        

class GreaterThanConstraint(ComparingConstraint):
    """A ValidationConstraint that requires the value of its Field to be greater than the value input into `other_field` (the > operator is used for the comparison).

       :param other_field: The Field whose value is compared.
       :keyword error_message: (See :class:`ValidationConstraint`)
    """
    name = 'greaterThan'

    def __init__(self, other_field, error_message=None):
        def greater_than(one, other): return one > other
        greater = Comparison(greater_than, error_message or _('$label should be greater than $other_label'))
        super().__init__(other_field, greater)


class SmallerThanConstraint(ComparingConstraint):
    """A ValidationConstraint that requires the value of its Field to be smaller than the value input 
       into `other_field` (the < operator is used for the comparison).
    
       :param other_field: The Field whose value is compared.
       :keyword error_message: (See :class:`ValidationConstraint`)
    """
    name = 'smallerThan'

    def __init__(self, other_field, error_message=None):
        def smaller_than(one, other): return one < other
        smaller = Comparison(smaller_than, error_message or _('$label should be smaller than $other_label'))
        super().__init__(other_field, smaller)


class MinLengthConstraint(ValidationConstraint):
    """A ValidationConstraint that requires length of what the user typed to be at least `min_length` characters long.
       
       :param min_length: The minimum allowed length of the input.
       :keyword error_message: (See :class:`ValidationConstraint`)
    """
    name = 'minlength'

    def __init__(self, min_length, error_message=None):
        error_message = error_message or _('$label should be $min_length characters or longer')
        super().__init__(error_message)
        self.min_length = min_length
    
    @property
    def parameters(self):
        return str(self.min_length)

    def validate_input(self, unparsed_input):
        if (unparsed_input is not None) and (len(unparsed_input) <  self.min_length):
            raise self


class MaxLengthConstraint(ValidationConstraint):
    """A ValidationConstraint that requires length of what the user typed to not be more than `max_length` 
       characters long.
       
       :param max_length: The maximum allowed length of the input.
       :keyword error_message: (See :class:`ValidationConstraint`)
    """
    name = 'maxlength'

    def __init__(self, max_length, error_message=None):
        error_message = error_message or _('$label should not be longer than $max_length characters')
        super().__init__(error_message)
        self.max_length = max_length

    @property
    def parameters(self):
        return str(self.max_length)

    def validate_input(self, unparsed_input):
        if (unparsed_input is not None) and (len(unparsed_input) > self.max_length):
            raise self


class PatternConstraint(ValidationConstraint):
    """A ValidationConstraint that requires unparsed input to match the supplied regex.
       
       :param pattern: The regex to match input against.
       :keyword error_message: (See :class:`ValidationConstraint`)

       .. versionchanged:: 6.1
          Arg pattern changed to also be able to be a callable to delay the computation of the pattern.

    """
    name = 'pattern'

    def __init__(self, pattern, error_message=None):
        error_message = error_message or _('$label is invalid')
        super().__init__(error_message)
        self._pattern = pattern

    @property
    def pattern(self):
        if callable(self._pattern):
            return self._pattern()
        else:
            return self._pattern

    @property
    def parameters(self):
        return self.pattern

    def validate_input(self, unparsed_input):
        try:
            regex = re.compile('^%s$' % self.pattern)
            match = regex.match(unparsed_input)
        except TypeError:
            match = None
        except sre_constants.error as ex:
            raise ProgrammerError(_('Invalid pattern: %s' % repr(ex)))
        if not match:
            raise self


class AllowedValuesConstraint(PatternConstraint):
    """A PatternConstraint that only allows unparsed input equal to one of a list of `allowed_values`.
       
       :param allowed_values: A list containing the strings values to be allowed.
       :keyword error_message: (See :class:`ValidationConstraint`)

       .. versionchanged:: 6.1
          Arg allowed_values changed to also be able to be a callable to delay the fetching of values to be allowed.

    """
    def new_for_copy(self):
        return self.__class__(self._allowed_values, error_message=self.error_message)

    def __init__(self, allowed_values, error_message=None):
        error_message = error_message or _('$label should be one of the following: $allowed')
        self._allowed_values = allowed_values
        def allowed_regex():
            return '(%s)' % self.allowed
        super().__init__(allowed_regex, error_message)

    @property
    def allowed_values(self):
        if callable(self._allowed_values):
            return self._allowed_values()
        else:
            return self._allowed_values

    @property
    def allowed(self):
        return '|'.join(self.allowed_values)
    

class IntegerConstraint(PatternConstraint):
    """A PatternConstraint that only allows input that represent a valid integer.
       
       :keyword error_message: (See :class:`ValidationConstraint`)
    """
    def __init__(self, error_message=None):
        error_message = error_message or _('$label should be an integer number')
        super().__init__('[-0123456789]+', error_message)

    def validate_input(self, unparsed_input):
        super().validate_input(unparsed_input)
        # (for good measure we do not rely on the regex alone)
        try:
            int(unparsed_input)
        except ValueError:
            raise self


class MinValueConstraint(ValidationConstraint):
    """A ValidationConstraint that requires its parsed input to be greater than or equal to a supplied `min_value`.
       (To do the comparison, the >= operator is used on the parsed value.)
       
       :param min_value: The minimum value allowed.
       :keyword error_message: (See :class:`ValidationConstraint`)
    """
    name = 'minvalue'

    def __init__(self, min_value, error_message=None):
        error_message = error_message or _('$label should be $min_value or greater')
        super().__init__(error_message=error_message)
        self.min_value = min_value

    def validate_parsed_value(self, parsed_value):
        if not (parsed_value >= self.min_value):
            raise self


class MaxValueConstraint(ValidationConstraint):
    """A ValidationConstraint that requires its parsed input to be smaller than or equal to a supplied `max_value`.
       (To do the comparison, the <= operator is used on the parsed value.)
       
       :param max_value: The maximum value allowed.
       :keyword error_message: (See :class:`ValidationConstraint`)
    """
    name = 'maxvalue'

    def __init__(self, max_value, error_message=None):
        error_message = error_message or _('$label should be no greater than $max_value')
        super().__init__(error_message=error_message)
        self.max_value = max_value

    def validate_parsed_value(self, parsed_value):
        if not (parsed_value <= self.max_value):
            raise self


class InputParseException(Exception):
    pass

class ExpectedInputNotFound(Exception):
    def __init__(self, input_name, searched_inputs):
        super().__init__('Expected to find %s in %s' % (input_name, str(searched_inputs)))

class FieldData:
    def __init__(self):
        self.initial_value = None
        self.input_status = None
        self.validation_error = None
        self.user_input = None
        self.parsed_input = None
       
class Field:
    """A Field represents something which can be input by a User.
    
       A Field is responsible for transforming user input from a string into a Python object which that string 
       represents. Different kinds of Fields marshall input to different kinds of Python object. This (base) class 
       does no marshalling itself, the parsed Python object is just the input string as given. Subclasses override 
       this behaviour.
       
       A Field also manages the validation of such input, based on a list of individual instances 
       of :class:`ValidationConstraint` added to the Field.
       
       The final parsed value of a Field is set as an attribute on a Python object to which the Field is bound.
       (See also :class:`ExposedNames`).

       :keyword default: The default (parsed) value if no user input is given.
       :keyword required: If True, indicates that input is always required for this Field.
       :keyword required_message: See ``error_message`` of :class:`RequiredConstraint`.
       :keyword label: A text label by which to identify this Field to a user.
       :keyword readable: A callable that takes one argument (this Field). It is executed to determine whether
                        the current user is allowed to see this Field. Returns True if the user is allowed,
                        else False.
       :keyword writable: A callable that takes one argument (this Field). It is executed to determine whether
                        the current user is allowed supply input for this Field. Returns True if the user is
                        allowed, else False.
       :keyword disallowed_message: An error message to be displayed when a user attempts to supply input
                        to this Field when it is not writable for that user. (See ``error_message`` of
                        :class:`ValidationConstraint`.)
       :keyword min_length: The minimum number of characters allowed in the user supplied input.
       :keyword max_length: The maximum number of characters allowed in the user supplied input.

       .. versionchanged:: 4.0
          Added min_length and max_length kwargs.
    """
    entered_input_type = str
    @arg_checks(readable=IsCallable(allow_none=True, args=(NotYetAvailable('field'),)), writable=IsCallable(allow_none=True, args=(NotYetAvailable('field'),)))
    def __init__(self, default=None, required=False, required_message=None, label=None,
                 readable=None, writable=None, disallowed_message=None,
                 min_length=None, max_length=None):
        if required and default:
            raise ProgrammerError('Both required and default are provided.'
                                  ' Default is only used when no value is provided by the user.'
                                  ' Required prevents this from happening.')
        self._name = None
        self.namespace = []
        self.storage_object = None
        self.default = default
        self.label = label or ''
        self.validation_constraints = ValidationConstraintList()
        self.add_validation_constraint(AccessRightsConstraint(disallowed_message or _('Not allowed')))
        self.access_rights = AccessRights(readable=readable, writable=writable)
        if required:
            self.make_required(required_message)
        if min_length:
            self.add_validation_constraint(MinLengthConstraint(min_length))
        if max_length:
            self.add_validation_constraint(MaxLengthConstraint(max_length))
        self.data = FieldData()
        self.clear_user_input()

    def get_data(name, self):
        return getattr(self.data, name)
    def set_data(name, self, value):
        return setattr(self.data, name, value)

    initial_value = property(functools.partial(get_data, 'initial_value'), functools.partial(set_data, 'initial_value'))
    input_status = property(functools.partial(get_data, 'input_status'), functools.partial(set_data, 'input_status'))
    validation_error = property(functools.partial(get_data, 'validation_error'), functools.partial(set_data, 'validation_error'))
    user_input = property(functools.partial(get_data, 'user_input'), functools.partial(set_data, 'user_input'))
    parsed_input = property(functools.partial(get_data, 'parsed_input'), functools.partial(set_data, 'parsed_input'))

    def push_namespace(self, namespace):
        self.namespace.append(namespace)

    def pop_namespace(self):
        self.namespace.pop()

    def activate_global_field_data_store(self, global_field_data_store):
        try:
            self.data = global_field_data_store[self.name_in_input]
        except KeyError:
            global_field_data_store[self.name_in_input] = self.data
            self.initial_value = self.get_model_value()

    def validate_default(self):
        unparsed_input = self.as_input()
        self.validate_input(unparsed_input, ignore=AccessRightsConstraint)
        self.validate_parsed(self.parse_input(unparsed_input), ignore=AccessRightsConstraint)

    def __str__(self):
        name_part = '(not bound)'
        if self.is_bound:
            name_part = 'name=%s' % self.name
        return '<%s %s>' % (self.__class__.__name__, name_part)

    @property
    def can_read(self):
        return self.access_rights.get_bound_read_rights(self)

    def can_write(self):
        return self.access_rights.can_write(self)

    def make_required(self, required_message):
        """Forces this Field to be required, using `required_message` as an error message."""
        message = required_message or _('$label is required')
        self.add_validation_constraint(RequiredConstraint(error_message=message))

    def as_required(self, required_message=None):
        """Returns a new Field which is exactly like this one, except that the new Field is required, using
           `required_message`."""
        new_version = self.copy()
        new_version.make_required(required_message)
        return new_version

    def make_optional(self):
        """Forces this Field to be optional (not required)."""
        self.remove_validation_constraint(RequiredConstraint)

    def as_optional(self):
        """Returns a new Field which is exactly like this one, except that the new Field is optional."""
        new_version = self.copy()
        new_version.make_optional()
        return new_version
    
    def remove_validation_constraint(self, validation_constraint_class):
        try:
            self.validation_constraints.remove_constraint_named(validation_constraint_class.name)
        except ConstraintNotFound:
            pass

    def copy(self):
        new_version = copy.copy(self)
        new_version.validation_constraints = self.validation_constraints.copy_for_field(new_version)
        new_version.access_rights = self.access_rights.copy()
        new_version.namespace = self.namespace.copy()
        new_version.data = copy.copy(self.data)
        return new_version

    def unbound_copy(self):
        new_version = self.copy()
        new_version.unbind()
        return new_version

    def without_validation_constraint(self, validation_constraint_class):
        """Returns a new Field which is exactly like this one, except that the new Field does not include 
           a ValidationConstraint of the class given as `validation_constraint_class`.

        .. versionchanged:: 4.0
           Changed name to be consistent with conventions for `with_` methods.
        """
        new_version = self.copy()
        new_version.remove_validation_constraint(validation_constraint_class)
        return new_version
        
    def with_validation_constraint(self, validation_constraint):
        """Returns a new Field which is exactly like this one, except that the new Field also includes 
           the ValidationConstraint given as `validation_constraint`.

        .. versionchanged:: 4.0
           Changed name to be consistent with conventions for `with_` methods.
        """
        new_version = self.copy()
        new_version.add_validation_constraint(validation_constraint)
        return new_version

    def with_label(self, label):
        """Returns a new Field which is exactly like this one, except that its label is set to 
           the given text.

        .. versionadded:: 5.0
        """
        new_version = self.copy()
        new_version.label = label
        return new_version

    def with_discriminator(self, discriminator):
        """Returns a new Field which is exactly like this one, except that its name is mangled
        to include the given text as to prevent name clashes.

        .. versionadded:: 5.0
        """
        new_field = self.copy()
        new_field.push_namespace(discriminator)
        return new_field

    def in_namespace(self, namespace):
        new_field = self.copy()
        new_field.push_namespace(namespace)
        new_field.data = self.data
        return new_field

    def out_of_namespace(self):
        new_field = self.copy()
        new_field.pop_namespace()
        new_field.data = self.data
        return new_field
        
    def clear_user_input(self):
        self.input_status = 'defaulted'
        self.validation_error = None
        self.user_input = None
        self.parsed_input = self.default
    
    def is_input_empty(self, input_value):
        return input_value == ''

    def set_user_input(self, input_value, ignore_validation=False, skip_validation_constraint=None):
        self.clear_user_input()
        self.user_input = input_value

        if not self.required and self.is_input_empty(input_value):
            self.input_status = 'validly_entered'
        else:
            try:
                self.input_status = 'invalidly_entered'
                self.validate_input(input_value, ignore=skip_validation_constraint)
                self.parsed_input = self.parse_input(input_value)
                self.validate_parsed(self.parsed_input, ignore=skip_validation_constraint)
                self.input_status = 'validly_entered'
            except ValidationConstraint as ex:
                self.validation_error = ex
                if not ignore_validation:
                    raise

    def bind(self, name, storage_object):
        if self.is_bound:
            warnings.warn('DEPRECATED: %s is bound to %s already. Call unbind() first if you intend to bind it again. This warning will be an error in 7.0' % (self, self.storage_object), DeprecationWarning, stacklevel=1)
            #raise ProgrammerError('%s is already bound to %s' % (self, self.storage_object))
        self._name = name
        if not self.label:
            self.label = name
        self.storage_object = storage_object

    def unbind(self):
        self.storage_object = None

    @property
    def is_bound(self):
        return self.bound_to is not None

    @property
    def bound_to(self):
        return self.storage_object
    
    def get_validation_constraint_named(self, name):
        return self.validation_constraints.get_constraint_named(name)

    def get_validation_constraint_of_class(self, cls):
        return self.validation_constraints.get_constraint_of_class(cls)

    @property
    def required(self):
        return self.validation_constraints.has_constraint_named(RequiredConstraint.name)
     
    @property
    def name(self):
        if not self._name:
            raise AssertionError('field %s with label "%s" is not yet bound' % (self, self.label))
        return '-'.join(reversed([self._name] + self.namespace))

    @property
    def variable_name(self):
        if not self._name:
            raise AssertionError('field %s with label "%s" is not yet bound' % (self, self.label))
        return self._name

    def qualify_name(self, name):
        return name

    @property
    def name_in_input(self):
        return self.qualify_name(self.name)

    def get_model_value(self):
        return getattr(self.storage_object, self.variable_name, self.default)
        
    def set_model_value(self):
        setattr(self.storage_object, self.variable_name, self.parsed_input)

    def validate_input(self, unparsed_input, ignore=None):
        self.validation_constraints.validate_input(unparsed_input, ignore=ignore)

    def format_input(self, unparsed_input):
        return self.unparse_input(self.parse_input(unparsed_input))
    
    def input_as_string(self, unparsed_input):
        return unparsed_input

    def validate_parsed(self, parsed_value, ignore=None):
        self.validation_constraints.validate_parsed(parsed_value, ignore=ignore)

    def update_valid_value_in_disambiguated_input(self, input_dict):
        input_dict[self.name_in_input] = self.as_user_input_value(for_input_status='defaulted')

    def extract_unparsed_input_from_dict_of_lists(self, input_dict):
        list_of_input = input_dict.get(self.name_in_input, [])
        if list_of_input:
            return list_of_input[0]
        else:
            return self.as_input()

    def from_disambiguated_input(self, input_dict, ignore_validation=False, ignore_access=False):
        input_value = self.extract_unparsed_input_from_dict_of_lists(input_dict)
        self.from_input(input_value, ignore_validation=ignore_validation, ignore_access=ignore_access)

    def parse_input(self, unparsed_input):
        """Override this method on a subclass to specify how that subclass transforms the `unparsed_input`
           (a string) into a representative Python object."""
        return unparsed_input

    def unparse_input(self, parsed_value):
        """Override this method on a subclass to specify how that subclass transforms a given Python
           object (`parsed_value`) to a string that represents it to a user."""
        return str(parsed_value if parsed_value is not None else '')

    def from_input(self, unparsed_input, ignore_validation=False, ignore_access=False):
        """Sets the value of this Field from the given `unparsed_input`."""
        if self.can_write() or ignore_access:
            self.from_input_regardless_access(unparsed_input, ignore_validation=ignore_validation)

    def from_input_regardless_access(self, unparsed_input, ignore_validation=False):
        self.set_user_input(unparsed_input, ignore_validation=ignore_validation, skip_validation_constraint=AccessRightsConstraint)
        if self.input_status == 'validly_entered':
            self.set_model_value()

    def as_user_input_value(self, for_input_status=None):
        return self.input_as_string(self.as_list_unaware_user_input_value(for_input_status=for_input_status))

    def get_initial_value_as_user_input(self):
        return self.input_as_string(self.unparse_input(self.initial_value))

    def as_list_unaware_user_input_value(self, for_input_status=None):
        if (for_input_status or self.input_status) == 'defaulted' or (not self.can_read()):
            return self.as_input()
        else:
            return self.user_input

    def as_input(self):
        """Returns the value of this Field as a string."""
        if self.can_read():
            return self.unparse_input(self.get_model_value())
        return ''

    def add_validation_constraint(self, validation_constraint):
        """Adds the given `validation_constraint` to this Field. All ValidationConstraints added to the
           Field are used in order, to validate input supplied to the Field."""
        validation_constraint.set_field(self)
        self.validation_constraints.append(validation_constraint)
        return validation_constraint


class AdaptedMethod:
    def __init__(self, declared_method, arg_names=[], kwarg_name_map={}):
        self.declared_method = declared_method
        self.arg_names = arg_names
        self.kwarg_name_map = kwarg_name_map
        self.kwarg_name_map_reversed = dict([(sent_name, adapted_to_name)
                                             for adapted_to_name, sent_name in kwarg_name_map.items()])
        self.full_arg_names = arg_names
        self.full_kwarg_names = kwarg_name_map.values()
        
    def set_full_arg_names(self, full_arg_names, full_kwarg_names=[]):
        self.full_arg_names = full_arg_names
        self.full_kwarg_names = full_kwarg_names
        
    def __call__(self, *args, **kwargs):
        args_to_send = self.get_args_to_send(args)
        kwargs_to_send = self.get_kwargs_to_send(kwargs)
        return self.declared_method(*args_to_send, **kwargs_to_send)

    def get_args_to_send(self, args_received):
        args_to_send = []
        for name in self.arg_names:
            i = self.full_arg_names.index(name)
            args_to_send.append(args_received[i])
        return args_to_send
            
    def get_kwargs_to_send(self, kwargs_received):
        kwargs_to_send = {}
        for name, value in kwargs_received.items():
            if name in self.kwarg_name_map_reversed:
                kwargs_to_send[self.kwarg_name_map_reversed[name]] = value
        return kwargs_to_send


class Action(AdaptedMethod):
    """An Action which is supplied to an :class:`Event` is executed when that :class:`Event` occurs.
       Executing the Action means executing its `declared_method`.
       
       :param declared_method: The method to be called when executing this Action.
       :param arg_names: A list of the names of Event arguments to send to `declared_method` as positional arguments
                         (in the order listed).
       :keyword kwarg_name_map: A dictionary specifying which keyword arguments to send to `declared_method` when called.
                         The dictionary maps each name of an Event argument that needs to be sent 
                         to the name of the keyword argument as which it should be sent.
    """
    def __call__(self, field):
        event = field
        event_arguments = event.get_model_value()
        args = [event_arguments[name] for name in self.arg_names]
        kwargs = dict([(name, event_arguments[name])
                       for name in self.kwarg_name_map_reversed.keys()])
        return super().__call__(*args, **kwargs)


    @property
    def readable(self):
        if isinstance(self.declared_method, (SecuredMethod, SecuredFunction)):
            return Action(self.declared_method._self_read_check, arg_names=self.arg_names, kwarg_name_map=self.kwarg_name_map)
        return None
    @property
    def writable(self):
        if isinstance(self.declared_method, (SecuredMethod, SecuredFunction)):
            return Action(self.declared_method._self_write_check, arg_names=self.arg_names, kwarg_name_map=self.kwarg_name_map)
        return None


class Allowed(Action):
    """An Action that always returns the (boolean) value of `allowed` with which it was constructed."""
    def __init__(self, allowed):
        super().__init__(self.is_allowed)
        self.allowed = allowed

    def is_allowed(self):
        return self.allowed


class Not(Action):
    """An Action which returns the boolean inverse of the result of another `action`."""
    def __init__(self, action):
        super().__init__(action.declared_method, arg_names=action.arg_names, kwarg_name_map=action.kwarg_name_map)
    def __call__(self, field):
        return not super().__call__(field)


class Event(Field):
    """An Event can be triggered by a user. When an Event occurs, the `action` of the Event is executed.
       

       :keyword label: (See :class:`Field`)
       :keyword action: The :class:`Action` to execute when this Event occurs.
       :keyword readable: (See :class:`Field`)
       :keyword writable: (See :class:`Field`)
       :keyword disallowed_message: (See :class:`Field`)
       :keyword event_argument_fields: Keyword arguments given in order to specify the names of the arguments
                        this Event should have. The value to each keyword argument is a Field
                        governing input to that Event argument.
    """
    @arg_checks(action=IsInstance(Action, allow_none=True), 
                readable=IsCallable(allow_none=True, args=(NotYetAvailable('self'),)), 
                writable=IsCallable(allow_none=True, args=(NotYetAvailable('self'),)))
    def __init__(self, label=None, action=None, readable=None, writable=None, disallowed_message=None, **event_argument_fields):
        label = label or ''
        if action and (readable or writable):
            raise ProgrammerError('either specify an action or readable/writable but not both')
        readable = action.readable if action else readable
        writable = action.writable if action else writable

        super().__init__(required=False, required_message=None, label=label, readable=readable, writable=writable, disallowed_message=disallowed_message)
        self.action = action or (lambda *args, **kwargs: None)
        self.event_argument_fields = event_argument_fields
        self.event_return_argument_name = None

    def __str__(self):
        argument_string = (', %s' % str(self.arguments)) if hasattr(self, 'arguments') else ''
        return 'Event(%s%s)' % (self.name, argument_string)
    
    def from_input(self, unparsed_input, ignore_validation=False, ignore_access=False):
        # Note: this needs to happen for Events whether you are allowed to write the Event or not,
        #       because during validation, an AccessRightsConstraint is raised
        #       (In the case of other Fields, input to non-writable Fields is silently ignored)
        if ignore_access:
            raise ProgrammerError('You cannot ignore_access on an Event')
        self.set_user_input(unparsed_input, ignore_validation=ignore_validation)

        super().from_input(unparsed_input, ignore_validation=ignore_validation, ignore_access=False)

    @property
    def occurred(self):
        if self.user_input:
            return self.user_input.startswith('?') and self.can_write()
        return False

    def can_write(self):
        return self.can_read() and super().can_write()

    def fire(self):
        """Fire this event - which executes the Action of the event."""
        if not self.occurred:
            raise ProgrammerError('attempted to fire Event that has not occurred: %s' % self)

        return_value = self.action(self)
        if self.event_return_argument_name:
            self.arguments[self.event_return_argument_name] = return_value

    def make_occurred(self):
        self.bind('arguments', self)
        arguments = {}
        self.ensure_values_for_all_arguments(arguments)
        unparsed_input = self.unparse_input(arguments)
        self.from_input(unparsed_input, ignore_validation=True)
        
    def bind(self, name, storage_object):
        super().bind(name, self)

    def copy(self):
        new_field = super().copy()
        new_field.unbind()
        new_field.bind(new_field._name, new_field)
        return new_field

    def ensure_values_for_all_arguments(self, arguments):
        for declared_argument_name, argument_field in self.event_argument_fields.items():
            if declared_argument_name not in arguments:
                arguments[declared_argument_name] = argument_field.default
    
    def with_arguments(self, **event_arguments):
        """Returns a new Event exactly like this one, but with argument values as given."""
        arguments = event_arguments.copy()
        self.ensure_values_for_all_arguments(arguments)

        new_field = self.copy()
        new_field.default = arguments
        return new_field

    def with_returned_argument(self, event_argument_name):
        """Returns a new Event exactly like this one, but indicates that the action of this event will return a value for the given argument name.

           .. versionadded:: 6.1
        """
        arguments = {event_argument_name:''}
        for declared_argument_name, argument_field in self.event_argument_fields.items():
            if declared_argument_name != event_argument_name:
                arguments[declared_argument_name] = argument_field.default

        new_field = self.copy()
        new_field.default = arguments
        new_field.event_return_argument_name = event_argument_name
        return new_field

    @property
    def variable_name(self):
        return u'arguments'
   
    def parse_input(self, unparsed_input):
        if unparsed_input:
            arguments_query_string = unparsed_input[1:]
            raw_input_values = dict([(k,v) for k, v in urllib.parse.parse_qs(arguments_query_string).items()])
            fields = StandaloneFieldIndex()
            fields.update_copies(self.event_argument_fields)
            fields.accept_input(raw_input_values)
            
            view_arguments = dict([(k,v[0]) for k, v in urllib.parse.parse_qs(arguments_query_string).items()
                                   if not k in fields.items()])
            arguments = view_arguments.copy()
            arguments.update(fields.as_kwargs())
            return arguments
        return None

    def unparse_input(self, parsed_value):
        if parsed_value:
            arguments = parsed_value.copy()
            fields = StandaloneFieldIndex(arguments)
            fields.update_copies(self.event_argument_fields)
            
            arguments.update(fields.as_input_kwargs())
            input_string = '?%s' % urllib.parse.urlencode(arguments)
            return input_string
        else:
            return '?'
    

class SecuredMethod(BoundFunctionWrapper):
    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
    def _self_read_check(self, *args, **kwargs):
        return self._self_parent.check_right(self.read_check, self._self_instance, *args, **kwargs)
    def _self_write_check(self, *args, **kwargs):
        return self._self_parent.check_right(self.write_check, self._self_instance, *args, **kwargs)


class SecuredFunction(FunctionWrapper):
    __bound_function_wrapper__ = SecuredMethod

    def __init__(self,  wrapped, read_check, write_check):
        super().__init__(wrapped, self.check_call_wrapped)
        self.check_and_setup_check(read_check)
        self._self_read_check = self.read_check = read_check

        self.check_and_setup_check(write_check)
        self._self_write_check = self.write_check = write_check

    def check_and_setup_check(self, check):
        if isinstance(check, AdaptedMethod):
            check.set_full_arg_names(self.get_declared_argument_names())
        if not isinstance(check, AdaptedMethod) and isinstance(check, Callable):
            self.check_method_signature(check, self.__wrapped__)

    def check_call_wrapped(self, wrapped, instance, args, kwargs):
        if not (self.check_right(self.read_check, instance, *args, **kwargs)
                and
                self.check_right(self.write_check, instance, *args, **kwargs)):
            raise AccessRestricted()
        return wrapped(*args, **kwargs)

    def check_right(self, right_to_check, instance, *args, **kwargs):
        if right_to_check:
            args_to_send = (args if instance is None
                            else (instance,)+args)
            return right_to_check(*args_to_send, **kwargs)
        else:
            return True

    def check_method_signature(self, check_method, original_method):
        check_signature = inspect.signature(check_method)
        expected_signature = inspect.signature(original_method)
        if check_signature != expected_signature:
            messages = [repr(method) + str(signature)
                        for signature, method in [(check_signature, check_method),
                                                  (expected_signature, original_method)]]
            message = 'signature of %s does not match expected signature of %s' % tuple(messages)
            raise ProgrammerError(message)

    def get_declared_argument_names(self):
        arg_spec = inspect.getfullargspec(self.__wrapped__)
        positional_args_end = len(arg_spec.args)-len(arg_spec.defaults or [])
        return arg_spec.args[:positional_args_end]


class SecuredDeclaration:
    """A decorator for marking a method as being @secured. Marking a method as @secured, causes a wrapper
       to be placed around the original method. The wrapper checks the access rights of the current user
       before each call to the method to ensure unauthorised users cannot call the wrapped method.
       
       When such a @secured method is used as the `declared_method` of an :class:`Action`, the :class:`Action`
       derives its access constraints directly from the @secured method.
       
       :keyword read_check: A callable with signature matching that of the @secured method. It should
                          return True to indicate that the current user may be aware of the method, else False.
                          User interface machinery could use this info to determine what to show to a user,
                          what to grey out, or what to hide completely, depending on who the current user is.
       
       :keyword write_check: A callable with signature matching that of the @secured method. It should
                           return True to indicate that the current user may execute the method, else False.
       
    """
    def __init__(self, read_check=None, write_check=None):
        self.read_check = read_check
        self.write_check = write_check

    def __call__(self, func):
        return SecuredFunction(func, self.read_check, self.write_check)

secured = SecuredDeclaration #: An alias for :class:`SecuredDeclaration`


class CurrentUser(Field):
    """A Field whose value is always set to the party of the account currently logged in."""
    def __init__(self):
        from reahl.domain.systemaccountmodel import LoginSession
        account = LoginSession.for_current_session().account
        if account:
            party = account.owner
        else:
            party = None
        super().__init__(required=party is None, default=party)
        self.bind('current_account', self)
        
    def parse_input(self, unparsed_input):
        return self.default

    def unparse_input(self, parsed_value):
        return 'The current account'


class EmailField(Field):
    """A Field representing a valid email address. Its parsed value is the given string."""
    def __init__(self, default=None, required=False, required_message=None, label=None, readable=None, writable=None):
        label = label or ''
        super().__init__(default, required, required_message, label, readable=readable, writable=writable, max_length=254)
        error_message=_('$label should be a valid email address')
        self.add_validation_constraint(PatternConstraint('[^\s]+@[^\s]+\.[^\s]{2,4}', error_message))


class PasswordField(Field):
    """A Field representing a password. Its parsed value is the given string, but the user is not
       allowed to see its current value."""
    def __init__(self, default=None, required=False, required_message=None, label=None, writable=None, min_length=6, max_length=20):
        label = label or ''
        super().__init__(default, required, required_message, label, readable=Allowed(False), writable=writable, min_length=min_length, max_length=max_length)


class IntegerField(Field):
    """A Field that yields an integer.
    
       :keyword min_value: The minimum value allowed as valid input.
       :keyword max_value: The maximum value allowed as valid input.
       
       (For other arguments, see :class:`Field`.)
    """
    def __init__(self, default=None, required=False, required_message=None, label=None, readable=None, writable=None, min_value=None, max_value=None):
        label = label or ''
        super().__init__(default, required, required_message, label, readable=readable, writable=writable)
        self.add_validation_constraint(IntegerConstraint())
        if min_value:
            self.add_validation_constraint(MinValueConstraint(min_value))
        if max_value:
            self.add_validation_constraint(MaxValueConstraint(max_value))

    def parse_input(self, unparsed_input):
        return int(unparsed_input)


class NumericField(Field):
    """A Field that yields any number that has a decimal point followed by digits that show the fractional part.

       :keyword precision: The number of decimal digits allowed.
       :keyword min_value: The minimum value allowed as valid input.
       :keyword max_value: The maximum value allowed as valid input.

       (For other arguments, see :class:`Field`.)

       .. versionadded:: 5.2

       """
    def __init__(self, default=None, precision=2, required=False, required_message=None, label=None, readable=None, writable=None, min_value=None, max_value=None):
        label = label or ''
        super().__init__(default, required, required_message, label, readable=readable, writable=writable, max_length=254)
        error_message = _('$label should be a valid number')

        locale = Locale.parse(ExecutionContext.get_context().interface_locale)
        plus = locale.number_symbols['plusSign']
        minus = locale.number_symbols['minusSign']
        decimal = locale.number_symbols['decimal']
        decimal_regex = '\.' if decimal == '.' else decimal
        group_separator = locale.number_symbols['group']
        group_separator_regex = '\.' if group_separator == '.' else group_separator
        regex_str = '[%s%s]?([0-9%s]+%s?[0-9%s]{0,%s})' % (plus, minus, group_separator_regex, decimal_regex, group_separator_regex, precision)

        self.add_validation_constraint(PatternConstraint(regex_str, error_message))
        if min_value:
            self.add_validation_constraint(MinValueConstraint(min_value))
        if max_value:
            self.add_validation_constraint(MaxValueConstraint(max_value))

    def parse_input(self, unparsed_input):
        return parse_decimal(unparsed_input, ExecutionContext.get_context().interface_locale)

    def unparse_input(self, parsed_value):
        if parsed_value is None:
            return ''
        return format_number(parsed_value, ExecutionContext.get_context().interface_locale)


class JsonField(Field):
    """
        A field that parses a JSON formatted string to a python dictionary object.

        .. versionadded:: 5.2

    """
    def parse_input(self, unparsed_input):
        return json.loads(unparsed_input if unparsed_input != '' else 'null')

    def unparse_input(self, parsed_value):
        return json.dumps(parsed_value)


class DateConstraint(ValidationConstraint):
    def validate_input(self, unparsed_input):
        try:
            self.field.parse_input(unparsed_input)
        except InputParseException:
            raise self
    
    def validate_parsed_value(self, parsed_value):
        pass


class DateField(Field):
    """A Field that can parse a Python Date from a given user input string. The input string need not
       conform to strict format -- a DateField does its best to parse what is given. The names of
       months, days, etc that may be typed by a user are parsed according to the current language in use.

       :keyword min_value: The earliest value allowed as valid input.
       :keyword max_value: The latest value allowed as valid input.
       :keyword date_format: Specify which format (short/medium/long/full) of the current locale to use for dates. 
                             (See https://babel.pocoo.org/en/latest/api/dates.html#date-and-time-formatting )

       (For other arguments, see :class:`Field`.)

        .. versionchanged:: 6.1
           Added date_format keyword
    """
    def __init__(self, default=None, date_format='medium', min_value=None, max_value=None, required=False, required_message=None, label=None, readable=None, writable=None):
        if date_format not in ['short','medium','long','full']:
            raise ProgrammerError('date_format=%s is not a valid format. Should be one of \'short\',\'medium\',\'long\',\'full\'' % date_format)
        label = label or ''
        super().__init__(default, required, required_message, label, readable=readable, writable=writable)
        self.date_format = date_format
        self.add_validation_constraint(DateConstraint())
        if min_value:
            self.add_validation_constraint(MinValueConstraint(min_value))
        if max_value:
            self.add_validation_constraint(MaxValueConstraint(max_value))

    def is_day_first_in_format_pattern(self):
        date_pattern = babel.dates.get_date_format(format=self.date_format, locale=_.current_locale)
        unique_chars = ''.join(OrderedDict.fromkeys(str(date_pattern))).lower()
        return unique_chars.index('d') < unique_chars.index('m')

    @property
    def parser_info(self):
        class ParserInfo(dateutil.parser.parserinfo):
            WEEKDAYS = [(_('Mon'), _('Monday')),
                    (_('Tue'), _('Tuesday')),
                    (_('Wed'), _('Wednesday')),
                    (_('Thu'), _('Thursday')),
                    (_('Fri'), _('Friday')),
                    (_('Sat'), _('Saturday')),
                    (_('Sun'), _('Sunday'))]
            MONTHS   = [(_('Jan'), _('January')),
                    (_('Feb'), _('February')),
                    (_('Mar'), _('March')),
                    (_('Apr'), _('April')),
                    (_('May'), _('May')),
                    (_('Jun'), _('June')),
                    (_('Jul'), _('July')),
                    (_('Aug'), _('August')),
                    (_('Sep'), _('September')),
                    (_('Oct'), _('October')),
                    (_('Nov'), _('November')),
                    (_('Dec'), _('December'))]

            HMS = [(_('h'), _('hour'), _('hours')),
                   (_('m'), _('minute'), _('minutes')),
                   (_('s'), _('second'), _('seconds'))]
            AMPM = [(_('am'), _('a')),
                    (_('pm'), _('p'))]
            UTCZONE = [_('UTC'), _('GMT'), _('Z')]
            PERTAIN = [_('of')]
            JUMP = [' ', '.', ',', ';', '-', '/', '\'',
                    _('at'), _('on'), _('and'), _('ad'), _('m'), _('t'), _('of'),
                    _('st'), _('nd'), _('rd'), _('th')]
        return ParserInfo()

    def parse_input(self, unparsed_input):
        try:
            return dateutil.parser.parse(unparsed_input, dayfirst=self.is_day_first_in_format_pattern(), parserinfo=self.parser_info).date()
            #Cannot use bable parse reliably. See https://github.com/python-babel/babel/issues/541
            #babel.dates.parse_date(unparsed_input, format=self.date_format, locale=_.current_locale)
            #and
            #print(dateparser.parse('12/12/12', locales=['en-US'])) # does not support en-US
        except (ValueError, TypeError):  # For TypeError, see https://bugs.launchpad.net/dateutil/+bug/1247643
            raise InputParseException()

    def unparse_input(self, parsed_value):
        if not parsed_value:
            return ''
        return babel.dates.format_date(parsed_value, format=self.date_format, locale=_.current_locale)


class Choice:
    """One possible Choice to be allowed as input for a ChoiceField.
    
       :param value: The Python value represented by this Choice.
       :param field: A Field able to marshall the value of this Choice.
                     The label of this Field is used as a string to represent this Choice
                     to a user.
    """
    def __init__(self, value, field):
        self._value = value
        self._value_as_set = None
        self.field = field
        self.field.bind('value', self)
    
    def get_value(self):
        return self._value
    def set_value(self, value):
        self._value_as_set = value
    value = property(get_value, set_value)
        
    def matches_input(self, unparsed_input):
        try:
            self.field.from_input(unparsed_input)
            return self._value_as_set == self.value
        except ValidationConstraint:
            return False
        
    def as_input(self):
        return self.field.as_input()

    @property
    def choices(self):
        return [self]

    @property
    def groups(self):
        return []


class ChoiceGroup:
    """Different :class:`Choice` instances can be grouped together. User interface machinery can
       use this information for display purposes.

       :param label: A name for the group to display.
       :param choices: The list of choices in this ChoiceGroup.
    """
    def __init__(self, label, choices):
        self.label = label
        self.choices = choices

    @property
    def groups(self):
        return [self]
    

class MultiChoiceConstraint(ValidationConstraint):
    def __init__(self, choices, error_message=None):
        error_message = error_message or _('$label should be a subset of $choice_input_values')
        super().__init__(error_message=error_message)
        self._choices = choices

    @property
    def choices(self):
        if callable(self._choices):
            return self._choices()
        else:
            return self._choices
 
    @property
    def choice_input_values(self):
        return [choice.as_input() for choice in self.choices]

    @property
    def choice_values(self):
        return [choice.value for choice in self.choices]

    def validate_input(self, unparsed_input):
        if not set(unparsed_input).issubset(set(self.choice_input_values)):
            raise self
    
    def validate_parsed_value(self, parsed_value):
        if not set(parsed_value).issubset(set(self.choice_values)):
            raise self


class ChoiceField(Field):
    """A Field that only allows the value of one of the given :class:`Choice` instances as input.
    
       :param grouped_choices: A list (or callable that will return a list) of :class:`Choice` or :class:`ChoiceGroup` 
                               instances from which a user should choose a single :class:`Choice`. If a callable,
                               it will be invoked at the last possible time to ensure an up-to-date list is obtained.
                               
       (For other arguments, see :class:`Field`.)

       .. versionchanged:: 6.1
          Kwarg grouped_choices changed to also be able to be a callable to delay the fetching of choices.
    """
    def __init__(self, grouped_choices, default=None, required=False, required_message=None, label=None, readable=None, writable=None):
        super().__init__(default, required, required_message, label, readable=readable, writable=writable)
        self._grouped_choices = grouped_choices
        self.init_validation_constraints()
        
    @property
    @memoized
    def grouped_choices(self):
        if callable(self._grouped_choices):
            return self._grouped_choices()
        else:
            return self._grouped_choices
        
    @property
    def allows_multiple_selections(self):
        return False

    def are_choices_unique(self, flattened_choices):
        return len(flattened_choices) == len(set([choice.value for choice in flattened_choices]))

    def init_validation_constraints(self):
        def allowed_values():
            return [choice.as_input() for choice in self.flattened_choices]
        self.add_validation_constraint(AllowedValuesConstraint(allowed_values))

    @property
    def flattened_choices(self):
        return self.flatten_choices(self.grouped_choices)

    def flatten_choices(self, grouped_choices):
        flattened = []
        for item in grouped_choices:
            flattened.extend(item.choices)
        if not self.are_choices_unique(flattened):
            raise ProgrammerError('Duplicate choices are not allowed')
        return flattened

    @property
    def groups(self):
        groups = []
        for item in self.grouped_choices:
            groups.extend(item.groups)
        return groups
        
    def parse_input(self, unparsed_input):
        for choice in self.flattened_choices:
            if choice.matches_input(unparsed_input):
                return choice.value
        raise ProgrammerError('The AllowedValuesConstraint added to a ChoiceField should have prevented this line from being reached.')


class BooleanField(ChoiceField):
    """A Field that can only have one of two parsed values: True or False. The string representation of
       each of these values are given in `true_value` or `false_value`, respectively.  (These default
       to 'on' and 'off' initially.)
    """
    def __init__(self, default=None, required=False, required_message=None, label=None, readable=None, writable=None, true_value=None, false_value=None):
        true_value = true_value or _('on')
        false_value = false_value or _('off')
        label = label or ''
        if required:
            error_message = required_message or _('$label is required')
            grouped_choices = [Choice(true_value, Field(label=true_value))]
        else:
            error_message = None
            grouped_choices = [Choice(true_value, Field(label=true_value)), Choice(false_value, Field(label=false_value))]
        super().__init__(grouped_choices, default=default, required=required, required_message=error_message, label=label, readable=readable, writable=writable)
        self.true_value = true_value
        self.false_value = false_value

    def parse_input(self, unparsed_input):
        return self.true_value == super().parse_input(unparsed_input)

    def unparse_input(self, parsed_value):
        if parsed_value:
            return self.true_value
        return self.false_value


class MultiChoiceField(ChoiceField):
    """A Field that allows a selection of values from the given :class:`Choice` instances as input."""
    entered_input_type = list

    def qualify_name(self, name):
        return '%s[]' % super().qualify_name(name)

    def is_input_empty(self, input_value):
        return input_value is None

    @property
    def allows_multiple_selections(self):
        return True

    def init_validation_constraints(self):
        def delayed_choices():
            return self.flattened_choices
        self.add_validation_constraint(MultiChoiceConstraint(delayed_choices))

    def get_empty_sentinel_name(self, base_name):
        return '%s-' % base_name

    def update_valid_value_in_disambiguated_input(self, input_dict):
        try:
            del input_dict[self.get_empty_sentinel_name(self.name_in_input)]
        except KeyError:
            pass

        try:
            del input_dict[self.name_in_input]
        except KeyError:
            pass

        list_value = self.as_list_unaware_user_input_value(for_input_status='defaulted')
        if list_value == []:
            input_dict[self.get_empty_sentinel_name(self.name_in_input)] = ''
        elif list_value:
            input_dict[self.name_in_input] = list_value

    def extract_unparsed_input_from_dict_of_lists(self, input_dict):
        submitted_as_empty = len(input_dict.get(self.get_empty_sentinel_name(self.name_in_input), [])) > 0
        if submitted_as_empty:
            return []
        else:
            list_value = input_dict.get(self.name_in_input, [])
            if not list_value:
                return None
            else:
                return list_value

    def input_as_string(self, unparsed_input):
        return ','.join(unparsed_input)

    def parse_input(self, unparsed_inputs):
        selected = []
        for choice in self.flattened_choices:
            for unparsed_input in unparsed_inputs:
                if choice.matches_input(unparsed_input):
                    selected.append(choice.value)
        return selected

    def unparse_input(self, parsed_values):
        inputs = []
        if parsed_values:
            for choice in self.flattened_choices:
                for value in parsed_values:
                    if choice.value == value:
                        inputs.append(choice.as_input())
        return inputs


class SingleFileConstraint(ValidationConstraint):
    def __init__(self, error_message=None):
        error_message = error_message or _('$label can only accept a single file')
        super().__init__(error_message=error_message)

    def validate_input(self, unparsed_input):
        if not len(unparsed_input) <= 1:
            raise self


class UploadedFile:
    """Represents a file that was input by a user. The contents of the file
    is represented as bytes, because knowing what the encoding is is a tricky
    issue. The user only sits in front of the browser and selects files on their
    filesystem and hits 'upload'. Those files can be binary or text. If text,
    they may or may not be in the same encoding as their system's preferred
    encoding. If binary, their browser may guess their content type correctly
    or may not, and if we go and decode them with i.e UTF-8, the system could
    break with UnicodeDecodeError on jpegs and the like.

    .. versionchanged:: 3.0
       UploadedFile is now constructed with the entire contents of the uploaded file instead of with a file-like object as in 2.1.

    """
    def __init__(self, filename, contents, mime_type):
        assert isinstance(contents, bytes)
        self.contents = contents
        self.filename = filename  #: The name of the file
        self.mime_type = mime_type #: The mime type of the file


    @property
    def size(self):
        """The size of the UploadedFile contents."""
        return len(self.contents)

    @contextmanager
    def open(self):
        """A contextmanager for reading the file contents (as bytes).

        For example:

        .. code-block:: python

           with uploaded_file.open() as contents:
               print(contents.read())
        """
        # Scaffolding to maintain the old API when contents was a file-like object
        with io.BytesIO(self.contents) as f:
            yield f


class FileSizeConstraint(ValidationConstraint):
    name = 'filesize'
    def __init__(self, max_size_bytes, error_message=None):
        error_message = error_message or _('files should be smaller than $human_max_size')
        super().__init__(error_message)
        self.max_size_bytes = max_size_bytes
    
    def __reduce__(self):
        reduced = super().__reduce__()
        return (reduced[0], (self.max_size_bytes,))+reduced[2:]

    @property
    def human_max_size(self):
        num = self.max_size_bytes
        for x in ['bytes','KB','MB','GB']:
            if num < 1000.0 and num > -1000.0:
                return "%3.1f%s" % (num, x)
            num /= 1000.0
        return '%3.1f%s' % (num, 'TB')

    @property
    def parameters(self):
        return str(self.max_size_bytes)

    def validate_input(self, unparsed_input):
        files_list = unparsed_input
        for f in files_list:
            if f.size > self.max_size_bytes:
                raise self


class MimeTypeConstraint(ValidationConstraint):
    name = 'accept'
    def __init__(self, accept, error_message=None):
        error_message = error_message or _('files should be of type $human_accepted_types')
        super().__init__(error_message)
        self.accept = accept
    
    def __reduce__(self):
        reduced = super().__reduce__()
        return (reduced[0], (self.accept,))+reduced[2:]

    @property
    def human_accepted_types(self):
        return '|'.join(self.accept)

    @property
    def parameters(self):
        return ','.join(self.accept)

    def validate_input(self, unparsed_input):
        def matches(actual_type, accepted_types):
            for accepted_type in accepted_types:
                if re.match(fnmatch.translate(accepted_type), actual_type):
                    return True
            return False

        files_list = unparsed_input
        for f in files_list:
            if not matches(f.mime_type, self.accept):
                raise self


class MaxFilesConstraint(ValidationConstraint):
    name = 'maxfiles'
    def __init__(self, max_files, error_message=None):
        error_message = error_message or _('a maximum of $max_files files may be uploaded')
        super().__init__(error_message)
        self.max_files = max_files
    
    def __reduce__(self):
        reduced = super().__reduce__()
        return (reduced[0], (self.max_files,))+reduced[2:]

    @property
    def parameters(self):
        return str(self.max_files)

    def validate_input(self, unparsed_input):
        files_list = unparsed_input

        if len(files_list) > self.max_files:
            raise self


class FileField(Field):
    """A Field that can accept one or more files as input.

       :param allow_multiple: Set to True to allow more than one file to be input at a time.
       :param max_size_bytes: The maximim size of file allowed, in bytes.
       :param accept: The accepted type of file, as specified via mime type.
       :param max_files: Specifies the maximum number of files the user is allowed to input.
                               
       (For other arguments, see :class:`Field`.)
    """
    def __init__(self, allow_multiple=False, default=None, required=False, required_message=None, label=None, readable=None, writable=None, max_size_bytes=None, accept=None, max_files=None):
        super().__init__(default=default, required=required, required_message=required_message, label=label, readable=readable, writable=writable)
        self.allow_multiple = allow_multiple
        if not allow_multiple:
            self.disallow_multiple()
        if max_size_bytes:
            self.add_validation_constraint(FileSizeConstraint(max_size_bytes))
        if accept:
            self.add_validation_constraint(MimeTypeConstraint(accept))
        if max_files:
            self.add_validation_constraint(MaxFilesConstraint(max_files))

    def disallow_multiple(self):
        self.allow_multiple = False
        self.add_validation_constraint(SingleFileConstraint())

    def parse_input(self, unparsed_value):
        files_list = unparsed_value
        files = files_list
        if self.allow_multiple:
            return files
        else:
            return files[0] if files else None

    def unparse_input(self, parsed_value):
        return ''




