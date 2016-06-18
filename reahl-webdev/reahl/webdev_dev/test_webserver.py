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

from __future__ import print_function, unicode_literals, absolute_import, division
import six
import threading
from threading import Event
import subprocess
import sys
import os
import time
import atexit
import datetime
import functools

from reahl.tofu import test, Fixture
from reahl.tofu import vassert, expected
from reahl.tofu import temp_dir
from reahl.tofu import temp_file_with
from reahl.stubble import stubclass, CallMonitor, replaced, exempt, EmptyStub

from reahl.webdev.webserver import ServerSupervisor, SlaveProcess


@stubclass(SlaveProcess)
class SlaveProcessStartCounterStub(SlaveProcess):
    spawned = 0
    terminated = 0
    def __init__(self):
        super(SlaveProcessStartCounterStub, self).__init__(None, None)
    def start(self): self.spawned += 1
    def terminate(self, timeout=5): self.terminated += 1

    @exempt
    def started(self, count):
        return self.spawned == count and self.terminated == count-1

    @exempt
    def is_running(self):
        return self.spawned - self.terminated > 0


class SupervisorFixture(Fixture):
    def new_dir_to_watch(self):
        return temp_dir()

    def new_supervisor(self):
        supervisor = ServerSupervisor(EmptyStub(), 0, directories_to_monitor=[self.dir_to_watch.name])
        supervisor.serving_process = SlaveProcessStartCounterStub()
        return supervisor
        
    def start_supervisor(self):
        self.supervisor_thread = threading.Thread(target=self.supervisor.run)
        self.supervisor_thread.start()
        self.wait_for(functools.partial(self.supervisor.serving_process.started, count=1))
        
    def stop_supervisor(self):
        self.supervisor.stop()
        self.supervisor_thread.join()

    def change_a_file(self):
        some_file = self.dir_to_watch.file_with('watchme.py', '')
        with open(some_file.name, 'w') as file_in_watched_dir:
            file_in_watched_dir.write('some text')

    def wait_for(self, condition, poll_interval=0.3, timeout=4):
        start = datetime.datetime.now()
        def timed_out():
            return (datetime.datetime.now() - start) > datetime.timedelta(seconds=timeout)
            
        while not timed_out():
            if not condition() and timed_out():
                raise AssertionError('Timed out waiting for condition: %s' % condition)
            time.sleep(poll_interval)


@test(SupervisorFixture)
def server_supervisor_restarts_slave_when_files_changed(fixture):
    """The ServerSupervisor watches for changes to files, and restarts a web serving process when a file was changed."""

    vassert( not fixture.supervisor.serving_process.is_running() )

    fixture.start_supervisor()

    try:
        vassert( fixture.supervisor.serving_process.started(count=1) )
        vassert( fixture.supervisor.serving_process.is_running() )

        fixture.change_a_file()

        def restarted():
            return fixture.supervisor.serving_process.started(count=2) and fixture.supervisor.serving_process.is_running()
        fixture.wait_for(restarted)

    finally:
        fixture.stop_supervisor()
    
    vassert( not fixture.supervisor.serving_process.is_running() )


@stubclass(SlaveProcess)
class SlaveProcessRegisterOrphanStub(SlaveProcess):
    kill_orphan_callable = None
    def __init__(self):
        super(SlaveProcessRegisterOrphanStub, self).__init__(None, None)

    def spawn_new_process(self):
        return EmptyStub(pid=123)

    def register_orphan_killer(self, kill_function):
        self.kill_orphan_callable = kill_function



@test(Fixture)
def slave_process_registers_process_to_kill(fixture):
    """The SlaveProcess ensures that orphaned os processes started by it will be killed upon exit."""
    
    slave_process = SlaveProcessRegisterOrphanStub()
    vassert( not slave_process.kill_orphan_callable )
    slave_process.start()
    vassert( callable(slave_process.kill_orphan_callable) )



class ProcessFake(object):
    pid=0
    def terminate(self, timeout=5): pass
    def wait(self, timeout=0): pass
    def kill(self): pass


@stubclass(SlaveProcess)
class SlaveProcessStub(SlaveProcess):
    def __init__(self):
        super(SlaveProcessStub, self).__init__(None, None)

    def spawn_new_process(self):
        return ProcessFake()

    def register_orphan_killer(self, kill_function): pass


@test(Fixture)
def slave_process_terminates_then_waits(fixture):
    """When the SlaveProcess is terminated, it waits for the OS process to die before returning."""

    slave_process = SlaveProcessStub()
    slave_process.start()

    with CallMonitor(slave_process.process.wait) as wait_monitor:
        slave_process.terminate()
    vassert( wait_monitor.times_called == 1 )



@stubclass(SlaveProcess)
class SlaveProcessThatDoesNotReallyStart(SlaveProcess):
    def __init__(self):
        super(SlaveProcessThatDoesNotReallyStart, self).__init__(None, None)
    def start(self): pass


class ProcessThatTakesLongToDie(ProcessFake):
    pid=0
    time_to_take_to_die = 1.0
    killed = False
    def wait(self, timeout=0):
        if six.PY2:
            time.sleep(self.time_to_take_to_die)
        else: 
            raise subprocess.TimeoutExpired('fake', 123)
    def kill(self):
        self.killed = True


@test(Fixture)
def process_wait_timeout_reached_raises_exception(fixture):
    """If a SlaveProcess does not terminate successfully, it is forcibly killed."""
    
    slave_process = SlaveProcessThatDoesNotReallyStart()
    slave_process.process = ProcessThatTakesLongToDie()

    slave_process.start()
    short_time = slave_process.process.time_to_take_to_die/10
    
    vassert( not slave_process.process.killed )
    slave_process.terminate(short_time)
    vassert( slave_process.process.killed )


