# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import unicode_literals
from __future__ import print_function
import six
import copy
import re
import fnmatch
import json
import sre_constants
from six.moves.urllib import parse as urllib_parse
from string import Template
import types
import inspect
from contextlib import contextmanager
import functools

import dateutil.parser 
import babel.dates 


from reahl.component.i18n import Translator
from reahl.component.decorators import memoized
from reahl.component.context import ExecutionContext
from reahl.component.exceptions import AccessRestricted, ProgrammerError, arg_checks, IsInstance, IsCallable, NotYetAvailable
import collections

_ = Translator('reahl-component')

class ConstraintNotFound(Exception):
    pass

class ObjectDictAdapter(object):
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
            super(ObjectDictAdapter, self).__setattr__(name, value)


class FieldIndex(object):
    """Used to define a set of :class:`Field` instances applicable to an object. In order to declare a
       :class:`Field`, merely assign an instance of :class:`Field` to an attribute of the FieldIndex.
    
       Programmers should not construct this class, a prepared instance of it will be passed to methods
       marked as @exposed. (See :class:`ExposedDecorator` )
    """
    def __init__(self, storage_object):
        super(FieldIndex, self).__init__()
        self.fields = {}
        self.storage_object = storage_object

    def __setattr__(self, name, value):
        if isinstance(value, Field):
            self.fields[name] = value
            if not value.is_bound:
                value.bind(six.text_type(name), self.storage_object)
        super(FieldIndex, self).__setattr__(name, value)

    def set(self, name, value):
        return setattr(self, name, value)

    def keys(self):
        return self.fields.keys()

    def items(self):
        return self.fields.items()

    def add_bound_field(self, field):
        setattr(self, field.name, field)

    def as_kwargs(self):
        return dict([(name, field.get_model_value()) for name, field in self.items()])

    def as_input_kwargs(self):
        return dict([(name, field.as_input()) for name, field in self.items()])

    def accept_input(self, input_dict):
        for name, field in self.items():
            field.from_input(input_dict.get(field.name, field.as_input()))

    def update(self, other):
        for name, value in other.items():
            setattr(self, name, value)

    def update_copies(self, other):
        for name, value in other.items():
            setattr(self, name, value.copy())

    def update_from_class(self, cls):
        items = cls.__dict__.items()
        for name, value in items:
            if isinstance(value, Field):
                setattr(self, name, value.copy())

    @property
    def is_empty(self):
        return self.fields == {}


class StandaloneFieldIndex(FieldIndex):
    def __init__(self, backing_dict=None):
        backing_dict = backing_dict or {}
        super(StandaloneFieldIndex, self).__init__(ObjectDictAdapter(backing_dict))

    @property
    def backing_dict(self):
        return self.storage_object.wrapped_dict
    
    def accept_parsed(self, value_dict):
        self.backing_dict.update(value_dict)

    def validate_defaults(self):
        for field in self.fields.values():
            field.validate_default()

import functools
class ExposedDecorator(object):
    """This class has the alias "exposed". Apply it as decorator to a method declaration to indicate that the method defines
       a number of Fields. The decorated method is passed an instance of :class:`FieldIndex` to which each Field should be assigned. 
       Each such Field is associated with an similarly named attribute on each instance of the current class.

       :param args: A list of names of Fields that will be defined by this method. This is used when accessing the
                    resultant FieldIndex on a class, instead of on an instance.
    """
    def __init__(self, *args):
        self.property = None
        self.expected_event_names = []
        if isinstance(args[0], six.string_types):
            self.add_fake_events(args)
        else:
            self.set_property(args[0])

    def add_fake_events(self, event_names):
        self.expected_event_names.extend(event_names)
        for name in event_names:
            setattr(self, name, FakeEvent(name))

    def __call__(self, func):
        self.set_property(func)
        return self

    def set_property(self, func):
        exposed_decorator = self
        @functools.wraps(func)
        def call_with_field_index(model_object):
            # Note: This function effectively becomes a method on the class where the exposed decorator is used
            #       Then it is wrapped as per exposed implementation below
            fields = FieldIndex(model_object)
            func(model_object, fields)
            if exposed_decorator.expected_event_names:
                declared_fields = set(fields.keys())
                expected_fields = set(exposed_decorator.expected_event_names)
                missing_fields = expected_fields - declared_fields
                if missing_fields:
                    raise ProgrammerError('You promised to instantiate "%s" in %s of %s but did not do so' % \
                                              (','.join(missing_fields), func, model_object))
            return fields
        self.property = property(memoized(call_with_field_index))
        
    def __get__(self, instance, owner):
        if not instance:
            return self
        return self.property.__get__(instance, owner)

    def __set__(self, instance, owner, value):
        return self.property.__set__(instance, owner, value)
        
    def __getattr__(self, name):
        raise AttributeError('%s has no attribute \'%s\' - did you perhaps write @exposed instead of @exposed(\'%s\')?' % \
                            (self, name, name))


