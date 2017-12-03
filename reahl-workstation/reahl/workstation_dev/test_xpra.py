import sys
import textwrap

import pytest
from reahl.workstation.xprasupport import ControlXpra, Xpra
from reahl.stubble import stubclass, exempt, replaced
from reahl.tofu import Fixture, scenario
from reahl.tofu.pytestsupport import with_fixtures
from reahl.dev.fixtures import ExecutableStub



class WhatFixture(Fixture):
    @scenario
    def start(self):
        self.command = 'start'
        self.expected_xpra_commandline = 'start --sharing=yes --systemd-run=no :100'

    @scenario
    def stop(self):
        self.command = 'stop'
        self.expected_xpra_commandline = 'stop :100'


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
        self.input_arguments = '-l'
        self.expected_executable = self.xpra_executable
        self.expected_commandline = ''
        self.expected_xpra_attach_commandline = [':100']

    @scenario
    def vagrant(self):
        self.input_arguments = '-V somemachine'
        self.expected_executable = self.ssh_executable
        self.expected_commandline = 'somemachine -o HostName=ahostname -o Port=aport -- xpra'
        self.expected_xpra_attach_commandline = ['ssh:somemachine:100', '--ssh="ssh -o HostName=ahostname -o Port=aport"']

    @scenario
    def ssh(self):
        self.input_arguments = '-s auser@somemachine -p aport'
        self.expected_executable = self.ssh_executable
        self.expected_commandline = 'auser@somemachine -p aport -o PasswordAuthentication=no -o ServerAliveInterval=30 -- xpra'
        self.expected_xpra_attach_commandline = ['ssh:auser@somemachine:100', '--ssh="ssh -p aport -o PasswordAuthentication=no -o ServerAliveInterval=30"']


@with_fixtures(WhatFixture, WhereFixture)
def test_control(what, where):
    """You can start/stop an xpra on the local machine, a vagrant box or via ssh"""
    command = ControlXpra(Xpra(xpra_executable=where.xpra_executable, ssh_executable=where.ssh_executable))
    
    with where.fake_vagrant.inserted_as_shim():
        command.do((what.command+' '+where.input_arguments).split())

    called_executable = where.expected_executable 
    assert called_executable.times_called == 1
    assert called_executable.calls[0].argv == (where.expected_commandline+' '+what.expected_xpra_commandline).strip().split()


@with_fixtures(WhereFixture)
def test_attach(where):
    """You can attach your local xpra to a local server, or one on a vagrant box or via ssh"""
    command = ControlXpra(Xpra(xpra_executable=where.xpra_executable, ssh_executable=where.ssh_executable))
    
    with where.fake_vagrant.inserted_as_shim():
        command.do(['attach'] + where.input_arguments.split())

    called_executable = where.xpra_executable
    assert called_executable.times_called == 1
    assert called_executable.calls[0].argv == 'attach --sharing=yes'.split() + where.expected_xpra_attach_commandline

    


