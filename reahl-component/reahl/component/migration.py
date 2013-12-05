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

"""Support for database schema migration."""

from pkg_resources import parse_version

from reahl.component.exceptions import ProgrammerError

class Migration(object):
    """Represents one logical change that can be made to an existing database schema.
    
       You should extend this class to build your own domain-specific database schema migrations. Set the
       `version` class attribute to a string containing the version of your component for which this Migration
       should be run when upgrading from a previous version.
       
       Never use code imported from your component in a Migration, since Migration code is kept around in
       future versions of a component and may be run to migrate a schema with different versions of your component.
    """
    version = None
    @classmethod
    def is_applicable(cls, current_schema_version, new_version):
        if not cls.version:
            raise ProgrammerError(u'Migration %s does not have a version set' % cls)
        return parse_version(cls.version) > parse_version(current_schema_version) and \
               parse_version(cls.version) <= parse_version(new_version)

    def run_phase(self, phase):
        if phase == 1:
            self.upgrade()
        else:
            self.upgrade_cleanup()

    def upgrade(self):
        """Override this method in a subclass in order to supply custom logic for changing the database schema. This
           method will be called for each of the applicable Migrations listed for all components, in reverse order of 
           dependency of components (less dependent components first).
        """
        pass
    def upgrade_cleanup(self):
        """Override this method in a subclass in order to supply custom logic that needs to run after the `.upgrade` method
           has been run for all Migrations of all components in an application. This
           method will be called for each of the applicable Migrations listed for all components, in normal order of 
           dependency of components (most dependent components first).
        """
        pass