exposed = ExposedDecorator

class FakeEvent(object):
    isEvent = True
    def __init__(self, name):
        self.name = name
        

class ReahlFields(object):
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
        for class_ in reversed(cls.mro()):
            if hasattr(class_, my_name):
                idx.update_from_class(getattr(class_, my_name))
        setattr(instance, my_name, idx)
        return idx


class ReadRights(object):
    def __init__(self, access_rights, field):
        self.field = field
        self.access_rights = access_rights

    def __call__(self):
        return self.access_rights.can_read(self.field)

    @property
    def is_specified(self):
        return self.access_rights.readable is not None


class AccessRights(object):
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
       
       :param error_message: The error message shat should be shown to a user if input failed this ValidationConstraint.
                             This error_message is a string containing a `PEP-292 <http://www.python.org/dev/peps/pep-0292/>`_
                             template. Attributes of the ValidationConstraint can be referred to by name in variable 
                             references of this template string.
    """
    is_remote = False
    name = '' #: A unique name for this type of constraint. Only one Constraint with a given name is allowed per Field.
    def __init__(self, error_message=None):
        error_message = error_message or _('$label is invalid')
        Exception.__init__(self)
        self.error_message = Template(error_message)
        self.field = None
    
    def __reduce__(self):
        reduced = super(ValidationConstraint, self).__reduce__()
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
        return self.field.label

    @property
    def value(self):
        """The current value which failed validation."""
        return self.field.user_input

    def __str__(self):
        return self.message



class RemoteConstraint(ValidationConstraint):
    """A ValidationConstraint which can only be executed on the server. Create a subclass of this class 
       and override `validate_input` and `validate_parsed_value`.
    
       :param error_message: (See :class:`ValidationConstraint`)
    """
    is_remote = True
    name = 'remote'
    def __init__(self, error_message=None):
        error_message = error_message or _('$label is not valid')
        super(RemoteConstraint, self).__init__(error_message)


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
        super(ValidationConstraintList, self).append(constraint)

    def has_constraint_named(self, name):
        return name in [validation_constraint.name for validation_constraint in self]

    def get_constraint_of_class(self, cls):
        for validation_constraint in self:
            if isinstance(validation_constraint, cls):
                return validation_constraint
        raise ConstraintNotFound(name)

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

    def js_escape(self, message):
        return message.replace('\'', '\\\'')
        
    def as_json_messages(self, map_name_function, ignore_names):
        messages_dict = dict([(map_name_function(validation_constraint.name), self.js_escape(validation_constraint.message))
                              for validation_constraint in self
                              if (not validation_constraint.name in ignore_names) ])
        if messages_dict:
            return json.dumps({'validate':{'messages':messages_dict}})
        return ''


class RequiredConstraint(ValidationConstraint):
    """The presence of this ValidationConstraint on a Field indicates that the Field is required.
    
       :param error_message: (See :class:`ValidationConstraint`)
    """
    name = 'required'
    empty_regex = re.compile('^ +$')
    def __init__(self, selector_expression='*', error_message=None):
        error_message = error_message or _('$label is required')
        super(RequiredConstraint, self).__init__(error_message)
        self.selector_expression = selector_expression

    @property
    def parameters(self):
        return self.selector_expression

    def validate_input(self, unparsed_input):
        if isinstance(unparsed_input, six.string_types) and self.empty_regex.match(unparsed_input):
            raise self
        if not unparsed_input:
            raise self


class Comparison(object):
    def __init__(self, compare_function, error_message):
        self.compare_function = compare_function
        self.error_message = error_message
    
    def compare(self, one, other):
        return self.compare_function(one, other)


class ComparingConstraint(ValidationConstraint):
    def __init__(self, other_field, comparison):
        error_message = comparison.error_message 
        super(ComparingConstraint, self).__init__(error_message)
        self.other_field = other_field
        self.comparison = comparison

    @property
    def other_label(self):
        return self.other_field.label
    
    @property
    def parameters(self):
        return self.other_field.variable_name

    def validate_parsed_value(self, parsed_value):
        if not self.comparison.compare(parsed_value, self.other_field.parsed_input):
            raise self


class EqualToConstraint(ComparingConstraint):
    """A ValidationConstraint that requires the value of its Field to be equal to the value input into `other_field`.
    
       :param other_field: The Field whose value must be equal to the Field to which this ValidationConstraint is attached.
       :param error_message: (See :class:`ValidationConstraint`)
    """
    name = 'equalTo2'
    def __init__(self, other_field, error_message=None):
        def equal_to(one, other): return one == other
        equals = Comparison(equal_to, error_message or _('$label should be equal to $other_label'))
        super(EqualToConstraint, self).__init__(other_field, equals)
        

class GreaterThanConstraint(ComparingConstraint):
    """A ValidationConstraint that requires the value of its Field to be greater than the value input into 
      `other_field` (the > operator is used for the comparison).
    
       :param other_field: The Field whose value is compared.
       :param error_message: (See :class:`ValidationConstraint`)
    """
    name = 'greaterThan'

    def __init__(self, other_field, error_message=None):
        def greater_than(one, other): return one > other
        greater = Comparison(greater_than, error_message or _('$label should be greater than $other_label'))
        super(GreaterThanConstraint, self).__init__(other_field, greater)


class SmallerThanConstraint(ComparingConstraint):
    """A ValidationConstraint that requires the value of its Field to be smaller than the value input into 
      `other_field` (the < operator is used for the comparison).
    
       :param other_field: The Field whose value is compared.
       :param error_message: (See :class:`ValidationConstraint`)
    """
    name = 'smallerThan'

    def __init__(self, other_field, error_message=None):
        def smaller_than(one, other): return one < other
        smaller = Comparison(smaller_than, error_message or _('$label should be smaller than $other_label'))
        super(SmallerThanConstraint, self).__init__(other_field, smaller)


class MinLengthConstraint(ValidationConstraint):
    """A ValidationConstraint that requires length of what the user typed to be at least `min_length`
       characters long.
       
       :param min_length: The minimum allowed length of the input.
       :param error_message: (See :class:`ValidationConstraint`)
    """
    name = 'minlength'
    def __init__(self, min_length, error_message=None):
        error_message = error_message or _('$label should be $min_length characters or longer')
        super(MinLengthConstraint, self).__init__(error_message)
        self.min_length = min_length
    
    @property
    def parameters(self):
        return six.text_type(self.min_length)

    def validate_input(self, unparsed_input):
        if len(unparsed_input) <  self.min_length:
            raise self


class MaxLengthConstraint(ValidationConstraint):
    """A ValidationConstraint that requires length of what the user typed to not be more than `max_length`
       characters long.
       
       :param max_length: The maximum allowed length of the input.
       :param error_message: (See :class:`ValidationConstraint`)
    """
    name = 'maxlength'
    def __init__(self, max_length, error_message=None):
        error_message = error_message or _('$label should not be longer than $max_length characters')
        super(MaxLengthConstraint, self).__init__(error_message)
        self.max_length = max_length

    @property
    def parameters(self):
        return six.text_type(self.max_length)

    def validate_input(self, unparsed_input):
        if len(unparsed_input) > self.max_length:
            raise self


class PatternConstraint(ValidationConstraint):
    """A ValidationConstraint that requires unparsed input to match the supplied regex.
       
       :param pattern: The regex to match input against.
       :param error_message: (See :class:`ValidationConstraint`)
    """
    name = 'pattern'
    def __init__(self, pattern, error_message=None):
        error_message = error_message or _('$label is invalid')
        super(PatternConstraint, self).__init__(error_message)
        self.pattern = pattern

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
       :param error_message: (See :class:`ValidationConstraint`)
    """
    def new_for_copy(self):
        return self.__class__(self.allowed_values, error_message=self.error_message)

    def __init__(self, allowed_values, error_message=None):
        error_message = error_message or _('$label should be one of the following: $allowed')
        self.allowed_values = allowed_values
        allowed_regex = '(%s)' % ('|'.join(self.allowed_values))
        super(AllowedValuesConstraint, self).__init__(allowed_regex, error_message)
        
    @property
    def allowed(self):
        return '|'.join(self.allowed_values)


