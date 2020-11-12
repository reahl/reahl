# Copyright 2017, 2018, 2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import textwrap

from reahl.workstation.xprasupport import ControlXpra, Xpra
from reahl.tofu import Fixture, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.dev.fixtures import ExecutableStub


class CommandFixture(Fixture):
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

    def run_command(self, arguments):
        command = ControlXpra(Xpra(xpra_executable=self.xpra_executable, ssh_executable=self.ssh_executable))
        with self.fake_vagrant.inserted_as_shim():
            command.do(arguments)

    def was_executable_run_with(self, expected_executable, expected_args_to_executable):
        return expected_executable.times_called == 1 and \
            expected_executable.calls[0].argv == expected_args_to_executable


@uses(command_fixture=CommandFixture)
class WhereFixture(Fixture):
    @scenario
    def local(self):
        self.input_arguments = ['-l']
        self.expected_executable = self.command_fixture.xpra_executable
        self.expected_commandline = []
        self.expected_xpra_attach_commandline = [':100']

    @scenario
    def vagrant(self):
        self.input_arguments = ['-V', 'somemachine']
        self.expected_executable = self.command_fixture.ssh_executable
        self.expected_commandline = ['somemachine', '-o', 'HostName=ahostname', '-o', 'Port=aport', '--', 'xpra']
        self.expected_xpra_attach_commandline = ['ssh:somemachine:100', '--ssh=ssh -o HostName=ahostname -o Port=aport']

    @scenario
    def ssh(self):
        self.input_arguments = ['-s', 'auser@somemachine', '-p', 'aport']
        self.expected_executable = self.command_fixture.ssh_executable
        self.expected_commandline = ['auser@somemachine', '-p', 'aport', '-o', 'PasswordAuthentication=no', '-o', 'ServerAliveInterval=30', '--', 'xpra']
        self.expected_xpra_attach_commandline = ['ssh:auser@somemachine:100', '--ssh=ssh -p aport -o PasswordAuthentication=no -o ServerAliveInterval=30']


@with_fixtures(CommandFixture, WhereFixture)
def test_start(fixture, where):
    """You can start an xpra on the local machine, a vagrant box or via ssh"""

    fixture.run_command(['start'] + where.input_arguments)

    assert fixture.was_executable_run_with(where.expected_executable,
                                       where.expected_commandline + ['start', '--sharing=yes', '--systemd-run=no', ':100'])


@with_fixtures(CommandFixture, WhereFixture)
def test_stop(fixture, where):
    """You can stop an xpra on the local machine, a vagrant box or via ssh"""

    fixture.run_command(['stop'] + where.input_arguments)

    assert fixture.was_executable_run_with(where.expected_executable,
                                       where.expected_commandline + ['stop', ':100'])


@with_fixtures(CommandFixture, WhereFixture)
def test_attach(fixture, where):
    """You can attach your local xpra to a local server, or one on a vagrant box or via ssh"""

    fixture.run_command(['attach'] + where.input_arguments)

    assert fixture.was_executable_run_with(fixture.xpra_executable,
                                           ['attach', '--sharing=yes'] + where.expected_xpra_attach_commandline)






