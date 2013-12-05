# Copyright 2009, 2010, 2011, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
    def __unicode__(self):
        return u'New release uploaded - needs to be marked as released'

    
class NotBuiltException(StatusException):
    legend = u'B'
    def __unicode__(self):
        return u'Project not built'


class NotBuiltAfterLastCommitException(StatusException):
    legend = u'b'
    def __unicode__(self):
        return u'Project build is older than the last commit'


class NotUploadedException(StatusException):
    legend = u'U'
    def __unicode__(self):
        project_name = 'Project'
        if self.args:
            project_name = self.args[0]
        return '%s is not uploaded' % project_name


class NotVersionedException(StatusException):
    legend = u'.'
    def __unicode__(self):
        return u'Not versioned'


class NotCheckedInException(StatusException):
    legend = u'C'
    def __unicode__(self):
        return u'Not checked in %s' % (self.args or '')


class MetaInformationNotAvailableException(StatusException):
    legend = u'M'
    def __unicode__(self):
        return u'Cannot find project meta information'


class MetaInformationNotReadableException(StatusException):
    legend = u'm'
    def __unicode__(self):
        return u'Cannot reliably read project meta information - perhaps a malformed file?'


class UnchangedException(StatusException):
    legend = u'='
    def __unicode__(self):
        return u'Unchanged since last release'


class NeedsNewVersionException(StatusException):
    legend = u'V'
    def __unicode__(self):
        return u'Needs a new version'

    
class AlreadyMarkedAsReleasedException(Exception):
    def __unicode__(self):
        return u'Already marked as released'


class AlreadyUploadedException(Exception):
    def __unicode__(self):
        return u'Already uploaded'


class AlreadyDebianisedException(Exception):
    def __unicode__(self):
        return u'Already debianised'
        

class NotAValidProjectException(Exception):
    def __unicode__(self):
        return u'Not a valid project'


class InvalidProjectFileException(Exception):
    def __unicode__(self):
        return u'Invalid project file'


class NoSuchProjectException(Exception):
    def __unicode__(self):
        return u'There is no such project (%s) in the workspace' % self.args[0]


    