class IntegerConstraint(PatternConstraint):
    """A PatternConstraint that only allows input that represent a valid integer.
       
       :param error_message: (See :class:`ValidationConstraint`)
    """
    def __init__(self, error_message=None):
        error_message = error_message or _('$label should be an integer number')
        super(IntegerConstraint, self).__init__('[-0123456789]+', error_message)

    def validate_input(self, unparsed_input):
        super(IntegerConstraint, self).validate_input(unparsed_input)
        # (for good measure we do not rely on the regex alone)
        try:
            int(unparsed_input)
        except ValueError:
            raise self


class MinValueConstraint(ValidationConstraint):
    """A ValidationConstraint that requires its parsed input to be greater than or equal to a supplied `min_value`.
       (To do the comparison, the >= operator is used on the parsed value.)
       
       :param min_value: The minimum value allowed.
       :param error_message: (See :class:`ValidationConstraint`)
    """
    name = 'minvalue'
    def __init__(self, min_value, error_message=None):
        error_message = error_message or _('$label should be $min_value or greater')
        super(MinValueConstraint, self).__init__(error_message=error_message)
        self.min_value = min_value

    def validate_parsed_value(self, parsed_value):
        if not (parsed_value >= self.min_value):
            raise self


class MaxValueConstraint(ValidationConstraint):
    """A ValidationConstraint that requires its parsed input to be smaller than or equal to a supplied `max_value`.
       (To do the comparison, the <= operator is used on the parsed value.)
       
       :param max_value: The maximum value allowed.
       :param error_message: (See :class:`ValidationConstraint`)
    """
    name = 'maxvalue'
    def __init__(self, max_value, error_message=None):
        error_message = error_message or _('$label should be no greater than $max_value')
        super(MaxValueConstraint, self).__init__(error_message=error_message)
        self.max_value = max_value

    def validate_parsed_value(self, parsed_value):
        if not (parsed_value <= self.max_value):
            raise self


