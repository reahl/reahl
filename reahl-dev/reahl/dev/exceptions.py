# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Exceptions used by modules in this package."""

import inspect

class StatusException(Exception):
    legend = None
    @classmethod
    def get_statusses(cls):
        import reahl.dev.exceptions
        return [i for i in [getattr(reahl.dev.exceptions, name) for name in dir(reahl.dev.exceptions)]
                if inspect.isclass(i) and issubclass(i, cls) and i is not cls]


class NoException(StatusException):
    legend = '+'
    def __str__(self):
        return 'New release uploaded - needs to be marked as released'

    
class NotBuiltException(StatusException):
    legend = 'B'
    def __str__(self):
        return 'Project not built'

class NotSignedException(StatusException):
    legend = 'S'
    def __str__(self):
        return 'Project not signed'


class NotBuiltAfterLastCommitException(StatusException):
    legend = 'b'
    def __str__(self):
        return 'Project build is older than the last commit'


class NotUploadedException(StatusException):
    legend = 'U'
    def __str__(self):
        project_name = 'Project'
        if self.args:
            project_name = self.args[0]
        return '%s is not uploaded' % project_name


class NotVersionedException(StatusException):
    legend = '.'
    def __str__(self):
        return 'Not versioned'


class NotCheckedInException(StatusException):
    legend = 'C'
    def __str__(self):
        return 'Not checked in %s' % (self.args or '')


class MetaInformationNotAvailableException(StatusException):
    legend = 'M'
    def __str__(self):
        return 'Cannot find project meta information'


class MetaInformationNotReadableException(StatusException):
    legend = 'm'
    def __str__(self):
        return 'Cannot reliably read project meta information - perhaps a malformed file?'


class UnchangedException(StatusException):
    legend = '='
    def __str__(self):
        return 'Unchanged since last release'


class NeedsNewVersionException(StatusException):
    legend = 'V'
    def __str__(self):
        return 'Needs a new version'

    
class AlreadyMarkedAsReleasedException(Exception):
    def __str__(self):
        return 'Already marked as released'


class AlreadyUploadedException(Exception):
    def __str__(self):
        return 'Already uploaded'


class AlreadyDebianisedException(Exception):
    def __str__(self):
        return 'Already debianised'
        

class NotAValidProjectException(Exception):
    def __str__(self):
        return 'Not a valid project'


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
    
