# Copyright 2005, 2006, 2009, 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from nose.tools import istest

from reahl.stubble import Delegate,stubclass,exempt


@istest
class DelegationTests(object):
    def setUp(self):
        class Stubbed(object):
            def method1(self): pass
            def method2(self): self.method1()
            attr1 = object()
            attr2 = object()

        self.stubbed = Stubbed
        self.stubbed_instance = Stubbed()

    @istest
    def test_delegate_pretends_to_be_stubbed(self):
        """a Delegate fakes being an instance the stubbed class"""
        @stubclass(self.stubbed)
        class Stub(Delegate):
            pass
        
        stub = Stub(self.stubbed_instance)

        #normal case
        assert isinstance(stub, self.stubbed)

    @istest
    def test_methods_and_attributes_are_shadowed_on_delegate_instance(self):
        """a method/attribute in the Delegate overrides one in the stubbed iff it is listed as shadowed"""

        @stubclass(self.stubbed)
        class Stub(Delegate):
            shadowed = exempt(['method1', 'attr1'])

            def method1(self): pass
            attr1 = object()

        stub = Stub(self.stubbed_instance)

        #case for a shadowed method
        assert stub.method1 != self.stubbed_instance.method1

        #case for non-shadowed method
        assert stub.method2 == self.stubbed_instance.method2

        #case for a shadowed attribute
        assert stub.attr1 is Stub.attr1
        stub.attr1 = 1
        assert stub.attr1 == 1
        del stub.attr1
        assert stub.attr1 is Stub.attr1

        #case for a non-shadowed attribute
        assert stub.attr2 is self.stubbed.attr2
        stub.attr2 = 2
        assert self.stubbed_instance.attr2 == 2
        del stub.attr2
        assert stub.attr2 is self.stubbed.attr2

#-----------------------------------------------------------------
# This is something we would like, but lack good ideas for how to implement it:
#  (see the explanation in examples/example.py)
#
#     def test_all_attribute_and_method_accesses_on_stubbed_are_intercepted(self):
#         @stubclass(self.stubbed)
#         class Stub(Delegate):
#             shadowed = exempt(['method1'])

#             def method1(self): self.a = 1234

#         stub = Stub(self.stubbed_instance)
#         stub.method2()
#         assert stub.a == 1234
