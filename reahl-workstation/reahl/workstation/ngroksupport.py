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

from reahl.component.shelltools import Command, Executable, CompositeCommand
from reahl.workstation.xprasupport import VagrantMachine
from reahl.workstation.dockersupport import DockerContainer

class Ngrok(CompositeCommand):
    """Manipulates ngrok on the local machine."""
    keyword = 'ngrok'

    @property
    def commands(self):
        return [NgrokStart]


class NgrokStart(Command):
    """Starts ngrok to open a tunnel to a local / vagrant or other machine reachable via ssh."""
    keyword = 'start'
    def assemble(self):
        super().assemble()
        location_group = self.parser.add_mutually_exclusive_group(required=True)
        location_group.add_argument('-l', '--local', action='store_true', dest='local', help='exposes the local machine ssh port')
        location_group.add_argument('-V', '--vagrant', nargs='?', const='default', default=False, help='exposes the given vagrant machine')
        location_group.add_argument('-D', '--docker', nargs='?', const='reahl', default=False, help='exposes the given docker container')
        location_group.add_argument('-s', '--ssh', default=None, help='exposes the given remote machine')
        location_group.add_argument('-n', '--named-tunnel', nargs='*', default=None, help='starts the given named tunnels')
        self.parser.add_argument('-p', '--port',  default='22', help='the port to expose')
        self.parser.add_argument('-r', '--region',  default='eu', help='ngrok region to connect to')
        self.parser.add_argument('-P', '--path',  default='~/bin', help='where to find ngrok')

    def execute(self, args):
        super().execute(args)

        env_with_path = dict(os.environ)
        env_with_path['PATH'] += '%s%s' % (os.pathsep, os.path.expanduser(args.path))
        if args.named_tunnel:
            return Executable('ngrok', verbose=True).check_call(['start', '--region=%s' % args.region]+args.named_tunnel, env=env_with_path)
        else:
            if args.vagrant:
                vagrant_ssh_config = VagrantMachine(args.vagrant).get_ssh_config()
                hostname = vagrant_ssh_config['HostName']
                port = vagrant_ssh_config['Port']
            elif args.docker:
                docker_container = DockerContainer(args.docker)
                hostname = docker_container.ip_address
                port = '22'
            elif args.ssh:
                hostname = args.ssh
                port = args.port
            else:
                hostname = None
                port = args.port

            hostname_port = ':'.join([i for i in [hostname, port] if i])
            return Executable('ngrok', verbose=True).check_call(['tcp', '--region=%s' % args.region, hostname_port], env=env_with_path)

