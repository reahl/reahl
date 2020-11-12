# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import types
import inspect
from functools import reduce

#
# class XStub(Stub):
#    stubbedclass = ARealClass
#    def abc(...):
#	pass
#
#    xx = stubbedmethod(abc)
# or:
#    xx = stubbedvariable(something)
#
# this way, when xx is called, it can break if xx with signature of abc
# is not same as in real class.
#
# or:
# class XStub(ARealClass):
#    def overridingmethodwithanyname(...):
#	pass
#    supermethodname = stubbedmethod(overridingmethodwithanyname)
#

# 2 scenarios:
#  -There is no instance, you want to instantiate (with/without normal __init__)
#  this exists in 2 flavours:
#   1) you implement an EmptyStub with only the methods you need on it
#   2) you inherit from RealClass and override only what you need to
#  -There is an instance which you want to replace with some methods forwarded, some stubbed.
#  (this is guessing - not used)


class Stub:
    pass


class StubMethod:
    def __init__(self, stub):
        self.stub = stub

    def __get__(self, instance, owner):
        assert issubclass(owner, Stub), 'stubbed methods belong in Stub classes...'
        assert instance, 'implemented for instance methods only'
        real_method = getattr(owner.stubbed, self.stub.__name__)
        assert isinstance(real_method.im_func, types.FunctionType), 'stubbed methods are for methods...'
        assert None, 'Hi'
        real_args = inspect.getfullargspec(real_method.im_func)
        stub_args = inspect.getfullargspec(self.stub)
        assert real_args == stub_args, 'argument specification mismatch'

        return types.MethodType(self.stub, instance)

    def __set__(self, instance, value):
        assert None, 'cannot set stub methods'

    def __delete__(self, instance):
        assert None, 'cannot delete stub methods'


def stubmethod(stub):
    return StubMethod(stub)


class StubAttribute:
    def __init__(self, name):
        self.name = name

    def instance_attributes(self, cls):
        def all_slots(l, cls):
            s = cls.__slots__
            if isinstance(s, str):
                s = [s]
            l.extend(s)
            return l
        return reduce(all_slots, inspect.getmro(cls)[:-1], [])

    def __get__(self, instance, owner):
        assert issubclass(owner, Stub), 'stubbed attributes belong in Stub classes...'
        assert instance, 'implemented for instance attributes only'
        assert self.name in self.instance_attributes(owner.stubbed), \
               'attribute not in real class'
        return getattr(instance, 'stubbed_%s' % self.name)

    def __set__(self, instance, value):
        setattr(instance, 'stubbed_%s' % self.name, value)

    def __delete__(self, instance):
        delattr(instance, 'stubbed_%s' % self.name)

def stubattribute(name):
    return StubAttribute(name)


class RealClass:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def ma(self, b):
        self.b = b

    def mb(self):
        self.boo = 'foo'

    @classmethod
    def pa(cls, a): pass

    def boetie(a, y): pass

    xx = 'yy'


class StubEx1(Stub):
    #this is how EmptyStub is used currently)

    stubbed = RealClass
    x = stubattribute('x')

    @stubmethod
    def ma(self, b):
        print('stub called with %s' % b)

    @stubmethod
    def donkey(self):
        print('donkey')

    @stubmethod
    def mb(self, b, c):
        print('stub called with %s %s' % (b, c))


class StubEx2(RealClass, Stub):
    #this is how classes are subclassed currently
    stubbed = RealClass
    x = StubAttribute('x')

    @stubmethod
    def ma(self, d):
        print('stub called with %s' % d)

    @stubmethod
    def donkey(self):
        print('donkey')

    @stubmethod
    def mb(self, b, c):
        print('stub called with %s %s' % (b, c))

s1 = StubEx1()
s2 = StubEx2(1, 2)
