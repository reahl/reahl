# Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import six

import os
import sys

import pkg_resources


from reahl.dev.devdomain import Project
from reahl.dev.devshell import WorkspaceCommand

from reahl.webdev.webserver import ReahlWebServer, ServerSupervisor




class ServeCurrentProject(WorkspaceCommand):
    """Serves the project configures in the ./etc directory or the directory given as an arg."""
    keyword = 'serve'

    options = [('-p', '--port', dict(action='store', dest='port', default=8000, help='port (optional)')),
               ('-D', '--dont-restart', dict(action='store_false', dest='restart', default=True, help='don\'t restart the server when file changes are detected'))]

    def execute(self, options, args):
        project = Project.from_file(self.workspace, self.workspace.startup_directory)
        with project.paths_set():
            if options.restart:
                try:
                    ServerSupervisor().run()
                except KeyboardInterrupt:
                    print('\nShutting down')
            else:
                config_directory = 'etc'
                if args:
                    config_directory = args[0]

                print('\nUsing config from %s\n' % config_directory)

                reahl_server = ReahlWebServer.fromConfigDirectory(config_directory, int(options.port))
                reahl_server.start(connect=True)
                print('\n\nServing http on port %s, https on port %s (config=%s)' % \
                                 (options.port, int(options.port)+363, config_directory))
                print('\nPress Ctrl+C (*nix) or Ctrl+Break (Windows) to terminate\n\n')
                reahl_server.wait_for_server_to_complete()

        return 0



