# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import six
import threading
from threading import Event
import sys
import time

from reahl.tofu import test, Fixture
from reahl.tofu import vassert, expected
from reahl.tofu import temp_dir
from reahl.tofu import temp_file_with
from reahl.stubble import stubclass, CallMonitor

from reahl.webdev.webserver import ServerSupervisor, SlaveProcess

"""

ServeCurrentProject
- restart when directory changes are detected option
or standalone.

Slaveprocess
- can spawn from the current process ['--dont-restart'] is added as option to slave
- will ensure no orphans at exit
- restart waits for previous process to die before spawning another one

ServerSupervisor
ALMOST DONE restart once when py files change (not also when pyc arrives)
- does not restart when directories change
-
"""


class SupervisorThread(threading.Thread):
    def __init__(self, supervisor):
        threading.Thread.__init__(self)
        self.supervisor = supervisor

    def run(self):
        def check_exception(ex):
            vassert( 'Requested to stop monitoring filesystem changes' in six.text_type(ex) )
        with expected(Exception, test=check_exception):
            self.supervisor.run()


@test(Fixture)
def server_supervisor_monitors_directory_changes(fixture):

    dir_to_watch = temp_dir()
    some_file = dir_to_watch.file_with('watchme.py', '')

    terminate_called = Event()
    class ProcessFake(object):
        pid=0
        def terminate(self):
            terminate_called.set()
        def wait(self): pass
        def was_spawned(self): pass
    process_fake = ProcessFake()

    @stubclass(SlaveProcess)
    class SlaveProcessStub(SlaveProcess):
        def spawn_new_process(self):
            process_fake.was_spawned()
            return process_fake
        def kill_on_exit_if_abandoned(self): pass

    def change_watched_file():
        with open(some_file.name, 'w') as watched_file:
            watched_file.write('some text')

    seconds_to_check_watched_files = 1
    supervisor = ServerSupervisor(directories_to_monitor=[dir_to_watch.name],
                                  slave_process_class=SlaveProcessStub,
                                  min_seconds_between_restarts=seconds_to_check_watched_files)


    with CallMonitor(process_fake.terminate) as terminate_monitor,\
        CallMonitor(process_fake.was_spawned) as spawned_monitor:

        thread = SupervisorThread(supervisor)
        thread.start()
        time.sleep(seconds_to_check_watched_files*2)#grant directory monitor a chance to scan the contents

        change_watched_file()

        terminate_called.wait()
        supervisor.stop_supervising.set()

        thread.join()

    vassert( spawned_monitor.times_called == 2 )
    vassert( terminate_monitor.times_called == 2 )