class InputParseException(Exception):
    pass

       
class Field(object):
    """A Field represents something which can be input by a User.
    
       A Field is responsible for transforming user input from a string into a Python object which that string 
       represents. Different kinds of Fields marshall input to different kinds of Python object. This (base) class 
       does no marshalling itself, the parsed Python object is just the input string as given. Subclasses override 
       this behaviour.
       
       A Field also manages the validation of such input, based on a list of individual instances 
       of :class:`ValidationConstraint` added to the Field.
       
       The final parsed value of a Field is set as an attribute on a Python object to which the Field is bound.

       :param default: The default (parsed) value if no user input is given.
       :param required: If True, indicates that input is always required for this Field.
       :param required_message: See `error_message` of :class:`RequiredConstraint`.
       :param label: A text label by which to identify this Field to a user.
       :param readable: A callable that takes one argument (this Field). It is executed to determine whether
                        the current user is allowed to see this Field. Returns True is the user is allowed, 
                        else False.
       :param writable: A callable that takes one argument (this Field). It is executed to determine whether
                        the current user is allowed supply input for this Field. Returns True is the user is 
                        allowed, else False.
       :param disallowed_message: An error message to be displayed when a user attempts to supply input
                        to this Field when it is not writable for that user. (See `error_message` of
                        :class:`ValidationConstraint`.)
    """
    @arg_checks(readable=IsCallable(allow_none=True, args=(NotYetAvailable('field'),)), writable=IsCallable(allow_none=True, args=(NotYetAvailable('field'),)))
    def __init__(self, default=None, required=False, required_message=None, label=None, readable=None, writable=None, disallowed_message=None):
        self.name = None
        self.storage_object = None
        self.default = default
        self.label = label or ''
        self.validation_constraints = ValidationConstraintList()
        self.add_validation_constraint(AccessRightsConstraint(disallowed_message or _('Not allowed')))
        self.access_rights = AccessRights(readable=readable, writable=writable)
        if required:
            self.make_required(required_message)
        self.clear_user_input()

    def validate_default(self):
        unparsed_input = self.as_input()
        self.validate_input(unparsed_input, ignore=AccessRightsConstraint)
        self.validate_parsed(self.parse_input(unparsed_input), ignore=AccessRightsConstraint)

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
        return new_version

    def unbound_copy(self):
        new_version = self.copy()
        new_version.unbind()
        return new_version

    def as_without_validation_constraint(self, validation_constraint_class):
        """Returns a new Field which is exactly like this one, except that the new Field does not include 
           a ValidationConstraint of the class given as `validation_constraint_class`."""
        new_version = self.copy()
        new_version.remove_validation_constraint(validation_constraint_class)
        return new_version
        
    def as_with_validation_constraint(self, validation_constraint):
        """Returns a new Field which is exactly like this one, except that the new Field also includes 
           the ValidationConstraint given as `validation_constraint`."""
        new_version = self.copy()
        new_version.add_validation_constraint(validation_constraint)
        return new_version

    def clear_user_input(self):
        self.input_status = 'defaulted'
        self.validation_error = None
        self.user_input = None
        self.parsed_input = self.default
    
    def set_user_input(self, input_value, ignore_validation=False):
        self.clear_user_input()

        self.user_input = input_value

        if not self.required and input_value == '':
            self.input_status = 'validly_entered'
        else:
            try:
                self.input_status = 'invalidly_entered'
                self.validate_input(input_value)
                self.parsed_input = self.parse_input(input_value)
                self.validate_parsed(self.parsed_input)
                self.input_status = 'validly_entered'
            except ValidationConstraint as ex:
                self.validation_error = ex
                if not ignore_validation:
                    raise

    def bind(self, name, storage_object):
        self.name = name
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
    def variable_name(self):
        if not self.name:
            raise AssertionError('field %s with label "%s" is not yet bound' % (self, self.label))
        return self.name
        
    def get_model_value(self):
        return getattr(self.storage_object, self.variable_name, self.default)
        
    def set_model_value(self):
        setattr(self.storage_object, self.variable_name, self.parsed_input)

    def validate_input(self, unparsed_input, ignore=None):
        self.validation_constraints.validate_input(unparsed_input, ignore=ignore)

    def format_input(self, unparsed_input):
        return self.unparse_input(self.parse_input(unparsed_input))
    
    def validate_parsed(self, parsed_value, ignore=None):
        self.validation_constraints.validate_parsed(parsed_value, ignore=ignore)
        
    def parse_input(self, unparsed_input):
        """Override this method on a subclass to specify how that subclass transforms the `unparsed_input`
           (a string) into a representative Python object."""
        return unparsed_input

    def unparse_input(self, parsed_value):
        """Override this method on a subclass to specify how that subclass transforms a given Python
           object (`parsed_value`) to a string that represents it to a user."""
        return six.text_type(parsed_value if parsed_value is not None else '')

    def from_input(self, unparsed_input):
        """Sets the value of this Field from the given `unparsed_input`."""
        if self.can_write():
            self.set_user_input(unparsed_input)
            self.set_model_value()
        
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


