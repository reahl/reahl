import contextlib
import sys
import textwrap
import shlex

import pytest
from reahl.workstation.xprasupport import ControlXpra, Xpra
from reahl.component.shelltools import Executable
from reahl.stubble import stubclass, exempt, replaced
from reahl.tofu import Fixture, scenario
from reahl.tofu.pytestsupport import with_fixtures


class MonitoredInvocation(object):
    def __init__(self, method, commandline_arguments, args, kwargs):
        self.method = method
        self.commandline_arguments = commandline_arguments
        self.args = args
        self.kwargs = kwargs

    @property
    def argv(self):
        return self.commandline_arguments


@stubclass(Executable)
class ExecutableStub(Executable):
    def __init__(self, name='fake executable', stdout=''):
        super(ExecutableStub, self).__init__(name)
        self.calls = []
        self.stdout = stdout

    def __repr__(self):
        return 'StubExecutable(\'%s\')' % self.name
    
    @exempt
    @property
    def times_called(self):
        return len(self.calls)

    def execute(self, method, commandline_arguments, *args, **kwargs):
        self.calls.append(MonitoredInvocation(method, commandline_arguments, args, kwargs))
        if self.stdout:
            out = kwargs.get('stdout', sys.stdout)
            print(self.stdout, file=out)

    @exempt
    @contextlib.contextmanager
    def activated(self):
        executable = self
        saved_which = Executable.which
        def test_which(self, program):
            if executable.name == program:
                return program
            else:
                return saved_which(self, program)

        saved_execute = Executable.execute
        def test_execute(self, method, commandline_arguments, *args, **kwargs):
            if executable.name == self.name:
                return executable.execute(method, commandline_arguments, *args, **kwargs)
            else:
                return saved_execute(self, method, commandline_arguments, *args, **kwargs)

        with replaced(Executable.which, test_which, Executable):
            with replaced(Executable.execute, test_execute, Executable):
                yield executable



def test_start_local():
    xpra_start_command = 'start -l'
    xpra = ExecutableStub()
    ControlXpra(Xpra(xpra_executable=xpra)).do(xpra_start_command.split(' '))

    assert xpra.times_called == 1
    assert xpra.calls[0].argv == 'start --sharing=yes --systemd-run=no :100'.split(' ')

    
class WhatFixture(Fixture):
    @scenario
    def start(self):
        self.command = 'start'
        self.expected_xpra_command = 'start --sharing=yes --systemd-run=no :100'

    @scenario
    def stop(self):
        self.command = 'stop'
        self.expected_xpra_command = 'stop :100'


class WhereFixture(Fixture):

    def new_fake_vagrant(self):
        return ExecutableStub('vagrant', stdout=textwrap.dedent("""
          Host ignoredname
             HostName ahostname
             Port aport
        """))

    def new_xpra_executable(self):
        return ExecutableStub('xpra')

    def new_ssh_executable(self):
        return ExecutableStub('ssh')

    @scenario
    def local(self):
        self.expected_executable = self.xpra_executable
        self.arguments = '-l'
        self.expected_command = ''
        self.expected_attach_destination = [':100']

    @scenario
    def vagrant(self):
        self.expected_executable = self.ssh_executable
        self.arguments = '-V somemachine'
        self.expected_command = 'somemachine -o HostName=ahostname -o Port=aport -- xpra'
        self.expected_attach_destination = ['ssh:somemachine:100', '--ssh="ssh -o HostName=ahostname -o Port=aport"']

    @scenario
    def ssh(self):
        self.expected_executable = self.ssh_executable
        self.arguments = '-s auser@somemachine -p aport'
        self.expected_command = 'auser@somemachine -p aport -o PasswordAuthentication=no -o ServerAliveInterval=30 -- xpra'
        self.expected_attach_destination = ['ssh:auser@somemachine:100', '--ssh="ssh -p aport -o PasswordAuthentication=no -o ServerAliveInterval=30"']


@with_fixtures(WhatFixture, WhereFixture)
def test_control(what, where):
    """You can start/stop an xpra on the local machine, a vagrant box or via ssh"""
    command = ControlXpra(Xpra(xpra_executable=where.xpra_executable, ssh_executable=where.ssh_executable))
    
    with where.fake_vagrant.activated():
        command.do((what.command+' '+where.arguments).split(' '))

    called_executable = where.expected_executable 
    assert called_executable.times_called == 1
    assert called_executable.calls[0].argv == (where.expected_command+' '+what.expected_xpra_command).strip().split(' ')


@with_fixtures(WhereFixture)
def test_attach(where):
    """You can attach your local xpra to a local server, or one on a vagrant box or via ssh"""
    command = ControlXpra(Xpra(xpra_executable=where.xpra_executable, ssh_executable=where.ssh_executable))
    
    with where.fake_vagrant.activated():
        command.do(('attach '+where.arguments).split(' '))

    called_executable = where.xpra_executable
    assert called_executable.times_called == 1
    assert called_executable.calls[0].argv == ('attach --sharing=yes').strip().split()+where.expected_attach_destination

    
@pytest.mark.parametrize('arguments, expected_command',[
    ('-V', 'default -o HostName=ahostname -o Port=aport -- xpra start --sharing=yes --systemd-run=no :100'.split(' ')),
    ('-V another', 'another -o HostName=ahostname -o Port=aport -- xpra start --sharing=yes --systemd-run=no :100'.split(' ')),
    ])
def test_start_vagrant(arguments, expected_command):
    test_data = textwrap.dedent("""
    Host ignoredname
       HostName ahostname
       Port aport
    """)

    with ExecutableStub('vagrant', stdout=test_data).activated():
        xpra_start_command = 'start ' + arguments
        ssh = ExecutableStub()
        ControlXpra(Xpra(ssh_executable=ssh)).do(xpra_start_command.split(' '))

    assert ssh.times_called == 1
    assert ssh.calls[0].argv == expected_command



