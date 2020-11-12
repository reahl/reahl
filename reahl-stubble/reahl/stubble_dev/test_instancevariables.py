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
from reahl.stubble import stubclass, checkedinstance, slotconstrained


def test_checked_instance_attributes_are_like_instance_attributes():
    """an attribute marked as checkedinstance behaves like an instance
       variable, but is checked against the class variables in the stubbed class"""

    class Stubbed:
        a = None

    with pytest.raises(AssertionError):
        #case where a class variable with such a name does not exist on the stubbed
        @stubclass(Stubbed)
        class Stub:
            b = checkedinstance()

    #case where a class variable with such a name does exist on the stub
    @stubclass(Stubbed)
    class Stub:
        a = checkedinstance()

    s = Stub()
    assert not hasattr(s, 'a')
    s.a = 12
    assert s.a == 12
    del s.a
    assert not hasattr(s, 'a')


def test_constrained_declaration():
    """an attribute marked slotconstrained breaks at definition time iff its name is not
       in __slots__ of Stubbed or its ancestors"""

    class Ancestor:
        __slots__ = ('a')

    class Stubbed(Ancestor):
        __slots__ = ('b')

    #case for name in __slots__ of ancestors
    @stubclass(Stubbed)
    class Stub:
        a = slotconstrained()

    #case for name in __slots__ of stubbed
    @stubclass(Stubbed)
    class Stub:
        b = slotconstrained()

    with pytest.raises(AssertionError):
        #case where name is not found
        @stubclass(Stubbed)
        class Stub:
            c = slotconstrained()