class AdaptedMethod(object):
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
       :param kwarg_name_map: A dictionary specifying which keyword arguments to send to `declared_method` when called.
                         The dictionary maps each name of an Event argument that needs to be sent 
                         to the name of the keyword argument as which it should be sent.
    """
    def __call__(self, field):
        event = field
        event_arguments = event.get_model_value()
        args = [event_arguments[name] for name in self.arg_names]
        kwargs = dict([(name, event_arguments[name])
                       for name in self.kwarg_name_map_reversed.keys()])
        return super(Action, self).__call__(*args, **kwargs)


    @property
    def readable(self):
        if isinstance(self.declared_method, SecuredMethod):
            return Action(self.declared_method.read_check, arg_names=self.arg_names, kwarg_name_map=self.kwarg_name_map)
        return None
    @property
    def writable(self):
        if isinstance(self.declared_method, SecuredMethod):
            return Action(self.declared_method.write_check, arg_names=self.arg_names, kwarg_name_map=self.kwarg_name_map)
        return None


class Allowed(Action):
    """An Action that always returns the (boolean) value of `allowed` with which it was constructed."""
    def __init__(self, allowed):
        super(Allowed, self).__init__(self.is_allowed)
        self.allowed = allowed

    def is_allowed(self):
        return self.allowed


class Not(Action):
    """An Action which returns the boolean inverse of the result of another `action`."""
    def __init__(self, action):
        super(Not, self).__init__(action.declared_method, arg_names=action.arg_names, kwarg_name_map=action.kwarg_name_map)
    def __call__(self, field):
        return not super(Not, self).__call__(field)


class Event(Field):
    """An Event can be triggered by a user. When an Event occurs, the `action` of the Event is executed.
       

       :param label: (See :class:`Field`)
       :param action: The :class:`Action` to execute when this Event occurs.
       :param readable: (See :class:`Field`)
       :param writable: (See :class:`Field`)
       :param disallowed_message: (See :class:`Field`)
       :param event_argument_fields: Keyword arguments given in order to specify the names of the arguments 
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

        super(Event, self).__init__(required=False, required_message=None, label=label, readable=readable, writable=writable, disallowed_message=disallowed_message)
        self.action = action or (lambda *args, **kwargs: None)
        self.event_argument_fields = event_argument_fields

    def __str__(self):
        argument_string = (', %s' % six.text_type(self.arguments)) if hasattr(self, 'arguments') else ''
        return 'Event(%s%s)' % (self.name, argument_string)

    def from_input(self, unparsed_input):
        # Note: this needs to happen for Events whether you are allowed to write the Event or not,
        #       because during validation, an AccessRightsConstraint is raised
        #       (In the case of other Fields, input to non-writable Fields is silently ignored)
        self.set_user_input(unparsed_input)
        self.set_model_value()

    @property
    def occurred(self):
        if self.user_input:
            return self.user_input.startswith('?') and self.can_write()
        return False

    def can_write(self):
        return self.can_read() and super(Event, self).can_write()

    def fire(self):
        if not self.occurred:
            raise ProgrammerError('attempted to fire Event that has not occurred: %s' % self)
        return self.action(self)

    def bind(self, name, storage_object):
        super(Event, self).bind(name, self)

    def copy(self):
        new_field = super(Event, self).copy()
        new_field.bind(new_field.name, new_field)
        return new_field
    
    def with_arguments(self, **event_arguments):
        """Returns a new Event exactly like this one, but with argument values as given."""
        arguments = event_arguments.copy()
        for declared_argument_name, argument_field in self.event_argument_fields.items():
            if declared_argument_name not in event_arguments:
                arguments[declared_argument_name] = argument_field.default

        new_field = self.copy()
        new_field.default = arguments
        return new_field

    @property
    def variable_name(self):
        return 'arguments'
   
    def parse_input(self, unparsed_input):
        if unparsed_input:
            arguments_query_string = unparsed_input[1:]
            raw_input_values = dict([(k,v[0]) for k, v in urllib_parse.parse_qs(arguments_query_string).items()])
            fields = StandaloneFieldIndex()
            fields.update_copies(self.event_argument_fields)
            fields.accept_input(raw_input_values)
            
            arguments = raw_input_values.copy()
            arguments.update(fields.as_kwargs())
            return arguments
        return None

    def unparse_input(self, parsed_value):
        if parsed_value:
            arguments = parsed_value.copy()
            fields = StandaloneFieldIndex(arguments)
            fields.update_copies(self.event_argument_fields)
            
            arguments.update(fields.as_input_kwargs())
            input_string='?%s' % urllib_parse.urlencode(arguments)
            return six.text_type(input_string)
        else:
            return '?'
    
    
