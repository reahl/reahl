# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from reahl.tofu import  Fixture, test, scenario
from reahl.tofu import expected, NoException, vassert

from reahl.component.modelinterface import secured, AdaptedMethod
from reahl.component.exceptions import AccessRestricted, ProgrammerError




@istest
class AccessControlTests(object):
    @test(Fixture)
    def methods_can_be_secured_basics(self, fixture):
        """A secured method can only be called if it can be read and written."""
        
        class ModelObject(object):
            did_something = False
            
            def always_allow(self): return True
            def always_deny(self): return False
            
            @secured( read_check=always_deny, write_check=always_allow )
            def do_something_write_only(self):
                self.did_something = True

            @secured( read_check=always_allow, write_check=always_deny )
            def do_something_read_only(self):
                self.did_something = True

            @secured( read_check=always_allow, write_check=always_allow )
            def do_something_read_and_write(self):
                self.did_something = True


        model_object = ModelObject()
        
        # Case: access not allowed
        model_object.did_something = False
        with expected(AccessRestricted):
            model_object.do_something_write_only()
        vassert( not model_object.did_something )

        model_object.did_something = False
        with expected(AccessRestricted):
            model_object.do_something_read_only()
        vassert( not model_object.did_something )

        # Case: access allowed
        model_object.did_something = False
        with expected(NoException):
            model_object.do_something_read_and_write()
        vassert( model_object.did_something )


    @test(Fixture)
    def checks_must_match_signature(self, fixture):
        """The same arguments passed to the protected method are also passed to its check methods."""
        
        expected_arg = 'expected arg'
        expected_kwarg = 'expected kwarg'

        class ModelObject(object):
            def read_check(self, arg, kwarg=None): 
                self.saved_arg_in_read_check = arg
                self.saved_kwarg_in_read_check = kwarg
                return True
                
            def write_check(self, arg, kwarg=None): 
                self.saved_arg_in_write_check = arg
                self.saved_kwarg_in_write_check = kwarg
                return True
            
            @secured( read_check=read_check, write_check=write_check )
            def do_something_with_arguments(self, arg, kwarg=None):
                self.saved_arg = arg
                self.saved_kwarg = kwarg


        model_object = ModelObject()

        # Case where arguments match
        model_object.do_something_with_arguments(expected_arg, kwarg=expected_kwarg)
        vassert( model_object.saved_arg_in_read_check is expected_arg )
        vassert( model_object.saved_kwarg_in_read_check is expected_kwarg )
        vassert( model_object.saved_arg_in_write_check is expected_arg )
        vassert( model_object.saved_kwarg_in_write_check is expected_kwarg )
        vassert( model_object.saved_arg is expected_arg )
        vassert( model_object.saved_kwarg is expected_kwarg )


    class Scenarios(Fixture):
        def check_with_no_args(self): return True
        def check_without_kwarg(self, arg): return True
        def check_without_arg(self, kwarg=None): return True
        def check_with_valid_signature(self, arg, kwarg=None): return True
        
        @scenario
        def read_check_differs_in_args(self):
            self.read_check = self.check_without_arg
            self.write_check = self.check_with_valid_signature
            
        @scenario
        def read_check_differs_in_kwargs(self):
            self.read_check = self.check_without_kwarg
            self.write_check = self.check_with_valid_signature

        @scenario
        def write_check_differs_in_args(self):
            self.read_check = self.check_with_valid_signature
            self.write_check = self.check_without_arg
            
        @scenario
        def write_check_differs_in_kwargs(self):
            self.read_check = self.check_with_valid_signature
            self.write_check = self.check_without_kwarg
            
            
    @test(Scenarios)
    def exception_on_mismatch_of_signature(self, fixture):
        """When the signatures of check methods do not match, an exception is raised."""

        with expected(ProgrammerError):
            class ModelObject(object):
                @secured( read_check=fixture.read_check, write_check=fixture.write_check )
                def do_something_with_arguments(self, arg, kwarg=None):
                    pass


    @test(Fixture)
    def adapted_methods(self, fixture):
        """When check methods do not match the signature of the protected method, an
           AdaptedMethod can be used to adapt them to the signature of the protected method."""
        
        expected_arg = 'expected arg'
        expected_kwarg = 'expected kwarg'

        class ModelObject(object):
            def read_check(self, an_arg, a_kwarg=None): 
                self.saved_arg_in_read_check = an_arg
                self.saved_kwarg_in_read_check = a_kwarg
                return True
                
            def write_check(self, also_an_arg, also_a_kwarg=None): 
                self.saved_arg_in_write_check = also_an_arg
                self.saved_kwarg_in_write_check = also_a_kwarg
                return True
            
            @secured( read_check=AdaptedMethod(read_check, ['self', 'arg'], dict(a_kwarg='kwarg')),
                      write_check=AdaptedMethod(write_check, ['self', 'arg'], dict(also_a_kwarg='kwarg')) )
            def do_something_with_arguments(self, arg, ignored_arg, kwarg=None, ignored_kwarg=None):
                self.saved_arg = arg
                self.saved_kwarg = kwarg


        model_object = ModelObject()

        # Case where arguments match
        model_object.do_something_with_arguments(expected_arg, 'ignored_arg',
                                                  kwarg=expected_kwarg, ignored_kwarg='ignored_kwarg')
        vassert( model_object.saved_arg_in_read_check is expected_arg )
        vassert( model_object.saved_kwarg_in_read_check is expected_kwarg )
        vassert( model_object.saved_arg_in_write_check is expected_arg )
        vassert( model_object.saved_kwarg_in_write_check is expected_kwarg )
        vassert( model_object.saved_arg is expected_arg )
        vassert( model_object.saved_kwarg is expected_kwarg )












