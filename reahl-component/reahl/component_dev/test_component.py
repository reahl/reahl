# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.tofu import expected, NoException
from reahl.stubble import easter_egg, EmptyStub

from reahl.component.eggs import ReahlEgg


def test_flattened_tree_of_eggs():
    """A Reahl application consists of a root egg and all its egg dependencies - with all such components
       often regarded in flattened order of dependence."""
    easter_egg.clear()
    easter_egg.add_dependency('reahl-component')

    # All eggs for a root egg can be found in dependency order
    components_in_order = ReahlEgg.compute_ordered_dependent_distributions(easter_egg.as_requirement_string())
    component_names_in_order = [i.project_name for i in components_in_order]
    # (many valid topological sorts are possible and the algorithm is nondeterministic in some aspects that
    #  do not matter, hence many possible valid orderings are possible for this dependency tree)
    #  We assert here only what matters, else this test becomes a flipper:
    def is_ordered_before(higher, lower):
        return component_names_in_order.index(higher) < component_names_in_order.index(lower)

    assert component_names_in_order[:2] == [easter_egg.project_name, 'reahl-component']
    assert is_ordered_before('Babel', 'pytz')
    assert is_ordered_before('python-dateutil', 'six')


def test_interface_with_meta_info():
    """A Reahl component can publish a ReahlEgg instance to supply extra meta information about itself.
       Such interfaces with extra information are also often used from a flattened list in dependency order."""

    easter_egg.clear()
    easter_egg.add_dependency('reahl-component')

    # The interface for a component is published via the reahl.eggs entry point
    line = 'Egg = reahl.component.eggs:ReahlEgg'
    easter_egg.add_entry_point_from_line('reahl.eggs', line)

    # Interfaces can be queried in dependency order too
    interfaces_in_order = ReahlEgg.compute_all_relevant_interfaces(easter_egg.as_requirement_string())
    assert len(interfaces_in_order) == 2   # That of reahl-component itself, and of the easteregg
    [interface] = [i for i in interfaces_in_order if i.distribution is easter_egg]

    # The meta-info that can be obtained via such an interface
    assert interface.configuration_spec is None

    assert interface.get_persisted_classes_in_order() == []
    assert interface.migrations_in_order == []

    # Hooks for allowing a component to do its own housekeeping
    with expected(NoException):
        interface.do_daily_maintenance()