class SecuredMethod(object):
    def __init__(self, to_be_called, secured_declaration):
        self.to_be_called = to_be_called
        self.secured_declaration = secured_declaration

    def __call__(self, *args, **kwargs):
        if not (self.read_check(*args, **kwargs) and self.write_check(*args, **kwargs)):
            raise AccessRestricted()
        return self.to_be_called(*args, **kwargs)

    def check_right(self, right_to_check, called_self, *args, **kwargs):
        args_to_send = args
        if called_self:
            args_to_send = [called_self]+list(args)
        if right_to_check:
            return right_to_check(*args_to_send, **kwargs)
        else:
            return True

    def read_check(self, *args, **kwargs):
        return self.check_right(self.secured_declaration.read_check, six.get_method_self(self.to_be_called), *args, **kwargs)
    
    def write_check(self, *args, **kwargs):
        return self.check_right(self.secured_declaration.write_check, six.get_method_self(self.to_be_called), *args, **kwargs)



class SecuredDeclaration(object):
    """A decorator for marking a method as being @secured. Marking a method as @secured, causes a wrapper
       to be placed around the original method. The wrapper checks the access rights of the current user
       before each call to the method to ensure unauthorised users cannot call the wrapped method.
       
       When such a @secured method is used as the `declared_method` of an :class:`Action`, the :class:`Action`
       derives its access constraints directly from the @secured method.
       
       :param read_check: A callable with signature matching that of the @secured method. It should
                          return True to indicate that the current user may be aware of the method, else False.
                          User interface machinery could use this info to determine what to show to a user,
                          what to grey out, or what to hide completely, depending on who the current user is.
       
       :param write_check: A callable with signature matching that of the @secured method. It should
                           return True to indicate that the current user may execute the method, else False.
       
    """
    def __init__(self, read_check=None, write_check=None):
        self.read_check = read_check
        self.write_check = write_check
        self.func = None

    def __call__(self, func):
        self.func = func
        arg_names = self.get_declared_argument_names(self.func)
        
        if isinstance(self.read_check, AdaptedMethod):
            self.read_check.set_full_arg_names(arg_names)
        elif isinstance(self.read_check, collections.Callable):
            self.check_method_signature(self.read_check, self.func)
        
        if isinstance(self.write_check, AdaptedMethod):
            self.write_check.set_full_arg_names(arg_names)
        elif isinstance(self.write_check, collections.Callable):
            self.check_method_signature(self.write_check, self.func)
        return self

    def check_method_signature(self, check_method, original_method):
        check_signature = inspect.getargspec(check_method)
        expected_signature = inspect.getargspec(original_method)
        if check_signature != expected_signature:
            messages = [repr(method) + inspect.formatargspec(*signature)
                        for signature, method in [(check_signature, check_method),
                                                  (expected_signature, original_method)]]
            raise ProgrammerError('signature of %s does not match expected signature of %s' % \
                                  tuple(messages))

    def get_declared_argument_names(self, func):
        arg_spec = inspect.getargspec(func)
        positional_args_end = len(arg_spec.args)-len(arg_spec.defaults or [])
        return arg_spec.args[:positional_args_end]

    def __get__(self, instance, owner):
        method = types.MethodType(self.func, instance, owner)
        return SecuredMethod(method, self)


