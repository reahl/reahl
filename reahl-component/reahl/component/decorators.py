# Copyright 2013-2023 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.



import inspect
import warnings
import sys

import platform
import pkg_resources
import wrapt

def deprecated(message, version='n/a'):
    def catch_wrapped(f):
        def is_init_or_classmethod(member):
            if sys.version_info.major == 3 and sys.version_info.minor >= 11:
                if isinstance(member, classmethod): 
                    return True
            else:
                if inspect.ismethod(member) and member.__self__ is f: 
                    return True
            return (inspect.ismethod(member) or inspect.isfunction(member)) and member.__name__ == '__init__'

        @wrapt.decorator
        def deprecated_wrapper(wrapped, instance, args, kwargs):
            if is_init_or_classmethod(wrapped):
                deprecated_thing = wrapped.__self__.__class__ 
                warnings.warn('DEPRECATED: %s. %s' % (deprecated_thing.__class__, message), DeprecationWarning, stacklevel=2)
            else:
                deprecated_thing = wrapped
                warnings.warn('DEPRECATED: %s. %s' % (deprecated_thing, message), DeprecationWarning, stacklevel=2)
                
            return wrapped(*args, **kwargs)

        if pkg_resources.parse_version(platform.python_version()) > pkg_resources.parse_version('3.6') and f.__doc__:
            f.__doc__ = '%s\n\n.. deprecated:: %s\n   %s' % (f.__doc__, version, message)

        if inspect.isclass(f):
            if sys.version_info.major == 3 and sys.version_info.minor >= 11:
                getmembers = inspect.getmembers_static
            else:
                getmembers = inspect.getmembers
                
            for name, method in getmembers(f, predicate=is_init_or_classmethod):
                setattr(f, name, deprecated_wrapper(method))
            return f
        else:
            return deprecated_wrapper(f)

    return catch_wrapped


