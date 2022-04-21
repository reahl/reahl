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
import sys
import os

sys.path.insert(0, os.getcwd())

def test_class_name(module_name):
    class_name = module_name.split('.')[-1]
    return '%s.%s' % (module_name, class_name)

loader = unittest.TestLoader()
runner = unittest.TextTestRunner()
testNames = [test_class_name(name) for name in sys.argv[1:]]

tests = loader.loadTestsFromNames(testNames)
runner.run(tests)
