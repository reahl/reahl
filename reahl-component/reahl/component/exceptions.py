# Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import print_function, unicode_literals, absolute_import, division
import six
import inspect
import sys
import functools

import wrapt
import inspect

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

#    __hash__ = None
#    def __eq__(self, other):
#        import pdb; pdb.set_trace()
#        return isinstance(other, self.__class__) and self.commit == other.commit
    
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
            ArgumentCheckedCallable(value, explanation=message).checkargs(*self.args, **self.kwargs)

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

class ArgumentCheckedCallable(object):
    def __init__(self, target, explanation=None):
        if six.PY2 and isinstance(target, functools.partial):
           self.target = target.func
        else:
           self.target = target
        self.explanation = explanation

    def __call__(self, *args, **kwargs):
        self.checkargs(*args, **kwargs)
        return self.target(*args, **kwargs)

    def checkargs(self, *args, **kwargs):
        if inspect.ismethod(self.target):
            to_check = self.target
        elif inspect.isfunction(self.target):
            to_check = self.target
        elif inspect.isclass(self.target):
            to_check = self.target.__init__
            args = (NotYetAvailable('self'), )+args
        elif isinstance(self.target, collections.Callable):
            to_check = self.target.__call__
        else:
            raise ProgrammerError('%s was expected to be a callable object' % self.target)

        try:
            try:
                bound_args = inspect.getcallargs(to_check, *args, **kwargs)
            except TypeError as ex:
                ex.args = (('%s: ' % self.target)+ex.args[0],) + ex.args[1:]
                raise
            args_to_check = getattr(to_check, 'arg_checks', {})
            for arg_name, arg_check in args_to_check.items():
                if arg_name in bound_args.keys():
                    arg_check.check(self.target, arg_name, bound_args[arg_name])
        except (TypeError, ArgumentCheck) as ex:
            if self.explanation:
                _, _, tb = sys.exc_info()
                new_ex = IncorrectArgumentError(self.explanation, ex)
                six.reraise(new_ex.__class__, new_ex, tb)
            else:
                raise


def arg_checks(**checks):
    def catch_wrapped(f):
        if inspect.ismethoddescriptor(f):
            f.__func__.arg_checks = checks
        else:
            f.arg_checks = checks
        @wrapt.decorator
        def check_call(wrapped, instance, args, kwargs):
            if six.PY2:
                if isinstance(wrapped, functools.partial) and not wrapped.func.__self__ and instance:
                    args = (instance,)+args
            return ArgumentCheckedCallable(wrapped)(*args, **kwargs)
        return check_call(f)
    return catch_wrapped


