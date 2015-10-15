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
import platform
import sys

import pkg_resources


from reahl.dev.devdomain import Project
from reahl.dev.devshell import WorkspaceCommand

from reahl.webdev.webserver import ReahlWebServer, ServerSupervisor, CouldNotConfigureServer


class ServeCurrentProject(WorkspaceCommand):
    """Serves the project configured in the given directory (defaults to ./etc)."""
    keyword = 'serve'

    options = [('-p', '--port', dict(action='store', type='int', dest='port', default=8000, help='port (optional)')),
               ('-s', '--seconds-between-restart', dict(action='store', type='int', dest='max_seconds_between_restarts', 
                                                        default=3, 
                                                        help='poll only every n seconds for filesystem changes (optional)')),
               ('-d', '--monitor-directory', dict(action='append', dest='monitored_directories', default=[],
                                                 help='add a directory to monitor for changes'
                                                 ' (the current directory is always included)')),
               ('-D', '--dont-restart', dict(action='store_false', dest='restart', default=True, 
                                             help='run as unsupervised server which does not monitor for filesystem changes'))]

    def execute(self, options, args):
        project = Project.from_file(self.workspace, self.workspace.startup_directory)
        with project.paths_set():
            try:
                if options.restart:
                    ServerSupervisor(sys.argv[1:]+['--dont-restart'],
                                     options.max_seconds_between_restarts,
                                     ['.']+options.monitored_directories).run()
                else:
                    config_directory = 'etc'
                    if args:
                        config_directory = args[0]

                    print('\nUsing config from %s\n' % config_directory)
                    
                    try:
                        reahl_server = ReahlWebServer.fromConfigDirectory(config_directory, options.port)
                    except pkg_resources.DistributionNotFound as ex:
                        terminate_keys = 'Ctrl+Break' if platform.system() == 'Windows' else 'Ctrl+C'
                        print('\nPress %s to terminate\n\n' % terminate_keys)
                        raise CouldNotConfigureServer(ex)

                    reahl_server.start(connect=True)
                    print('\n\nServing http on port %s, https on port %s (config=%s)' % \
                                     (options.port, options.port+363, config_directory))
                    terminate_keys = 'Ctrl+Break' if platform.system() == 'Windows' else 'Ctrl+C'
                    print('\nPress %s to terminate\n\n' % terminate_keys)

                    reahl_server.wait_for_server_to_complete()
            except KeyboardInterrupt:
                print('\nShutting down')
            except CouldNotConfigureServer as ex:
                print(ex)
        return 0



