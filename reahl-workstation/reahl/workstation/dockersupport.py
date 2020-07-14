# Copyright 2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import subprocess
from reahl.component.shelltools import Executable

class DockerContainer:
    def __init__(self, container_name):
        self.container_name = container_name
        self.docker = Executable('docker', verbose=True)
        
    def get_ssh_args(self):
        return ['-o', 'UserKnownHostsFile=/dev/null', '-o', 'StrictHostKeyChecking=no']

    @property
    def ip_address(self):
        res = self.docker.run(['inspect', '-f',  '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', self.container_name],
                              stdout=subprocess.PIPE, encoding='utf-8')
        return res.stdout.strip()

    @property
    def user_name(self):
        res = self.docker.run(['container', 'exec', self.container_name, 'printenv', 'REAHL_USER'],
                              stdout=subprocess.PIPE, encoding='utf-8')
        return res.stdout.strip()

    @property
    def ssh_to(self):
        return '%s@%s' % (self.user_name, self.ip_address)