secured = SecuredDeclaration #: An alias for :class:`SecuredDeclaration`


class CurrentUser(Field):
    """A Field whose value is always set to the party of the account currently logged in."""
    def __init__(self):
        account = ExecutionContext.get_context().session.account
        if account:
            party = account.party
        else:
            party = None
        super(CurrentUser, self).__init__(required=True, default=party)
        self.bind('current_account', self)
        
    def parse_input(self, unparsed_input):
        return self.default

    def unparse_input(self, parsed_value):
        return 'The current account'


class EmailField(Field):
    """A Field representing a valid email address. Its parsed value is the given string."""
    def __init__(self, default=None, required=False, required_message=None, label=None, readable=None, writable=None):
        label = label or ''
        super(EmailField, self).__init__(default, required, required_message, label, readable=readable, writable=writable)
        error_message=_('$label should be a valid email address')
        self.add_validation_constraint(PatternConstraint('[^\s]+@[^\s]+\.[^\s]{2,4}', error_message))


class PasswordField(Field):
    """A Field representing a password. Its parsed value is the given string, but the user is not
       allowed to see its current value."""
    def __init__(self, default=None, required=False, required_message=None, label=None, writable=None):
        label = label or ''
        super(PasswordField, self).__init__(default, required, required_message, label, readable=Allowed(False), writable=writable)
        self.add_validation_constraint(MinLengthConstraint(6))
        self.add_validation_constraint(MaxLengthConstraint(20))


class BooleanField(Field):
    """A Field that can only have one of two parsed values: True or False. The string representation of
       each of these values are given in `true_value` or `false_value`, respectively.  (These default
       to 'on' and 'off' initially.)
    """
    def __init__(self, default=None, required=False, required_message=None, label=None, readable=None, writable=None, true_value=None, false_value=None):
        true_value = true_value or _('on')
        false_value = false_value or _('off')
        label = label or ''
        super(BooleanField, self).__init__(default, required, required_message, label, readable=readable, writable=writable)
        self.true_value = true_value
        self.false_value = false_value
        allowed_values = [self.true_value]
        if required:
            error_message = required_message or _('$label is required')
        else:
            error_message = _('$label should be either "%s" or "%s"') % (self.true_value, self.false_value)
            allowed_values.append(self.false_value)
        self.add_validation_constraint(AllowedValuesConstraint(allowed_values, error_message=error_message))

    def parse_input(self, unparsed_input):
        value = True if unparsed_input == self.true_value else False
        return value
        
    def unparse_input(self, parsed_value):
        if parsed_value:
            return self.true_value
        return self.false_value 


class IntegerField(Field):
    """A Field that yields an integer.
    
       :param min_value: The minimum value allowed as valid input.
       :param max_value: The maximum value allowed as valid input.
       
       (For other arguments, see :class:`Field`.)
    """
    def __init__(self, default=None, required=False, required_message=None, label=None, readable=None, writable=None, min_value=None, max_value=None):
        label = label or ''
        super(IntegerField, self).__init__(default, required, required_message, label, readable=readable, writable=writable)
        self.add_validation_constraint(IntegerConstraint())
        if min_value:
            self.add_validation_constraint(MinValueConstraint(min_value))
        if max_value:
            self.add_validation_constraint(MaxValueConstraint(max_value))

    def parse_input(self, unparsed_input):
        return int(unparsed_input)


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

       :param min_value: The earliest value allowed as valid input.
       :param max_value: The latest value allowed as valid input.
       
       (For other arguments, see :class:`Field`.)
    """
    def __init__(self, default=None, required=False, required_message=None, label=None, readable=None, writable=None, min_value=None, max_value=None):
        label = label or ''
        super(DateField, self).__init__(default, required, required_message, label, readable=readable, writable=writable)
        self.add_validation_constraint(DateConstraint())
        if min_value:
            self.add_validation_constraint(MinValueConstraint(min_value))
        if max_value:
            self.add_validation_constraint(MaxValueConstraint(max_value))

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
            return dateutil.parser.parse(unparsed_input, dayfirst=True, parserinfo=self.parser_info).date()
        except ValueError:
            raise InputParseException()

    def unparse_input(self, parsed_value):
        return babel.dates.format_date(parsed_value, format='medium', locale=_.current_locale)


class Choice(object):
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
    def label(self):
        return self.field.label

    @property
    def choices(self):
        return [self]

    @property
    def groups(self):
        return []


class ChoiceGroup(object):
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
        super(MultiChoiceConstraint, self).__init__(error_message=error_message)
        self.choices = choices

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
    
       :param grouped_choices: A list of :class:`Choice` or :class:`ChoiceGroup` instances from which
                               a user should choose a single :class:`Choice`.
                               
       (For other arguments, see :class:`Field`.)
    """
    allows_multiple_selections = False
    def __init__(self, grouped_choices, default=None, required=False, required_message=None, label=None, readable=None, writable=None):
        super(ChoiceField, self).__init__(default, required, required_message, label, readable=readable, writable=writable)
        self.grouped_choices = grouped_choices
        self.init_validation_constraints()

    def is_selected(self, choice):
        return self.get_model_value() == choice.value
        
    def init_validation_constraints(self):
        allowed_values = [choice.as_input() for choice in self.flattened_choices]
        self.add_validation_constraint(AllowedValuesConstraint(allowed_values))

    @property
    def flattened_choices(self):
        flattened = []
        for item in self.grouped_choices:
            flattened.extend(item.choices)
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


