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

import six

import platform
import sys
import os
import os.path
import re
import subprocess

import pkg_resources


from reahl.dev.devdomain import Project
from reahl.dev.devshell import WorkspaceCommand
from reahl.component.shelltools import Executable, Command
from reahl.component.exceptions import DomainException

from reahl.dev.exceptions import CouldNotConfigureServer
from reahl.webdev.webserver import ReahlWebServer, ServerSupervisor


class ServeCurrentProject(WorkspaceCommand):
    """Serves the project configured in the given directory (defaults to ./etc)."""
    keyword = 'serve'

    def assemble(self):
        super(ServeCurrentProject, self).assemble()
        self.parser.add_argument('-p', '--port', action='store', type=int, dest='port', default=8000, help='port (optional)')
        self.parser.add_argument('-s', '--seconds-between-restart', action='store', type=int, dest='max_seconds_between_restarts', 
                                 default=3, help='poll only every n seconds for filesystem changes (optional)')
        self.parser.add_argument('-d', '--monitor-directory', action='append', dest='monitored_directories', default=[],
                                 help='add a directory to monitor for changes'
                                 ' (the current directory is always included)')
        self.parser.add_argument('-D', '--dont-restart', action='store_false', dest='restart', default=True, 
                                 help='run as unsupervised server which does not monitor for filesystem changes')
        self.parser.add_argument('config_directory', default='etc', nargs='?',
                                 help='the configuration directory of the system to serve')

    def execute(self, args):
        project = Project.from_file(self.workspace, self.workspace.startup_directory)
        with project.paths_set():
            try:
                if args.restart:
                    ServerSupervisor(sys.argv[1:]+['--dont-restart'],
                                     args.max_seconds_between_restarts,
                                     ['.']+args.monitored_directories).run()
                else:
                    config_directory = args.config_directory
                    print('\nUsing config from %s\n' % config_directory)
                    
                    try:
                        reahl_server = ReahlWebServer.fromConfigDirectory(config_directory, args.port)
                    except pkg_resources.DistributionNotFound as ex:
                        terminate_keys = 'Ctrl+Break' if platform.system() == 'Windows' else 'Ctrl+C'
                        print('\nPress %s to terminate\n\n' % terminate_keys)
                        raise CouldNotConfigureServer(ex)

                    reahl_server.start(connect=True)
                    print('\n\nServing http on port %s, https on port %s (config=%s)' % \
                                     (args.port, args.port+363, config_directory))
                    terminate_keys = 'Ctrl+Break' if platform.system() == 'Windows' else 'Ctrl+C'
                    print('\nPress %s to terminate\n\n' % terminate_keys)

                    notify = Executable('notify-send')
                    try:
                        notify.call(['Reahl', 'Server restarted'])
                    except:
                        pass

                    reahl_server.wait_for_server_to_complete()
            except KeyboardInterrupt:
                print('\nShutting down')
            except CouldNotConfigureServer as ex:
                print(ex)
        return 0


class SyncFiles(Command):
    """Uses the sitecopy program to upload / sync static files to a remote webserver."""
    keyword = 'syncfiles'

    def get_site_name(self):
        if not os.path.isfile('sitecopy.rc'):
            raise DomainException(message='Could not find a sitecopy config file "sitecopy.rc" in the current directory')
        with open('sitecopy.rc') as config_file:
            for line in config_file:
                match = re.match('.*(?!#).*site\s+(\S+)', line)
                if match:
                    return match.group(1)
        raise DomainException(message='Cannot find the site name in sitecopy.rc')

    
    def assemble(self):
        self.parser.add_argument('-f', '--fetch-first', action='store_true', dest='fetch_first',
                                 help='first fetch data from the site to ensure we are in sync')
        self.parser.add_argument('site_name', default=None, nargs='?',
                                 help='the name of the site as listed in sitecopy.rc')

    def execute(self, args):
        super(SyncFiles, self).execute(args)
        self.sitecopy = Executable('sitecopy')

        try:
            site_name = args.site_name or self.get_site_name()
            local_info_file = os.path.expanduser(os.path.join('~', '.sitecopy', site_name))
            if args.fetch_first or not os.path.exists(local_info_file):
                if os.path.exists(local_info_file):
                    os.remove(local_info_file)
                self.sitecopy.check_call('-r sitecopy.rc --fetch'.split()+[site_name])
            self.sitecopy.check_call('-r sitecopy.rc --update'.split()+[site_name])
        except subprocess.CalledProcessError as ex:
            raise DomainException(message='Running "%s" failed with exit code %s' % (' '.join(ex.cmd), ex.returncode))
