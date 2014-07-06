# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from reahl.tofu import  test, Fixture
from reahl.tofu  import vassert, expected, NoException
from reahl.stubble import easter_egg, EmptyStub

from reahl.component.eggs import ReahlEgg


@istest
class ComponentTests(object):
    @test(Fixture)
    def flattened_tree_of_eggs(self, fixture):
        """A Reahl application consists of a root egg and all its egg dependencies - with all such components
           often regarded in flattened order of dependence."""
        easter_egg.clear()
        easter_egg.add_dependency('reahl-component')
        
        # All eggs for a root egg can be found in dependency order
        components_in_order = ReahlEgg.compute_ordered_dependent_distributions(easter_egg.as_requirement_string())
        component_names_in_order = [i.project_name for i in components_in_order]
        vassert( component_names_in_order == [easter_egg.project_name, 'reahl-component', 'decorator', 'python-dateutil', 'Babel', 'six'] )

    @test(Fixture)
    def interface_with_meta_info(self, fixture):
        """A Reahl component can publish a ReahlEgg instance to supply extra meta information about itself.
           Such interfaces with extra information are also often used from a flattened list in dependency order."""
        
        easter_egg.clear()
        easter_egg.add_dependency('reahl-component')
        
        # The interface for a component is published via the reahl.eggs entry point
        line = 'Egg = reahl.component.eggs:ReahlEgg'
        easter_egg.add_entry_point_from_line('reahl.eggs', line)
        
        # Interfaces can be queried in dependency order too
        interfaces_in_order = ReahlEgg.compute_all_relevant_interfaces(easter_egg.as_requirement_string())
        vassert( len(interfaces_in_order) == 2 )  # That of reahl-component itself, and of the easteregg
        [interface] = [i for i in interfaces_in_order if i.distribution is easter_egg]

        # The meta-info that can be obtained via such an interface
        vassert( interface.configuration_spec is None )

        orm_control = EmptyStub()
        vassert( interface.get_persisted_classes_in_order(orm_control) == [] )
        vassert( interface.migrations_in_order == [] )
        vassert( interface.get_roles_to_add() == [] )

        # Hooks for allowing a component to do its own housekeeping
        with expected(NoException):
            interface.do_daily_maintenance() 













