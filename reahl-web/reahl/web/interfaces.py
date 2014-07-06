# Copyright 2010, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""
The interfaces for persisted classes that are needed by the core Reahl framework. Different
implementations of the framework can be provided by implementing these.
"""
from __future__ import print_function
from __future__ import unicode_literals
import six

from abc import ABCMeta, abstractmethod

from reahl.interfaces import UserSessionProtocol


class WebUserSessionProtocol(UserSessionProtocol):
    """The protocol for an implementation to a class used via `web.session_class`."""
    @classmethod
    @abstractmethod
    def get_or_create_session(cls): 
        """Returns a session, creating a new one if none can be determined. If one can be determined from
           the browser, that session is returned."""

    @abstractmethod
    def set_session_key(self, response): 
        """Called at the end of a request loop to enable an implementation to save some identifying information
           to the response (such as setting a cookie with the ID of the current session).
        """


@six.add_metaclass(ABCMeta)
class UserInputProtocol(object):
    """User input, typed as strings on a form is persisted using this class, for the current user's session
       for use in a subsequent request. Used via `web.persisted_userinput_class`.
    """

    @classmethod
    @abstractmethod
    def clear_for_form(cls, form):
        """Removes all the user input associated with the given :class:`reahl.web.ui.Form`."""

    @classmethod
    @abstractmethod
    def get_previously_entered_for_form(cls, form, input_name): 
        """Returns the user input associated with the given :class:`reahl.web.ui.Form`, as previously saved using
           `input_name` as name."""

    @classmethod
    @abstractmethod
    def save_input_value_for_form(cls, form, input_name, value):
        """Persists `value` as the value of the user input associated with the given :class:`reahl.web.ui.Form`,
           using `input_name` as name."""

    __hash__ = None
    @abstractmethod
    def __eq__(self, other): 
        """Is required to be implemented."""

    @abstractmethod
    def __neq__(self, other): 
        """Is required to be implemented."""


class PersistedExceptionProtocol(UserInputProtocol):
    """When a :class:`reahl.component.exceptions.DomainException` happens during Form submission, the 
       exception is persisted using this class, for the current user's session for use in a subsequent 
       request. Used via `web.persisted_exception_class`.
    """
    @classmethod
    @abstractmethod
    def get_exception_for_form(self, form): 
        """Retrieves an exception previously saved for the given :class:`reahl.web.ui.Form`, or None if
           not found."""

    @classmethod
    @abstractmethod
    def get_exception_for_input(self, form, input_name): 
        """Retrieves an exception previously saved for the given :class:`reahl.web.ui.Form` and `input_name`
           or None if not found."""
    
    @classmethod
    @abstractmethod
    def clear_for_all_inputs(cls, form): 
        """Removes all saved Exceptions associated with the given :class:`reahl.web.ui.Form`."""

      
@six.add_metaclass(ABCMeta)
class PersistedFileProtocol(object):
    """When a file is uploaded, file is persisted using this class, for the current user's session 
       for use in a subsequent request. Used via `web.persisted_file_class`.
    """
    @property
    @abstractmethod
    def file_obj(self): 
        """Returns an object with traditional `.read` and `.seek` methods which can be used to
           read the contents of the persisted file.
        """

    @classmethod
    @abstractmethod
    def clear_for_form(cls, form): 
        """Removes all files previously saved for the given :class:`reahl.web.ui.Form`."""

    __hash__ = None
    @abstractmethod
    def __eq__(self, other): 
        """Is required to be implemented."""

    @abstractmethod
    def __neq__(self, other): 
        """Is required to be implemented."""

    @classmethod
    @abstractmethod
    def get_persisted_for_form(cls, form, input_name): 
        """Returns the previously persisted file for the given :class:`reahl.web.ui.Form`,
           using the given `input_name` as name."""

    @classmethod
    @abstractmethod
    def add_persisted_for_form(cls, form, input_name, uploaded_file): 
        """Saves the given `uploaded_file` (a :class:`cgi.FileStorage`) using the given `input_name`
           for the given :class:`reahl.web.ui.Form`.
        """

    @classmethod
    @abstractmethod
    def remove_persisted_for_form(cls, form, input_name, filename): 
        """Removes previously persisted file with name `filename`, as saved for the given 
           :class:`reahl.web.ui.Form` and `input_name`."""

    @classmethod
    @abstractmethod
    def is_uploaded_for_form(cls, form, input_name, filename): 
        """Answers whether a file with name `filename` has previously been saved for the given 
           :class:`reahl.web.ui.Form` and `input_name`."""
