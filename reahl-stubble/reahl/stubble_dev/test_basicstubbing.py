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


import pytest

from reahl.stubble import stubclass, exempt, EmptyStub


class Stubbed:
    attr = 1
    
    def method(self, a, b, akwarg=None, *args, **kwargs): pass

    @classmethod
    def a_class_method(cls, x, y): pass

    @property
    def my_existing_property(self):
        return 1


#----------------------------------------[ EmptyStub ]
def test_empty_stub():
    """an EmptyStub can be created with instance attributes"""

    #normal case
    value = EmptyStub()
    stub = EmptyStub(a_value = value)
    assert stub.a_value is value


#----------------------------------------[ shadowed members ]
def test_method_attribute_mismatch():
    """a method in the stub which is an attribute in the stubbed is not allowed"""
    #normal case
    with pytest.raises(AssertionError) as excinfo:
        @stubclass(Stubbed)
        class Stub:
            def attr(self):
                pass

    assert excinfo.match(r"^attribute mismatch: <class '.*\.Stub'>\.<(unbound method|function) .*Stub\.attr.*> is not compatible with the original type <(type|class) 'int'> on <class '.*Stubbed'>")


def test_method_signature_mismatch():
    """a method signature mismatch between the stub and the stubbed is not allowed"""
    #normal case
    with pytest.raises(AssertionError) as excinfo:
        @stubclass(Stubbed)
        class Stub:
            def method(self, b, akwarg=None, *args, **kwargs):
                pass
    assert excinfo.match(r'^signature mismatch on method for args: orig\(\[\'self\', \'a\', \'b\', \'akwarg\'\]\) != stub\(\[\'self\', \'b\', \'akwarg\'\]\)$')


def test_property_method_missing_on_orig():
    """a property on the stub is not allowed if the stubbed class does not have property or an attribute"""
    #case where the property does ont exist on the stubbed class
    with pytest.raises(AssertionError):
        @stubclass(Stubbed)
        class Stub:
            @property
            def non_existing_property(self):
                return 2


def test_property_method_masks_method_on_orig():
    """a property on the stub is not allowed if the stubbed class has a method with the same name"""
    #case where the property does ont exist on the stubbed class
    with pytest.raises(AssertionError):
        @stubclass(Stubbed)
        class Stub:
            @property
            def method(self):
                return 2


def test_property_method_for_attribute_on_orig():
    """a property on the stub is allowed if the stubbed class has a property or an attribute of the same name"""
    #case where the stubbed class has an attribute for the property
    @stubclass(Stubbed)
    class Stub:
        @property
        def attr(self):
            return 2

    #case where the stubbed class has a matching property
    @stubclass(Stubbed)
    class Stub:
        @property
        def my_existing_property(self):
            return 2


def test_attribute_not_present_mismatch():
    """an attribute in the stub which is not in the stubbed is not allowed"""
    #normal case
    with pytest.raises(AssertionError):
        @stubclass(Stubbed, True)
        class Stub:
            i_am_not = 1


def test_method_name_mismatch():
    """a method in the stub which has no counterpart in the stubbed is not allowed"""
    #normal case
    with pytest.raises(AssertionError):
        @stubclass(Stubbed)
        class Stub:
            def method1(self, a, b):
                pass


def test_normal_method():
    """a method in the stub which accurately describes one in the stubbed is allowed"""
    #normal case
    @stubclass(Stubbed)
    class Stub:
        def method(self, a, b, akwarg=None, *args, **kwargs):
            pass


def test_normal_attribute():
    """an attribute in the stub which is also present in the stubbed is allowed"""

    #normal case
    @stubclass(Stubbed, True)
    class Stub:
        attr = 1

    #case where we're not checking for attributes
    @stubclass(Stubbed)
    class Stub:
        i_am_not = 1


#----------------------------------------[ exempt members ]
def test_exempt_attribute():
    """an attribute or property marked exempt does not raise an error"""
    @stubclass(Stubbed, True)
    #normal case
    class Stub:
        attr = 1
        attr = exempt(attr)
        @exempt
        @property
        def prop(self):
            pass

    # the property returns the correct value
    assert Stub().prop is None


def test_exempt_method():
    """any methods marked as exempt does not raise an error"""
    #normal case
    @stubclass(Stubbed)
    class Stub:
        @exempt
        def local_method(self):
            pass

        @exempt
        def method():
            pass

        @exempt
        @classmethod
        def local_class_method(cls):
            pass

        @exempt
        @classmethod
        def a_class_method(cls):
            pass

    Stub.local_class_method()
    Stub.a_class_method()


def test_exempt_inherited_method():
    """any methods marked as exempt do not raise an error, even if they are inherited by the stub"""
    #normal case
    @stubclass(Stubbed)
    class Stub:
        @exempt
        def local_method(self):
            pass

        @exempt
        def method(self):
            pass

        @exempt
        @classmethod
        def local_class_method(cls):
            pass

        @exempt
        @classmethod
        def a_class_method(cls):
            pass

    @stubclass(Stubbed)
    class InheritingStub(Stub):
        pass

    InheritingStub.local_class_method()
    InheritingStub.a_class_method()


