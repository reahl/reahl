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
from reahl.stubble import Impostor, stubclass


@istest
class ImpostoringTests(object):
    def setUp(self):
        class Stubbed(object):
            __slots__ = 'a'

        self.stubbed = Stubbed

    @istest
    def test_impostor_pretends_to_be_stubbed(self):
        """an Impostor fakes being an instance the stubbed class"""

        @stubclass(self.stubbed)
        class Stub(Impostor):
            pass
        
        stub = Stub()
        #normal case
        assert isinstance(stub, self.stubbed)
