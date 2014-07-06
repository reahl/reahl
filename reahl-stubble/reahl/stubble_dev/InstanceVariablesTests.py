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
from nose.tools import istest, assert_raises

from reahl.stubble import stubclass, checkedinstance, slotconstrained

@istest
class InstanceVariablesTests(object):
    def setUp(self):
        class Stubbed(object):
            a = None

        self.stubbed = Stubbed

    @istest
    def test_checked_instance_attributes_are_like_instance_attributes(self):
        """an attribute marked as checkedinstance behaves like an instance
           variable, but is checked against the class variables in the stubbed class"""

        #case where a class variable with such a name does not exist on the stubbed
        def declare_it():
            @stubclass(self.stubbed)
            class Stub(object):
                b = checkedinstance()

        assert_raises(AssertionError,
                          declare_it)

        #case where a class variable with such a name does exist on the stub
        @stubclass(self.stubbed)
        class Stub(object):
            a = checkedinstance()

        s = Stub()
        assert not hasattr(s, 'a')
        s.a = 12
        assert s.a == 12
        del s.a
        assert not hasattr(s, 'a')

    @istest
    def test_constrained_declaration(self):
        """an attribute marked slotconstrained breaks at definition time iff its name is not
           in __slots__ of Stubbed or its ancestors"""

        class Ancestor(object):
            __slots__ = ('a')

        class Stubbed(Ancestor):
            __slots__ = ('b')

        self.stubbed = Stubbed

        #case for name in __slots__ of ancestors
        @stubclass(self.stubbed)
        class Stub(object):
            a = slotconstrained()

        #case for name in __slots__ of stubbed
        @stubclass(self.stubbed)
        class Stub(object):
            b = slotconstrained()

        #case where name is not found
        def declare_it():
            @stubclass(self.stubbed)
            class Stub(object):
                c = slotconstrained()
        assert_raises(AssertionError, declare_it)
