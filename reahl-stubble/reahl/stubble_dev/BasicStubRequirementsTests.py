# Copyright 2005, 2006, 2008-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import unicode_literals
from __future__ import print_function
import six

from nose.tools import istest, assert_raises, assert_true, assert_equals

from reahl.stubble import stubclass, exempt, EmptyStub


@istest
class BasicStubRequirementsTests(object):
    def setUp(self):
        class Stubbed(object):
            attr = 1
            def method(self, a, b, akwarg=None, *args, **kwargs): pass
            @classmethod
            def a_class_method(cls, x, y): pass
            @property
            def my_existing_property(self):
                return 1
        self.stubbed = Stubbed

    #----------------------------------------[ EmptyStub ]
    @istest
    def test_empty_stub(self):
        """an EmptyStub can be created with instance attributes"""

        #normal case
        value = EmptyStub()
        stub = EmptyStub(a_value = value)
        assert_true( stub.a_value is value )

    #----------------------------------------[ shadowed members ]
    @istest
    def test_method_attribute_mismatch(self):
        """a method in the stub which is an attribute in the stubbed is not allowed"""
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                def attr(self): pass
        
        #normal case
        with assert_raises(AssertionError) as context:
            declare_class()
        assert_equals( six.text_type(context.exception), '''attribute mismatch: <class 'reahl.stubble_dev.BasicStubRequirementsTests.Stub'>.<unbound method Stub.attr> is not compatible with the original type <type 'int'> on <class 'reahl.stubble_dev.BasicStubRequirementsTests.Stubbed'>''' )

    @istest
    def test_method_signature_mismatch(self):
        """a method signature mismatch between the stub and the stubbed is not allowed"""
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                def method(self, b, akwarg=None, *args, **kwargs): pass

        #normal case
        with assert_raises(AssertionError) as context:
            declare_class()
        
        assert_equals( six.text_type(context.exception), '''signature mismatch: <unbound method Stub.method>(self, b, akwarg=None, *args, **kwargs) does not match <unbound method Stubbed.method>(self, a, b, akwarg=None, *args, **kwargs)''' )

    @istest
    def test_property_method_missing_on_orig(self):
        """a property on the stub is not allowed if the stubbed class does not have property or an attribute"""
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                @property
                def non_existing_property(self):
                    return 2

        #case where the property does ont exist on the stubbed class
        assert_raises(AssertionError, declare_class)

    @istest
    def test_property_method_masks_method_on_orig(self):
        """a property on the stub is not allowed if the stubbed class has a method with the same name"""
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                @property
                def method(self):
                    return 2

        #case where the property does ont exist on the stubbed class
        assert_raises(AssertionError, declare_class)

    @istest
    def test_property_method_for_attribute_on_orig(self):
        """a property on the stub is allowed if the stubbed class has a property or an attribute of the same name"""
        #case where the stubbed class has an attribute for the property
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                @property
                def attr(self):
                    return 2

        declare_class()

        #case where the stubbed class has a matching property
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                @property
                def my_existing_property(self):
                    return 2

        declare_class()

    @istest
    def test_attribute_not_present_mismatch(self):
        """an attribute in the stub which is not in the stubbed is not allowed"""
        def declare_class():
            @stubclass(self.stubbed, True)
            class Stub(object):
                i_am_not = 1

        #normal case
        assert_raises(AssertionError, declare_class)

    @istest
    def test_method_name_mismatch(self):
        """a method in the stub which has no counterpart in the stubbed is not allowed"""
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                def method1(self, a, b): pass

        #normal case
        assert_raises(AssertionError, declare_class)

    @istest
    def test_normal_method(self):
        """a method in the stub which accurately describes one in the stubbed is allowed"""
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                def method(self, a, b, akwarg=None, *args, **kwargs): pass

        #normal case
        declare_class()

    @istest
    def test_normal_attribute(self):
        """an attribute in the stub which is also present in the stubbed is allowed"""

        #normal case
        def declare_class():
            @stubclass(self.stubbed, True)
            class Stub(object):
                attr = 1

        declare_class()

        #case where we're not checking for attributes
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                i_am_not = 1

        declare_class()

    #----------------------------------------[ exempt members ]
    @istest
    def test_exempt_attribute(self):
        """an attribute or property marked exempt does not raise an error"""
        def declare_class():
            @stubclass(self.stubbed, True)
            class Stub(object):
                attr = 1
                attr = exempt(attr)
                @exempt
                @property
                def prop(self): pass
            return Stub

        #normal case
        Stub = declare_class()

        # the property returns the correct value
        assert Stub().prop is None

    @istest
    def test_exempt_method(self):
        """any methods marked as exempt does not raise an error"""
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                @exempt
                def local_method(self): pass

                @exempt
                def method(): pass

                @exempt
                @classmethod
                def local_class_method(cls): pass

                @exempt
                @classmethod
                def a_class_method(cls): pass
            return Stub

        #normal case
        _class = declare_class()
        _class.local_class_method()
        _class.a_class_method()

    @istest
    def test_exempt_inherited_method(self):
        """any methods marked as exempt does not raise an error, even if they are inherited by the stub"""
        def declare_class():
            @stubclass(self.stubbed)
            class Stub(object):
                @exempt
                def local_method(self): pass

                @exempt
                def method(): pass

                @exempt
                @classmethod
                def local_class_method(cls): pass

                @exempt
                @classmethod
                def a_class_method(cls): pass


            @stubclass(self.stubbed)
            class InheritingStub(Stub):
                pass
            
            return InheritingStub

        #normal case
        _class = declare_class()
        _class.local_class_method()
        _class.a_class_method()


