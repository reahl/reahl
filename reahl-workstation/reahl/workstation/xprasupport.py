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


import os
import re
import tempfile
import argparse
import shlex
import contextlib
import itertools
import collections

from reahl.component.shelltools import Command, Executable, CompositeCommand
from reahl.workstation.dockersupport import DockerContainer

class VagrantMachine:
    def __init__(self, machine_name):
        self.machine_name = machine_name

    @contextlib.contextmanager
    def ssh_config_file(self):
        try:
            with tempfile.NamedTemporaryFile('w', delete=False) as ssh_config:
                Executable('vagrant').check_call(['ssh-config', self.machine_name], stdout=ssh_config)
            yield ssh_config
        finally:
            os.remove(ssh_config.name)

    def get_ssh_config(self):
        config_dict = collections.OrderedDict()
        with self.ssh_config_file() as ssh_config:
            for line in open(ssh_config.name):
                match = re.match('^ +(\w+) ([^\s ]+).*', line)
                if match:
                    config_dict[match.group(1)] = match.group(2)
        return config_dict
        
    def get_ssh_args(self):
        config_dict = self.get_ssh_config()
        return list(itertools.chain.from_iterable([['-o', '%s=%s' % (name, value)] for name, value in config_dict.items()]))

    
class EndPoint:
    def __init__(self, display, ssh_to=None, ssh_arguments=None):
        self.display = display
        self.ssh_to = ssh_to
        self.ssh_arguments = ssh_arguments

    @property
    def is_local(self):
        return not self.ssh_to

    def as_attach_arguments(self):
        if self.ssh_to:
            arguments = ['ssh:%s%s' % (self.ssh_to, self.display)]
        else:
            arguments = [self.display]
        if self.ssh_arguments:
            arguments.append('--ssh=ssh %s' % (' '.join(self.ssh_arguments)))
        return arguments

    def as_ssh_arguments(self):
        return [self.ssh_to] + self.ssh_arguments     


class Xpra:
    def __init__(self, xpra_executable=None, ssh_executable=None):
        self.xpra_executable = xpra_executable or Executable('xpra', verbose=True)
        self.ssh_executable = ssh_executable or Executable('ssh', verbose=True)

    def get_xpra_args_for(self, action, extra_args):
        if action == 'attach':
            action_args = ['--sharing=yes']
        elif action == 'start':
            action_args = ['--sharing=yes', '--systemd-run=no']
        else:
            action_args = []
        return [action] + action_args + extra_args

    def attach(self, endpoint, extra_args):
        self.xpra_executable.check_call(self.get_xpra_args_for('attach', extra_args) + endpoint.as_attach_arguments())

    def run_at_endpoint(self, action, endpoint, extra_args):
        if endpoint.is_local:
            self.xpra_executable.check_call(self.get_xpra_args_for(action, extra_args) + [endpoint.display])
        else:
            self.ssh_executable.check_call(endpoint.as_ssh_arguments() +
                                           ['--', 'xpra'] + self.get_xpra_args_for(action, extra_args) + [endpoint.display])



class ControlXpra(CompositeCommand):
    """Controls an xpra server locally, or on another machine."""
    keyword = 'xpra'

    def __init__(self, xpra=None):
        super().__init__()
        self.xpra = xpra or Xpra()

    @property
    def commands(self):
        return [XpraSubcommand(self.xpra, 'start', 'Starts an Xpra server locally or elsewhere', ),
                XpraSubcommand(self.xpra, 'stop', 'Stops an Xpra server locally or elsewhere'),
                XpraSubcommand(self.xpra, 'attach', 'Attaches to an Xpra server locally or elsewhere')]


class XpraSubcommand(Command):
    def __init__(self, xpra, keyword, description):
        self.xpra = xpra
        self.keyword = keyword
        self.description = description
        super().__init__()

    def format_description(self):
        return self.description
    
    def assemble(self):
        super().assemble()
        location_group = self.parser.add_mutually_exclusive_group(required=True)
        location_group.add_argument('-l', '--local', action='store_true', dest='local', help='%s the xpra server locally' % self.keyword)
        location_group.add_argument('-V', '--vagrant', nargs='?', const='default', default=False, help='%s the xpra server inside this vagrant machine' % self.keyword)
        location_group.add_argument('-D', '--docker', nargs='?', const='reahl', default=False, help='%s the xpra server inside this docker container' % self.keyword)
        location_group.add_argument('-s', '--ssh', default=None, help='ssh to this to %s the xpra server' % self.keyword)

        self.parser.add_argument('-p', '--ssh_port',  help='the ssh port to %s to'  % self.keyword)
        self.parser.add_argument('--ssh-args', default='', help='extra arguments to ssh')

        self.parser.add_argument('-d', '--display', default=':100', help='the X display on which to %s the server' % self.keyword)
        self.parser.add_argument('extra_args', nargs=argparse.REMAINDER, help='Extra arguments to pass on to xpra')

    def endpoint_from_args(self, args):
        ssh_args = shlex.split(args.ssh_args)
        if args.ssh_port:
            ssh_args += ['-p', args.ssh_port]

        if args.local:
            return EndPoint(args.display)
        elif args.docker:
            docker_container = DockerContainer(args.docker)
            return EndPoint(args.display, ssh_to=docker_container.ssh_to, ssh_arguments=ssh_args+docker_container.get_ssh_args())
        elif args.vagrant:
            vagrant_ssh_args = VagrantMachine(args.vagrant).get_ssh_args()
            return EndPoint(args.display, ssh_to=args.vagrant, ssh_arguments=ssh_args+vagrant_ssh_args)
        else:
            defaulted_ssh_args = ['-o', 'PasswordAuthentication=no', '-o', 'ServerAliveInterval=30']
            return EndPoint(args.display, ssh_to=args.ssh, ssh_arguments=ssh_args+defaulted_ssh_args)

    def execute(self, args):
        super().execute(args)

        if self.keyword == 'attach':
            return self.xpra.attach(self.endpoint_from_args(args), args.extra_args)
        else:
            return self.xpra.run_at_endpoint(self.keyword, self.endpoint_from_args(args), args.extra_args)







