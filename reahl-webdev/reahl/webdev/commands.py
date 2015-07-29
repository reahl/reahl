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

import time
from six.moves.queue import Queue
from functools import partial

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from reahl.dev.devdomain import Project
from reahl.dev.devshell import WorkspaceCommand

from reahl.webdev.webserver import ReahlWebServer


class FilesChangedMonitor(FileSystemEventHandler):
    def __init__(self, directory_to_monitor):
        self.observer = Observer()
        self.observer.schedule(self, directory_to_monitor, recursive=True)
        self.observer.start()

        self.filesystem_changed_queue = Queue()

    def on_any_event(self, event):
        self.filesystem_changed_queue.put(event.src_path)

    def has_changes(self):
        return not self.filesystem_changed_queue.empty()

    def discard_changes(self):
        while not self.filesystem_changed_queue.empty():
            try:
                self.filesystem_changed_queue.get()
            except Empty:
                continue
            self.filesystem_changed_queue.task_done()

    def shutdown(self):
        self.observer.stop()
        self.observer.join()


class ServeCurrentProject(WorkspaceCommand):
    """Serves the project configures in the ./etc directory or the directory given as an arg."""
    keyword = 'serve'

    options = [('-p', '--port', dict(action='store', dest='port', default=8000, help='port (optional)'))]

    def execute(self, options, args):
        project = Project.from_file(self.workspace, self.workspace.startup_directory)
        config_directory = 'etc'
        if args:
            config_directory = args[0]

        print('\nUsing config from %s\n' % config_directory)

        current_directory = '.'
        with project.paths_set():

            files_changed_monitor = FilesChangedMonitor('.')

            server_start_command = partial(self.start_server, options, config_directory)
            reahl_server = server_start_command()

            check_for_file_changes_in_seconds = 5
            try:
                while True:
                    time.sleep(check_for_file_changes_in_seconds)
                    if files_changed_monitor.has_changes():
                        print('\nChanges to filesystem detected, scheduling a restart...\n')
                        reahl_server.stop()

                        files_changed_monitor.discard_changes()

                        reahl_server = server_start_command()

            except KeyboardInterrupt:
                print('\nShutting down...\n')
            files_changed_monitor.shutdown()
            reahl_server.stop()
        return 0

    def start_server(self, options, config_directory):
        reahl_server = ReahlWebServer.fromConfigDirectory(config_directory, int(options.port))
        reahl_server.start(connect=True)
        print('\n\nServing http on port %s, https on port %s (config=%s)' % \
                                 (options.port, int(options.port)+363, config_directory))
        print('\nPress Ctrl+C (*nix) or Ctrl+Break (Windows) to terminate\n\n')
        return reahl_server