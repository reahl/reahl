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

"""
The interfaces for persisted classes that are needed by the core Reahl framework. Different
implementations of the framework can be provided by implementing these.
"""

from abc import ABCMeta, abstractmethod


class UserSessionProtocol(object, metaclass=ABCMeta):
    """A UserSession represents a potentially lengthy interaction of a particular user with the system."""

    @classmethod
    @abstractmethod
    def for_current_session(cls): 
        """Returns a UserSession instance for the current user. If no UserSession is present for the current
           interaction yet this method should create one. If a UserSession does exist for the current interaction,
           this method returns the correct UserSession."""

    @abstractmethod
    def is_active(self): 
        """Answers whether the session is still usable (instead of being expired due to inactivity)."""
        
    @abstractmethod
    def is_secured(self): 
        """Answers whether the interaction is currently done via a secure channel where applicable.
        
           .. versionadded:: 3.1
        """
        
    @abstractmethod
    def set_last_activity_time(self): 
        """Sets a timestamp on the UserSession to indicate when the last activity was detected 
           relating to this interaction. UserSessions typically expire automatically if no activity is
           detected after some time."""

    @abstractmethod
    def get_interface_locale(self): 
        """Answers a string identifying the currently selected locale."""

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

    @classmethod
    @abstractmethod
    def initialise_web_session_on(cls, context):
        """Fetch/create a new UserSession or do any initialisation or reinitialisation needed on it and set it 
           on the given context as its .session attribute. 
           
           Called at the beginning of a request or after an abort during the request (which may require reinitialisation
           of the session so it may still be used after the abort).
        """

    @classmethod
    @abstractmethod
    def preserve_session(cls, session):
        """
        Ensure the given session object is kept intact so that it can survive a transaction abort.

        .. versionadded:: 5.2
        """

    @classmethod
    @abstractmethod
    def restore_session(cls, session):
        """
        After a transaction is aborted, this ensures the given session is restored to its state before the abort.

        .. versionadded:: 5.2
        """

    @abstractmethod
    def get_csrf_token(self):
        """
        Fetch/create a suitable token for protecting against CSRF.

        .. versionadded:: 5.2
        """


class SessionDataProtocol(object, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def clear_for_form(cls, form):
        """Removes all the user input associated with the given :class:`reahl.web.ui.Form`."""

    @classmethod
    @abstractmethod
    def clear_for_view(cls, view):
        """Removes all data saved in the scope of the given :class:`reahl.web.fw.UrlBoundView`.

        .. versionadded:: 5.0        
        """
    
    __hash__ = None
    @abstractmethod
    def __eq__(self, other): 
        """Is required to be implemented."""

    @abstractmethod
    def __neq__(self, other): 
        """Is required to be implemented."""


class UserInputProtocol(SessionDataProtocol, metaclass=ABCMeta):
    """User input, typed as strings on a form is persisted using this class, for the current user's session
       for use in a subsequent request. Used via `web.persisted_userinput_class`.
    """
    @classmethod
    @abstractmethod
    def get_previously_entered_for_form(cls, form, input_name, entered_input_type):
        """Returns the user input associated with the given :class:`reahl.web.ui.Form`, as previously saved using
           `input_name` as name.

           .. versionchanged:: 4.0
              Added entered_input_type
        """

    @classmethod
    @abstractmethod
    def save_input_value_for_form(cls, form, input_name, value, entered_input_type):
        """Persists `value` as the value of the user input associated with the given :class:`reahl.web.ui.Form`,
           using `input_name` as name.

           .. versionchanged:: 4.0
              Added entered_input_type
        """

    @classmethod
    @abstractmethod
    def get_persisted_for_view(cls, view, key, value_type):
        """Returns the value associated with the given :class:`reahl.web.fw.UrlBoundView`, as previously saved using
           `key`.

           .. versionadded:: 5.0
        """

    @classmethod
    @abstractmethod
    def add_persisted_for_view(cls, view, key, value, value_type):
        """Persists `value` associated with the given :class:`reahl.web.fw.UrlBoundView`,
           to be retrieved using `key`.

           .. versionadded:: 5.0
        """

    @classmethod
    @abstractmethod
    def remove_persisted_for_view(cls, view, key):
        """Removes previously persisted value with the given :class:`reahl.web.fw.UrlBoundView`, as previously saved using
           `key`

           .. versionadded:: 5.0
    """


class PersistedExceptionProtocol(SessionDataProtocol):
    """When a :class:`reahl.component.exceptions.DomainException` happens during Form submission, the 
       exception is persisted using this class, for the current user's session for use in a subsequent 
       request. Used via `web.persisted_exception_class`.
    """
    @classmethod
    @abstractmethod
    def clear_for_form_except_inputs(cls, form):
        """Clears the exception associated with this form, while leaving exeptions for invididual inputs intact.
        
        .. versionadded:: 5.0
        """

    @classmethod
    @abstractmethod
    def save_exception_for_form(cls, form, **kwargs):
        """Saves a an exception for the given :class:`reahl.web.ui.Form`.
        
        .. versionadded:: 5.0
        """

    @classmethod
    @abstractmethod
    def get_exception_for_form(cls, form):
        """Retrieves an exception previously saved for the given :class:`reahl.web.ui.Form`, or None if
           not found."""

    @classmethod
    @abstractmethod
    def get_exception_for_input(cls, form, input_name):
        """Retrieves an exception previously saved for the given :class:`reahl.web.ui.Form` and `input_name`
           or None if not found."""
    
    @classmethod
    @abstractmethod
    def clear_for_all_inputs(cls, form): 
        """Removes all saved Exceptions associated with the given :class:`reahl.web.ui.Form`."""


class PersistedFileProtocol(object, metaclass=ABCMeta):
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
