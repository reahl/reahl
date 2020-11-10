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

from reahl.stubble import Delegate, stubclass, exempt, Impostor, slotconstrained, checkedinstance

#----------------------------------------[ the real code ]
# RealClass is not a test class - it is an example of a class
# which we will create example stubs for
class RealClass:
    b = 123

    def foo(self, a):
        print('i am the real foo')

    def bar(self):
        print('i am the real bar')


#==================================================[ BasicStubRequirements ]
# (see also acceptance/BasicStubRequirementsTests.py)


#----------------------------------------[ straightforward stuff ]
@stubclass(RealClass)
class Stub:
    def foo(self, a):
        """i am a fake foo"""

s = Stub()
s.foo(1)       #calls the fake foo (off course)
s.x = 1        #sets a new instance attribute "x" as usual
try:
    s.bar()    #breaks as usual, since bar does not exist
except:
    pass


#----------------------------------------[ really being a-kind-of the real class ]
@stubclass(RealClass)
class Stub(RealClass):
    def foo(self, a):
        print('i am a fake foo')

s = Stub()
s.foo(1)      #calls the fake foo, naturally
s.bar()       #calls the real bar (which may even call the fake foo polimorphically)

#----------------------------------------[ class attributes ]
@stubclass(RealClass, check_attributes_also=True)
class Stub(RealClass):
    pass

#    a = 'asd'    # uncomment this line and it will break


#----------------------------------------[ exempt methods ]
@stubclass(RealClass)
class Stub:
    @exempt
    def my_own_method(self):
        print('i am my own method')


s = Stub()
s.my_own_method()


#==================================================[ Impostoring ]
# (see also acceptance/ImpostoringTests.py)

@stubclass(RealClass)
class Stub(Impostor):
    pass

assert not issubclass(Stub, RealClass)  #unfortunatly issubclass still catches Impostors out
s = Stub()
assert isinstance(s, RealClass)         #but the foolery works well here


#==================================================[ Delegation ]
# (see also acceptance/DelegationTests.py)


#----------------------------------------[ replacing an already existing instance ]
real_instance = RealClass()


@stubclass(RealClass)
class Stub(Delegate):
    shadowed = exempt(['foo', 'aa'])

    def foo(self, a):
        print('i am a fake foo')


s = Stub(real_instance)

assert isinstance(s, RealClass)         #Delegates act like Impostors do
s.foo(1)                                #calls the fake
s.bar()                                 #calls the real

try:
    s.aa                                #breaks regardless of whether or not aa is on real_instance
except:
    pass

s.aa = 123                              #is set on the fake
assert s.aa == 123                      #read from the fake
assert not hasattr(real_instance, 'aa')  #see, it was not set there


#----------------------------------------[ the problem with Delegates ]
class AnotherRealClass:
    def foo(self):
        self.aa = 123

real_instance = AnotherRealClass()


@stubclass(AnotherRealClass)
class Stub(Delegate):
    shadowed = exempt(['aa'])

s = Stub(real_instance)

#the behaviour we would expect here is that, upon
# calling s.foo, the real foo is called, which
# sets 'aa' on the stub, even though the setting of
# 'aa' happens in real code.

s.foo()

try:
    #this expected behaviour is would have been tested
    # like this:
    assert s.aa == 123
    assert not hasattr(real_instance, 'aa')
except:
    pass

#but alas, we cannot do that...
#
# This problem severely limits the use of Delegates and can
# cause bugs in tests that are very difficult to find, so be
# careful!
#


#==================================================[ InstanceVariables ]
# (see also acceptance/InstanceVariablesTests.py)

#----------------------------------------[ a misconception about __slots__ ]
# This example was originally posted on comp.lang.python
# by Blair Hall on Apr 10 2003:  (I modified it a bit, though...)
#
class A:
    def __init__(self):
        pass


class B(A):
    __slots__ = ('z',)
    def __init__(self):
        super().__init__()

#now, if you used __slots__ thinking that, since 'c' is not in B.__slots__
#  and that the code above would complain, you're in for a surprise...
b = B()
b.c = 3     # passes


#----------------------------------------[ using the class attributes convention ]
class RealClassFollowingConventions:
    a = None
    b = None


@stubclass(RealClass)
class Stub:
    a = 'asd'
    b = checkedinstance()


#----------------------------------------[ for the stubborn ]
#  (remove 'aa' from __slots__ to see it complain)


class StubbornRealClass:
    __slots__ = ('aa')


@stubclass(StubbornRealClass)
class Stub  :
    aa = slotconstrained()

s = Stub()
try:
    s.aa                      #even though declared as class attributes, these behave
                              # like instance attributes, so its not there if not set
except AttributeError as e:
    pass

s.aa = 123                    #as usual
assert s.aa == 123            #as usual

