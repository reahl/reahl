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

from reahl.component.shelltools import Executable
from reahl.workstation.ngroksupport import Ngrok
from reahl.stubble import stubclass
from reahl.tofu import Fixture, scenario
from reahl.tofu.pytestsupport import with_fixtures
from reahl.dev.fixtures import ExecutableStub



class WhereFixture(Fixture):
    def new_fake_vagrant(self):
        return ExecutableStub('vagrant', stdout=textwrap.dedent("""
          Host ignoredname
             HostName ahostname
             Port aport
        """))

    @scenario
    def local(self):
        self.input_arguments = '-l'
        self.expected_commandline = ['tcp', '--region=eu', '22']
        self.expected_full_args = ['tcp', '--region=us', '1212']

    @scenario
    def vagrant(self):
        self.input_arguments = '-V somemachine'
        self.expected_commandline = ['tcp', '--region=eu', 'ahostname:aport']
        self.expected_full_args = ['tcp', '--region=us', 'ahostname:aport']

    @scenario
    def ssh(self):
        self.input_arguments = '-s somemachine'
        self.expected_commandline = ['tcp', '--region=eu', 'somemachine:22']
        self.expected_full_args = ['tcp', '--region=us', 'somemachine:1212']

    @scenario
    def named_tunnel(self):
        self.input_arguments = '-n one two'
        self.expected_commandline = ['start', '--region=eu', 'one', 'two']
        self.expected_full_args = ['start', '--region=us', 'one', 'two']


@with_fixtures(WhereFixture)
def test_attach(where):
    """You can expoe yout local machine, a vagrant machine or another machine using ngrok"""
    command = Ngrok()

    ngrok = ExecutableStub('ngrok')
    
    with ngrok.inserted_as_shim(), where.fake_vagrant.inserted_as_shim():
        command.do(['start'] + where.input_arguments.split())

    assert ngrok.times_called == 1
    assert ngrok.calls[0].argv == where.expected_commandline

    with ngrok.inserted_as_shim(), where.fake_vagrant.inserted_as_shim():
        command.do(['start'] + where.input_arguments.split()+ ['-r', 'us', '-p', '1212'])

    assert ngrok.times_called == 2
    assert ngrok.calls[1].argv == where.expected_full_args
    

@with_fixtures(WhereFixture.local)
def test_path(where):
    """Change the path used to find ngrok with -P"""
    command = Ngrok()
    @stubclass(Executable)
    class NgrokStub(ExecutableStub):
        path = ''
        def execute(self, method, commandline_arguments, *args, **kwargs):
            self.path = kwargs['env']['PATH']

    ngrok = NgrokStub('ngrok')
    
    with ngrok.inserted_as_shim(), where.fake_vagrant.inserted_as_shim():
        command.do(['start', '-l', '-P', '/tmp/somewhere'])

    assert '/tmp/somewhere' in ngrok.path.split(':')
