# Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from nose.tools import istest
from reahl.tofu import Fixture
from reahl.tofu import test
from reahl.tofu import expected, NoException, vassert

from reahl.component.exceptions import IncorrectArgumentError, arg_checks, IsInstance, IsSubclass, checkargs, checkargs_explained, NotYetAvailable


@istest
class ArgumentCheckTests(object):
    @test(Fixture)
    def checking_arguments(self, fixture):
        """Methods can be augmented with checks that can be performed on arguments sent to them. 
           These checks are done when calling such a method, or can be done before calling a method
           via checkargs or checkargs_explained."""
        
        class ModelObject(object):
            @arg_checks(y=IsInstance(int), title=IsInstance(six.string_types))
            def do_something(self, x, y, title='a title', style=None):
                pass
                
        model_object = ModelObject()
        with expected(IsInstance):
            model_object.do_something(1, '2', title='some title', style='style')
        with expected(IsInstance):
            model_object.do_something(1, 2, title=3, style='style')
        with expected(IsInstance):
            model_object.do_something(1, 2, 3, 'style')
        with expected(IsInstance):
            model_object.do_something(1, 2, title=None)
        
        with expected(NoException):
            model_object.do_something(1, 2)

        with expected(IsInstance):
            checkargs(model_object.do_something, 1, 2, 3)
        with expected(TypeError):
            checkargs(model_object.do_something, 1, 2, 3, 4, 5, 6, 7)

        with expected(IncorrectArgumentError):
            checkargs_explained('explanation', model_object.do_something, 1, '2', title='some title', style='style')


    @test(Fixture)
    def stubbable_is_instance(self, fixture):
        """Classes can be marked with a flag to let them pass the IsInstance or IsSubclass checks even
           though they do not inherit from the specified class."""
           
        class A(object):
            pass
            
        class B(object):
            is_A = True
            
        with expected(NoException):
            vassert( IsInstance(A).is_valid(B()) )
        with expected(NoException):
            vassert( IsSubclass(A).is_valid(B) )
    
    @test(Fixture)
    def checking_before_args_available(self, fixture):
        """When checking arguments before a method call, the checks for some arguments may be ignored by passing NotYetAvailable
           instances for them. The name of NotYetAvailable arguments should match the name of the argument it replaces."""
        class ModelObject(object):
            @arg_checks(y=IsInstance(int), title=IsInstance(six.string_types))
            def do_something(self, x, y, title='a title', style=None):
                pass
                
        model_object = ModelObject()
        with expected(NoException):
            checkargs(model_object.do_something, 'x', NotYetAvailable('y'), 'a title')
        with expected(IsInstance):
            checkargs(model_object.do_something, 'x', NotYetAvailable('y'), 123)

        with expected(IncorrectArgumentError):
            checkargs(model_object.do_something, 'x', NotYetAvailable('x'), 'a valid title')


