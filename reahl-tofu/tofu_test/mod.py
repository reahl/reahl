# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


import unittest

class TestCase(unittest.TestCase):
    def test_working(self):
        self.ran = True
        return True

    def test_failing(self):
        self.ran = True
        assert None, 'here we fail'

class TestCase2(unittest.TestCase):
    def test_working2(self):
        self.ran = True
        return True

