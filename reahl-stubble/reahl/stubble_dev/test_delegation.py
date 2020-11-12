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
from reahl.stubble import Delegate, stubclass, exempt

@pytest.fixture
def stubbed_class():
    class Stubbed:
        def method1(self): pass
        def method2(self): self.method1()
        attr1 = object()
        attr2 = object()
    return Stubbed


@pytest.fixture
def stubbed_instance(stubbed_class):
    return stubbed_class()


def test_delegate_pretends_to_be_stubbed(stubbed_class, stubbed_instance):
    """a Delegate fakes being an instance the stubbed class"""
    @stubclass(stubbed_class)
    class Stub(Delegate):
        pass

    stub = Stub(stubbed_instance)

    #normal case
    assert isinstance(stub, stubbed_class)


def test_methods_and_attributes_are_shadowed_on_delegate_instance(stubbed_class, stubbed_instance):
    """a method/attribute in the Delegate overrides one in the stubbed iff it is listed as shadowed"""

    @stubclass(stubbed_class)
    class Stub(Delegate):
        shadowed = exempt(['method1', 'attr1'])

        def method1(self): pass
        attr1 = object()

    stub = Stub(stubbed_instance)

    #case for a shadowed method
    assert stub.method1 != stubbed_instance.method1

    #case for non-shadowed method
    assert stub.method2 == stubbed_instance.method2

    #case for a shadowed attribute
    assert stub.attr1 is Stub.attr1
    stub.attr1 = 1
    assert stub.attr1 == 1
    del stub.attr1
    assert stub.attr1 is Stub.attr1

    #case for a non-shadowed attribute
    assert stub.attr2 is stubbed_class.attr2
    stub.attr2 = 2
    assert stubbed_instance.attr2 == 2
    del stub.attr2
    assert stub.attr2 is stubbed_class.attr2

#-----------------------------------------------------------------
# This is something we would like, but lack good ideas for how to implement it:
#  (see the explanation in examples/example.py)
#
#     def test_all_attribute_and_method_accesses_on_stubbed_are_intercepted(stubbed_class, stubbed_instance):
#         @stubclass(stubbed_class)
#         class Stub(Delegate):
#             shadowed = exempt(['method1'])

#             def method1(self): self.a = 1234

#         stub = Stub(stubbed_instance)
#         stub.method2()
#         assert stub.a == 1234
