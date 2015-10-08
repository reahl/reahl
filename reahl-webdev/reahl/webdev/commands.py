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
    """Serves the project configured in the relative etc directory or the directory given as an arg."""
    keyword = 'serve'

    dont_restart_option = '--dont-restart'
    options = [('-p', '--port', dict(action='store', type='int', dest='port', default=8000, help='port (optional)')),
               ('-s', '--seconds-between-restart', dict(action='store', type='int',  dest='max_seconds_between_restarts', default=3, help='restart after n seconds if there were filesystem changes (optional)')),
               ('-D', dont_restart_option, dict(action='store_false', dest='restart', default=True, help='don\'t restart the server when file changes are detected'))]

    def execute(self, options, args):
        project = Project.from_file(self.workspace, self.workspace.startup_directory)
        with project.paths_set():
            try:
                if options.restart:
                    ServerSupervisor(sys.argv[1:]+[self.dont_restart_option],
                                     options.max_seconds_between_restarts).run()
                else:
                    config_directory = 'etc'
                    if args:
                        config_directory = args[0]

                    print('\nUsing config from %s\n' % config_directory)

                    reahl_server = ReahlWebServer.fromConfigDirectory(config_directory, options.port)
                    reahl_server.start(connect=True)
                    print('\n\nServing http on port %s, https on port %s (config=%s)' % \
                                     (options.port, options.port+363, config_directory))
                    print('\nPress Ctrl+C (*nix) or Ctrl+Break (Windows) to terminate\n\n')
                    reahl_server.wait_for_server_to_complete()
            except KeyboardInterrupt:
                print('\nShutting down')
        return 0



