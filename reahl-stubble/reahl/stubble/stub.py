# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import print_function, unicode_literals, absolute_import, division
import inspect
import collections
from functools import reduce

import six


class StubClass(object):
    def __init__(self, orig, check_attributes_also=False):
        self.orig = orig
        self.check_attributes_also = check_attributes_also

    def __call__(self, stub):
        for attribute_name in dir(stub):
            self.check_compliance(stub, attribute_name)
        stub._stubbed_class = self.orig
        return stub

    def find_in_dict(self, stub, attribute_name):
        for class_ in stub.__mro__:
            try:
                return class_.__dict__[attribute_name]
            except KeyError:
                pass
        return None

    def check_compliance(self, stub, attribute_name):
        if attribute_name.startswith('_'):
            return

        attribute = getattr(stub, attribute_name)
        possible_descriptor = self.find_in_dict(stub, attribute_name)
        if isinstance(possible_descriptor, StubbleDescriptor):
            possible_descriptor.name = attribute_name
            possible_descriptor.stubble_check(None, self.orig, stub)
            if possible_descriptor.is_instance_only():
                delattr(stub, attribute_name)
            return

        try:
            orig_attribute = getattr(self.orig, attribute_name)
        except AttributeError:
            if not self.check_attributes_also:
                if not isinstance(attribute, collections.Callable) and not isinstance(attribute, property): 
                    return 

            message = 'attribute mismatch: %s.%s does not exist on %s' % \
                (stub, attribute_name, self.orig)
            raise AssertionError(message)

        if orig_attribute is attribute:
            return
        
        self.types_match(stub, orig_attribute, attribute)
        if inspect.ismethod(orig_attribute) or inspect.isfunction(orig_attribute):
            self.signatures_match(orig_attribute, attribute)

    def types_match(self, stub, orig, stubbed):
        assert isinstance(orig, collections.Callable) == isinstance(stubbed, collections.Callable), \
            'attribute mismatch: %s.%s is not compatible with the original type %s on %s' % \
            (stub, stubbed, type(orig), self.orig)

    @classmethod
    def signatures_match(cls, orig, stubbed, ignore_self=False):
        if six.PY2:
            orig_arguments = inspect.getargspec(orig)
            stub_arguments = inspect.getargspec(stubbed)
        else:
            orig_arguments = inspect.getfullargspec(orig)
            stub_arguments = inspect.getfullargspec(stubbed)

        if ignore_self:
            if 'self' in orig_arguments.args: orig_arguments.args.remove('self')
            if 'self' in stub_arguments.args: stub_arguments.args.remove('self')
        assert orig_arguments == stub_arguments, \
            'signature mismatch: %s%s does not match %s%s' % \
            (stubbed, inspect.formatargspec(*stub_arguments), 
             orig, inspect.formatargspec(*orig_arguments))
            
        return False
        


#------------------------------------------------[ Impostor ]
class Impostor(object):
    def __getattribute__(self, name):
        _stubbed_class = object.__getattribute__(self, '_stubbed_class')
        if name == '__class__':
            return _stubbed_class
        return super(Impostor, self).__getattribute__(name)
                        


#------------------------------------------------[ Delegate ]
class Delegate(object):
    def __init__(self, real):
        super(Delegate, self).__setattr__('real', real)

    def _bound_delegate_method(self, name, method_name):
        real = super(Delegate, self).__getattribute__('real')
        shadowed = super(Delegate, self).__getattribute__('shadowed')

        if name in shadowed:
            return getattr(super(Delegate, self), method_name)
        else:
            if method_name == '__getattribute__':
                method = getattr
            elif method_name == '__setattr__':
                method = setattr
            elif method_name == '__delattr__':
                method = delattr
            return lambda *args: method(real, *args)

        assert None, \
               '_bound_delegate_method may only be called for one of: __getattribute__, __setattr__, __delattr__'

    def __getattribute__(self, name):
        _stubbed_class = object.__getattribute__(self, '_stubbed_class')
        if name == '__class__':
            return _stubbed_class

        bound_delegate_method = super(Delegate, self).__getattribute__('_bound_delegate_method')
        return bound_delegate_method(name, '__getattribute__')(name)

    def __setattr__(self, name, value):
        bound_delegate_method = super(Delegate, self).__getattribute__('_bound_delegate_method')
        bound_delegate_method(name, '__setattr__')(name, value)

    def __delattr__(self, name):
        bound_delegate_method = super(Delegate, self).__getattribute__('_bound_delegate_method')
        bound_delegate_method(name, '__delattr__')(name)


#------------------------------------------------[ StubbleDescriptor ]
class StubbleDescriptor(object):
    def stubble_check(self, instance, orig, stub):
        pass

    def is_instance_only(self):
        return False


#------------------------------------------------[ SlotConstrained ]
class SlotConstrained(StubbleDescriptor):
    def available_slots(self, cls):
        def flatten_slots(l, cls):
            s = cls.__slots__
            if isinstance(s, six.string_types):
                s = [s]
            l.extend(s)
            return l
        return reduce(flatten_slots, inspect.getmro(cls)[:-1], [])

    def stubble_check(self, instance, orig, stub):
        assert self.name in self.available_slots(orig), \
               'stub attribute mismatch for "%s.%s": %s not found in __slots__ of %s or its anchestors' % \
               (stub.__name__,
                self.name,
                self.name,
                orig.__name__)

    def is_instance_only(self):
        return True


#------------------------------------------------[ Exempt ]
class Exempt(StubbleDescriptor):
    def __init__(self, value):
        self.value = value

    def __get__(self, instance, owner):
        if inspect.ismethoddescriptor(self.value) or inspect.isdatadescriptor(self.value):
            return self.value.__get__(instance, owner)
        if inspect.isfunction(self.value):
            if instance is None:
                return self
            else:
                return six.create_bound_method(self.value, instance)
        else:
            return self.value            


#------------------------------------------------[ CheckedInstance ]    
class CheckedInstance(StubbleDescriptor):
    def stubble_check(self, instance, orig, stub):
        assert hasattr(orig, self.name), \
               'stub attribute mismatch for "%s.%s": %s not found as class attribute of %s' % \
               (stub.__name__,
                self.name,
                self.name,
                orig.__name__)

    def is_instance_only(self):
        return True    
