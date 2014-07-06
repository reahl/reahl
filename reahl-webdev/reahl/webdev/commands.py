# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from six.moves import input

from reahl.dev.devdomain import Project
from reahl.dev.devshell import WorkspaceCommand

from reahl.webdev.webserver import ReahlWebServer

class ServeCurrentProject(WorkspaceCommand):
    """Serves the project in the current directory."""
    keyword = 'serve'

    options = [('-p', '--port', dict(action='store', dest='port', default=8000, help='port (optional)'))]

    def execute(self, options, args):
        project = Project.from_file(self.workspace, self.workspace.startup_directory)
        config_directory = 'etc'
        if args:
            config_directory = args[0]

        print('\nUsing config from %s\n' % config_directory)
            
        with project.paths_set():
            reahl_server = self.start_server(options, config_directory)

            print('\n\nServing http on port %s, https on port %s (config=%s)' % \
                                     (options.port, int(options.port)+363, config_directory))
            print('\nPress <Enter> to terminate\n\n')
    
            input()        
            reahl_server.stop()
        return 0


    def start_server(self, options, config_directory):  
        reahl_server = ReahlWebServer.fromConfigDirectory(config_directory, int(options.port))
        reahl_server.start(connect=True)
        return reahl_server
