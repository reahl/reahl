# Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Interfaces for classes that have pluggable implementations."""

from __future__ import unicode_literals
from __future__ import print_function
import six
from abc import ABCMeta, abstractmethod

@six.add_metaclass(ABCMeta)
class UserSessionProtocol(object):
    """A UserSession represents a potentially lengthy interaction of a particular the user with the system."""

    @classmethod
    @abstractmethod
    def for_current_session(cls): 
        """Returns a UserSession instance for the current user. If no UserSession is present for the current
           interaction yet this method should create one. If a UserSession does exist for the current interaction,
           this method returns the correct UserSession."""

    @abstractmethod
    def is_secure(self): 
        """Answers whether the interaction is currently done via a secure channel where applicable."""
        
    @abstractmethod
    def is_logged_in(self): 
        """Answers whether the current user has been authenticated."""

    @abstractmethod
    def set_last_activity_time(self): 
        """Sets a timestamp on the UserSession to indicate when the last activity was detected 
           relating to this interaction. UserSessions typically expore automatically if no activity is
           detected after some time."""

    @abstractmethod
    def get_interface_locale(self): 
        """Answers a string identifying the currently selected locale."""

    
