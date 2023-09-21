# Copyright 2013-2023 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Exceptions used by modules in this package."""

import inspect


class NotAValidProjectException(Exception):
    def __str__(self):
        message = 'Not a valid project'
        if self.args[0]:
            message = f'{message}: {self.args[0]}'
        return message

class InvalidProjectFileException(Exception):
    def __str__(self):
        return 'Invalid project file: %s (%s)' % (self.args[0], self.args[1])


class NoSuchProjectException(Exception):
    def __str__(self):
        return 'There is no such project (%s) in the workspace' % self.args[0]


class CouldNotConfigureServer(Exception):
    def __init__(self, ex):
        message = '\nCould not configure server: %s\nDid you perhaps forget to: "python -m pip install --no-deps -e ." ?' % ex
        super().__init__(message)
    
