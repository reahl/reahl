# Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Exceptions used throughout several Reahl components."""

from __future__ import unicode_literals
from __future__ import print_function
import six
import inspect
import sys

from decorator import decorator

from reahl.component.i18n import Translator
import collections

_ = Translator('reahl-component')

class DomainException(Exception):
    """Any exception indicating an application-specific error condition that 
       should be communicated to a user.

       :param commit: Set to True to indicate that the current database transaction 
                      should be committed. By default transactions are rolled back
                      when a DomainException is raised.
    """
    def __init__(self, commit=False):
        self.commit = commit

    __hash__ = None
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.commit == other.commit
    
    def __reduce__(self):
        return (self.__class__, (self.commit,))
    
    def as_user_message(self):
        return _('An error occurred: %s' % self.__class__.__name__)


class AccessRestricted(Exception):
    """Raised to prevent the current user to perform some function which is not allowed."""

class ProgrammerError(Exception):
    """Raised to indicate an error in the program."""

class IncorrectArgumentError(ProgrammerError):
    """Raised to indicate an attempt to pass an incorrect argument to a Python callable."""
    def __init__(self, explanation, cause):
        ProgrammerError.__init__(self)
        self.explanation = explanation
        self.cause = cause
    
    def __str__(self):
        return '%s (%s)' % (self.explanation, self.cause)


class NotYetAvailable(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return '<%s name=%s>' % (self.__class__.__name__, self.name)

class DeferredImport(object):
    def __init__(self, value_or_string):
        self.value_or_string = value_or_string

    @property
    def value(self):
        return self.coerce_to_type(self.value_or_string)

    def import_string_spec(self, string_spec):
        bits = string_spec.split(':')
        assert len(bits) == 2, 'Invalid specification %s' % string_spec
        [module_name, class_name] = bits

        try:
            module = __import__(module_name, {}, {}, [class_name], 0)
            return getattr(module, class_name)
        except ImportError:
            raise ProgrammerError('Could not import %s' % string_spec)
        except AttributeError:
            raise ProgrammerError('Could not find %s in %s (from %s)' % (class_name, module_name, string_spec))

    def coerce_to_type(self, type_or_string):
        if isinstance(type_or_string, six.string_types):
            return self.import_string_spec(type_or_string)
        else:
            return type_or_string

class ArgumentCheck(Exception):
    def __init__(self, allow_none=False):
        self.allow_none = allow_none

    def check(self, func, name, value):
        if isinstance(value, NotYetAvailable):
            if value.name != name:
                raise IncorrectArgumentError('expected an argument for %s, got ' % name, value)
            else:
                return

        if not value:
            if not self.allow_none:
                self.raise_with(func, name, value)
            else:
                return
        if not self.is_valid(value):
            self.raise_with(func, name, value)

    def is_valid(self, value):
        return False
        
    def raise_with(self, func, arg_name, value):
        self.func = func
        self.arg_name = arg_name
        self.value = value
        raise self
    
class TypeBasedArgumentCheck(ArgumentCheck):
    def __init__(self, type_or_string, allow_none=False):
        super(TypeBasedArgumentCheck, self).__init__(allow_none=allow_none)
        self.type_ = DeferredImport(type_or_string)

    def is_marked_with_attribute(self, value):
        return hasattr(self.type_.value, '__name__') and hasattr(value, 'is_%s' % self.type_.value.__name__)

class IsInstance(TypeBasedArgumentCheck):
    def is_valid(self, value):
        return isinstance(value, self.type_.value) or self.is_marked_with_attribute(value)

    def __str__(self):
        return '%s: %s should be an instance of %s (got %s instead)' % (self.func, self.arg_name, self.type_.value, self.value)
        
class IsSubclass(TypeBasedArgumentCheck):
    def is_valid(self, value):
        return inspect.isclass(value) and (issubclass(value, self.type_.value) or self.is_marked_with_attribute(value))

    def __str__(self):
        return '%s: %s should be %s or subclass of it (got %s instead)' % (self.func, self.arg_name, self.type_.value, self.value)

class IsCallable(ArgumentCheck):
    def __init__(self, args=(), kwargs={}, allow_none=False):
        super(IsCallable, self).__init__(allow_none=allow_none)
        self.args = args
        self.kwargs = kwargs

    def check(self, func, name, value):
        super(IsCallable, self).check(func, name, value)
        if value:
            message = '%s will be called with %s' % (value, self.formatted_message())
            checkargs_explained(message, value, *self.args, **self.kwargs)

    def formatted_message(self):
        formatted_args = ','.join([i.name for i in self.args])
        formatted_kwargs = ','.join(['%s=%s' for name, default in self.kwargs.items()])
        formatted_all = []
        if formatted_args:
            formatted_all.append(formatted_args)
        if formatted_kwargs:
            formatted_all.append(formatted_kwargs)
        return '(%s)' % (','.join(formatted_all))

    def is_valid(self, value):
        return isinstance(value, collections.Callable)

    def __str__(self):
        return '%s: %s should be a callable object (got %s)' % (self.func, self.arg_name, self.value)

def checkargs(method, *args, **kwargs):
    arg_checks = getattr(method, 'arg_checks', {})
    try:
        if inspect.ismethod(method) or inspect.isfunction(method):
            to_check = method
        elif inspect.isclass(method):
            to_check = method.__init__
        elif isinstance(method, collections.Callable):
            to_check = method.__call__
        else:
            raise ProgrammerError('%s was expected to be a callable object' % method)

        if inspect.ismethod(to_check) and not to_check.__self__:
            call_args = (NotYetAvailable('self'),)+args
        else:
            call_args = args
        bound_args = inspect.getcallargs(to_check, *call_args, **kwargs)
    except TypeError as ex:
        ex.args = (('%s: ' % method)+ex.args[0],) + ex.args[1:]
        raise
    for arg_name, arg_check in arg_checks.items():
        if arg_name in bound_args.keys():
            arg_check.check(method, arg_name, bound_args[arg_name])

def checkargs_explained(explanation, method, *args, **kwargs):
    try:
        checkargs(method, *args, **kwargs)
    except (TypeError, ArgumentCheck) as ex:
        _, _, tb = sys.exc_info()
        new_ex = IncorrectArgumentError(explanation, ex)
        six.reraise(new_ex.__class__, new_ex, tb)


class arg_checks(object):
    def __init__(self, **arg_checks):
        self.arg_checks = arg_checks
    
    def __call__(self, f):
        f.arg_checks = self.arg_checks
        def check_call(func, *args, **kwargs):
            checkargs(func, *args, **kwargs)
            return func(*args, **kwargs)
        return decorator(check_call, f)

