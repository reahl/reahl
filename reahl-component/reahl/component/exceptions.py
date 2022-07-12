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

"""Exceptions used throughout several Reahl components."""

import sys

import wrapt
from wrapt.wrappers import PartialCallableObjectProxy
import inspect


from collections.abc import Callable

from reahl.component.context import ExecutionContext
from reahl.component.context import ExecutionContext, NoContextFound


class DomainException(Exception):
    """Any exception indicating an application-specific error condition that 
       should be communicated to a user.

       :keyword commit: Set to True to indicate that the current database transaction 
                        should be committed. By default transactions are rolled back
                        when a DomainException is raised.
       :keyword message: Optional error message.
       :keyword detail_messages: A list of error messages giving more detail about the exception.
       :keyword handled_inline: If False, indicates that this exception is not reported in the normal rendering of the page.

       .. versionchanged: 5.0
          Added `detail_messages` kwarg.
    """
    def __init__(self, commit=False, message=None, detail_messages=[], handled_inline=True, json_string=None):
        super().__init__(message)
        self.commit = commit
        self.message = message
        self.detail_messages = detail_messages
        self.handled_inline = handled_inline
        self.json_string = json_string
    
    def __reduce__(self):
        return (self.__class__, (self.commit, self.message, self.detail_messages, self.handled_inline, self.json_string))

    def as_user_message(self):
        # To ensure this module can be imported at a very low level
        from reahl.component.i18n import Catalogue
        _ = Catalogue('reahl-component')
        return self.message if self.message else _('An error occurred: %s' % self.__class__.__name__)

    def as_json(self):
        if self.json_string:
            return self.json_string
        else:
            return '"%s"' % super().__str__()

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


class NotYetAvailable:
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return '<%s name=%s>' % (self.__class__.__name__, self.name)

class DeferredImport:
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
        if isinstance(type_or_string, str):
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

        if value is None:
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
        super().__init__(allow_none=allow_none)
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
        super().__init__(allow_none=allow_none)
        self.args = args
        self.kwargs = kwargs

    def check(self, func, name, value):
        super().check(func, name, value)
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
        return isinstance(value, Callable)

    def __str__(self):
        return '%s: %s should be a callable object (got %s)' % (self.func, self.arg_name, self.value)

class ArgumentCheckedCallable:
    def __init__(self, target, explanation=None):
        self.target = target
        self.explanation = explanation

    def __call__(self, *args, **kwargs):
        self.checkargs(*args, **kwargs)
        return self.target(*args, **kwargs)

    def checkargs(self, *args, **kwargs):

        try:
            config = ExecutionContext.get_context().config
            if not config.reahlsystem.runtime_checking_enabled:
                return
        except (NoContextFound, AttributeError):
            pass

        if isinstance(self.target, PartialCallableObjectProxy):
            to_check = self.target.__call__
        elif inspect.ismethod(self.target):
            to_check = self.target
        elif inspect.isfunction(self.target):
            to_check = self.target
        elif inspect.isclass(self.target):
            to_check = self.target.__init__
            args = (NotYetAvailable('self'), )+args
        elif isinstance(self.target, Callable):
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
                raise new_ex.with_traceback(tb)
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
            try:
                config = ExecutionContext.get_context().config
                if not config.reahlsystem.runtime_checking_enabled:
                    return wrapped(*args, **kwargs)
            except (NoContextFound, AttributeError):
                pass
            return ArgumentCheckedCallable(wrapped)(*args, **kwargs)
        return check_call(f)

    return catch_wrapped


