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
from reahl.stubble import stubclass, CallMonitor, replaced, exempt

from reahl.webdev.webserver import ServerSupervisor, SlaveProcess, PythonScriptCommand, ProcessWaitPatch, TimeoutExpired

"""

ServeCurrentProject
- restart when directory changes are detected option
or standalone.

Slaveprocess
- can spawn from the current process ['--dont-restart'] is added as option to slave
- will ensure no orphans at exit (use stubble with_replaced(atexit.register)
- restart waits for previous process to die before spawning another one

ServerSupervisor
- restart once when py files change (not also when pyc arrives)
- does not restart when directories change
-
"""


class SupervisorThread(threading.Thread):
    def __init__(self, supervisor):
        threading.Thread.__init__(self)
        self.supervisor = supervisor
        self.start()

    def run(self):
        self.supervisor.run()

    def stop(self):
        self.supervisor.stop()
        self.join()


@stubclass(SlaveProcess)
class SlaveProcessStartCounterStub(SlaveProcess):
    spawned = 0
    terminated = 0
    def spawn(self): self.spawned += 1
    def terminate(self): self.terminated += 1
    def register_orphan_killer(self, kill_function): pass

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
        supervisor = ServerSupervisor(directories_to_monitor=[self.dir_to_watch.name], min_seconds_between_restarts=0)
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
    def spawn_new_process(self):
        class ProcessFake(object):
            pid=0
            def terminate(self): pass
            def wait(self, timeout=0): pass
            def kill(self): raise Exception('please don\'t kill me')
        return ProcessFake()

    def register_orphan_killer(self, kill_function):
        self.kill_orphan_callable = kill_function

    @exempt
    def started(self, count):
        return True


class SupervisorKillProcessFixture(SupervisorFixture):
    def new_supervisor(self):
        supervisor = super(SupervisorKillProcessFixture, self).new_supervisor()
        supervisor.serving_process = SlaveProcessRegisterOrphanStub()
        return supervisor


@test(SupervisorKillProcessFixture)
def slave_process_registers_process_to_kill(fixture):

    fixture.start_supervisor()
    orphan_kill_method = fixture.supervisor.serving_process.kill_orphan_callable
    fixture.stop_supervisor()

    def check_exception(ex):
        vassert( 'please don\'t kill me' in six.text_type(ex) )

    with expected(Exception, test=check_exception):
        orphan_kill_method()


class ProcessFake(object):
    pid=0
    def terminate(self): pass
    def wait(self, timeout=0): pass
    def kill(self): pass


@stubclass(SlaveProcess)
class SlaveProcessStub(SlaveProcess):
    def spawn_new_process(self):
        return ProcessFake()

    def register_orphan_killer(self, kill_function): pass


@test(Fixture)
def slave_process_terminates_then_waits(fixture):

    slave_process = SlaveProcessStub()
    slave_process.spawn()


    with CallMonitor(slave_process.process.terminate) as terminate_monitor,\
         CallMonitor(slave_process.process.wait) as wait_monitor:
        slave_process.terminate()
    vassert( terminate_monitor.times_called == 1 )
    vassert( wait_monitor.times_called == 1 )


@test(Fixture)
def python_script_command_properties(fixture):

    script_command = PythonScriptCommand(spawn_args=['--dont_restart'])

    def typical_sys_argv():
        return ['reahl', 'serve', '--some_arg']

    with replaced(script_command.get_system_arguments, typical_sys_argv):
        popen_args = script_command.popen_args_to_spawn

    vassert(  len(popen_args) == 5 )

    split_of_python_interpreter_path = popen_args[0].split(os.path.sep)
    vassert(  len(split_of_python_interpreter_path) > 0 )
    vassert(  'python' in split_of_python_interpreter_path[-1] )

    split_of_script_full_path = popen_args[1].split(os.path.sep)
    vassert(  len(split_of_script_full_path) > 0 )
    vassert(  'reahl' in split_of_script_full_path[-1] )

    vassert( popen_args[2] ==  'serve' )
    vassert( popen_args[3] ==  '--some_arg' )
    vassert( popen_args[4] ==  '--dont_restart' )


class ProcessWaitTimeoutFake(ProcessFake):
    pid=0
    long_timeout = 1.0
    def wait(self, timeout=0): time.sleep(self.long_timeout)


@test(Fixture)
def process_wait_timeout_reached_raises_exception(fixture):

    process = ProcessWaitTimeoutFake()
    short_timeout = ProcessWaitTimeoutFake.long_timeout/10.0

    with ProcessWaitPatch(process, timeout=short_timeout):
        with expected(TimeoutExpired):
            process.wait()


class PopenStub(object):
    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return ProcessFake()

    def __enter__(self):
        self.original_popen = subprocess.Popen
        subprocess.Popen = self
        return self

    def __exit__(self, exception_type, value, traceback):
        subprocess.Popen = self.original_popen


@test(SupervisorFixture)
def slave_process_calls_popen_with_correct_args(fixture):

    supervisor = ServerSupervisor(directories_to_monitor=[], min_seconds_between_restarts=0, spawn_args=['some_args'])
    thread = threading.Thread(target=supervisor.run)
    try:
        with PopenStub() as popen_stub:
            thread.start()
    finally:
        supervisor.stop()

    expected_script_command = PythonScriptCommand(spawn_args=['some_args'])

    vassert( set(popen_stub.args[0]) == set(expected_script_command.popen_args_to_spawn) )
    vassert( popen_stub.kwargs['env'] == os.environ )