class MultiChoiceField(ChoiceField):
    """A Field that allows a selection of values from the given :class:`Choice` instances as input."""
    allows_multiple_selections = True
    def init_validation_constraints(self):
        self.add_validation_constraint(MultiChoiceConstraint(self.flattened_choices))

    def is_selected(self, choice):
        return self.get_model_value() and (choice.value in self.get_model_value())

    def parse_input(self, unparsed_inputs):
        selected = []
        for choice in self.flattened_choices:
            for unparsed_input in unparsed_inputs:
                if choice.matches_input(unparsed_input):
                    selected.append(choice.value)
        return selected

    def unparse_input(self, parsed_values):
        inputs = []
        for choice in self.flattened_choices:
            for value in parsed_values:
                if choice.value == value:
                    inputs.append(choice.as_input())
        return inputs


class SingleFileConstraint(ValidationConstraint):
    def __init__(self, error_message=None):
        error_message = error_message or _('$label can only accept a single file')
        super(SingleFileConstraint, self).__init__(error_message=error_message)

    def validate_input(self, unparsed_input):
        if not len(unparsed_input) <= 1:
            raise self


class UploadedFile(object):
    """Represents a file that was input by a user."""
    def __init__(self, filename, file_obj, content_type, size):
        self.file_obj = file_obj
        self.filename = filename
        self.content_type = content_type
        self.size = size

    @contextmanager
    def open(self):
        self.file_obj.seek(0)
        try:
            yield self.file_obj
        finally:
            self.file_obj.seek(0)


class FileSizeConstraint(ValidationConstraint):
    name = 'filesize'
    def __init__(self, max_size_bytes, error_message=None):
        error_message = error_message or _('files should be smaller than $human_max_size')
        super(FileSizeConstraint, self).__init__(error_message)
        self.max_size_bytes = max_size_bytes
    
    def __reduce__(self):
        reduced = super(FileSizeConstraint, self).__reduce__()
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
        return six.text_type(self.max_size_bytes)

    def validate_input(self, unparsed_input):
        files_list = unparsed_input
        for f in files_list:
            if f.size > self.max_size_bytes:
                raise self


class MimeTypeConstraint(ValidationConstraint):
    name = 'accept'
    def __init__(self, accept, error_message=None):
        error_message = error_message or _('files should be of type $human_accepted_types')
        super(MimeTypeConstraint, self).__init__(error_message)
        self.accept = accept
    
    def __reduce__(self):
        reduced = super(MimeTypeConstraint, self).__reduce__()
        return (reduced[0], (self.self.accept,))+reduced[2:]

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
            if not matches(f.content_type, self.accept):
                raise self


class MaxFilesConstraint(ValidationConstraint):
    name = 'maxfiles'
    def __init__(self, max_files, error_message=None):
        error_message = error_message or _('a maximum of $max_files files may be uploaded')
        super(MaxFilesConstraint, self).__init__(error_message)
        self.max_files = max_files
    
    def __reduce__(self):
        reduced = super(MaxFilesConstraint, self).__reduce__()
        return (reduced[0], (self.self.max_files,))+reduced[2:]

    @property
    def parameters(self):
        return six.text_type(self.max_files)

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
        super(FileField, self).__init__(default=default, required=required, required_message=required_message, label=label, readable=readable, writable=writable)
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




