# Copyright 2013-2023 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.



from packaging.requirements import Requirement

from reahl.tofu import expected, NoException
from reahl.stubble import EasterEgg

from reahl.component.eggs import ReahlEgg, DistributionCache


def distribution_name(distribution):
    """Return the canonical distribution name via importlib.metadata."""
    return distribution.metadata['Name'].lower()


def dependency_names(distribution):
    """Return dependency names using the production resolver."""
    dependencies = ReahlEgg.find_dependencies(distribution)
    return [distribution_name(dep) for dep in dependencies]


def test_flattened_tree_of_eggs():
    """A Reahl application consists of a root egg and all its egg dependencies - with all such components
       often regarded in flattened order of dependence."""
    DistributionCache.clear_cache()
    ReahlEgg.clear_cache()
    
    egg = EasterEgg(name='test')
    with egg.installed():
        egg.add_dependency('reahl-component')

        # All eggs for a root egg can be found in dependency order
        components_in_order = ReahlEgg.compute_ordered_dependent_distributions(egg.as_requirement_string(), [])
        component_names_in_order = [distribution_name(i) for i in components_in_order]
        # (many valid topological sorts are possible and the algorithm is nondeterministic in some aspects that
        #  do not matter, hence many possible valid orderings are possible for this dependency tree)
        #  We assert here only what matters, else this test becomes a flipper:
        def is_ordered_before(higher, lower):
            return component_names_in_order.index(higher) < component_names_in_order.index(lower)

        assert component_names_in_order[:2] == [distribution_name(egg), 'reahl-component']

        components_by_name = dict(zip(component_names_in_order, components_in_order))

        for package_name, distribution in components_by_name.items():
            dependencies = [name for name in dependency_names(distribution) if name != package_name]
            assert all(is_ordered_before(package_name, dependency_name) for dependency_name in dependencies)


def test_interface_with_meta_info():
    """A Reahl component can publish a ReahlEgg instance to supply extra meta information about itself.
       Such interfaces with extra information are also often used from a flattened list in dependency order."""
    DistributionCache.clear_cache()
    ReahlEgg.clear_cache()

    egg = EasterEgg(name='test')
    with egg.installed():
        egg.add_dependency('reahl-component')

        # An egg is a component if it has reahl-component.tom metadata
        egg.stubbed_metadata['reahl-component.toml'] = 'metadata_version = "1.0.0"'

        # Interfaces can be queried in dependency order too
        interfaces_in_order = ReahlEgg.compute_all_relevant_interfaces(egg.as_requirement_string(), [])
        assert len(interfaces_in_order) == 2   # That of reahl-component itself, and of the easteregg
        [interface] = [i for i in interfaces_in_order if i.distribution is egg]

        # The meta-info that can be obtained via such an interface
        assert interface.configuration_spec is None

        assert interface.get_persisted_classes_in_order() == []

        egg.stubbed_metadata['reahl-component.toml'] = '''
        metadata_version = "1.0.0"
        [versions."1.0"]
        '''

        versions = interface.get_versions()
        assert versions[-1] == interface.installed_version

        egg.stubbed_metadata['reahl-component.toml'] = '''
        metadata_version = "1.0.0"
        translations = "reahl.messages"
        '''
        egg.add_entry_point_from_line('reahl.translations', '%s = reahl.messages' % egg.project_name)
        assert interface.translation_package_name == 'reahl.messages'
        assert interface.translation_package_entry_point.name == 'test'
        assert interface.translation_package_entry_point.module == 'reahl.messages'

        # Hooks for allowing a component to do its own housekeeping
        with expected(NoException):
            interface.do_daily_maintenance()


def xxx_test_all_relevant_interfaces_includes_transitive_dependencies():
    """get_all_relevant_interfaces should recursively find all transitive dependencies."""
    from reahl.stubble import EasterEgg

    # Create a dependency chain: root -> pkg_a -> pkg_b -> reahl-component
    # This tests that transitive dependencies (pkg_b) are found even though
    # root doesn't directly depend on it

    pkg_b = EasterEgg(name='pkg-b')
    pkg_b.add_dependency('reahl-component')
    pkg_b.stubbed_metadata['reahl-component.toml'] = 'metadata_version = "1.0.0"'

    pkg_a = EasterEgg(name='pkg-a')
    pkg_a.add_dependency('pkg-b')
    pkg_a.stubbed_metadata['reahl-component.toml'] = 'metadata_version = "1.0.0"'

    root = EasterEgg(name='root-pkg')
    root.add_dependency('pkg-a')
    root.stubbed_metadata['reahl-component.toml'] = 'metadata_version = "1.0.0"'

    with pkg_b.installed(), pkg_a.installed(), root.installed():
        # Get all interfaces - should include entire dependency tree
        interfaces = ReahlEgg.get_all_relevant_interfaces(root.as_requirement_string(), [])
        interface_names = [i.name for i in interfaces]

        # Verify all packages in the chain are found
        assert 'root-pkg' in interface_names, "Root package should be in interfaces"
        assert 'pkg-a' in interface_names, "Direct dependency should be in interfaces"
        assert 'pkg-b' in interface_names, "Transitive dependency should be in interfaces"
        assert 'reahl-component' in interface_names, "Base component should be in interfaces"

        # Verify we found at least these 4 packages (there may be more from reahl-component's deps)
        assert len(interfaces) >= 4, f"Expected at least 4 interfaces, got {len(interfaces)}"


def test_compute_ordered_dependent_distributions_finds_transitive_dependencies_via_modern_api():
    """Verify modern API correctly finds all transitive dependencies."""
    DistributionCache.clear_cache()
    ReahlEgg.clear_cache()
    
    # Get all distributions for reahl-component
    component_distributions = list(ReahlEgg.compute_ordered_dependent_distributions('reahl-component', []))
    component_names = {d.name.lower() if hasattr(d, 'name') else d.project_name.lower() 
                      for d in component_distributions}
    
    # Get all distributions for reahl-tofu (which depends on reahl-component)
    tofu_distributions = list(ReahlEgg.compute_ordered_dependent_distributions('reahl-tofu', []))
    tofu_names = {d.name.lower() if hasattr(d, 'name') else d.project_name.lower() 
                 for d in tofu_distributions}
    
    # reahl-tofu depends on reahl-component, so all of reahl-component's dependencies
    # should also be in reahl-tofu's dependency list (proving transitive resolution works)
    assert component_names.issubset(tofu_names), \
        f"reahl-tofu should include all reahl-component dependencies. Missing: {component_names - tofu_names}"
    
    # reahl-tofu should have MORE distributions than just reahl-component's
    # (at minimum: reahl-component's deps + reahl-tofu itself)
    assert len(tofu_distributions) > len(component_distributions), \
        f"reahl-tofu should have more distributions than reahl-component alone"
    
    # Verify reahl-tofu itself is in its list
    assert 'reahl-tofu' in tofu_names or 'reahl_tofu' in tofu_names

