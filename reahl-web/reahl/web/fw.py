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

"""The reahl.fw module implements the core of the Reahl web framework.

Run 'reahl componentinfo reahl-web' for configuration information.
"""

import atexit
import inspect
import json
import logging
import hashlib
import mimetypes
import string
import time
import sys
import threading
from contextlib import contextmanager
from datetime import datetime
import itertools
import functools
import io
import locale
import os
import os.path
import re
import tempfile
import warnings
from collections import OrderedDict
import urllib.parse

import pkg_resources
import rjsmin
import rcssmin

from webob import Request, Response
from webob.exc import HTTPException
from webob.exc import HTTPForbidden
from webob.exc import HTTPInternalServerError
from webob.exc import HTTPMethodNotAllowed
from webob.exc import HTTPNotFound
from webob.exc import HTTPSeeOther
from webob.request import DisconnectionError
from webob.multidict import MultiDict

from reahl.component.config import StoredConfiguration
from reahl.component.context import ExecutionContext
from reahl.component.dbutils import SystemControl
from reahl.component.decorators import memoized
from reahl.component.exceptions import ArgumentCheckedCallable
from reahl.component.exceptions import DomainException
from reahl.component.exceptions import IsInstance
from reahl.component.exceptions import IsSubclass
from reahl.component.exceptions import NotYetAvailable
from reahl.component.exceptions import ProgrammerError
from reahl.component.exceptions import arg_checks
from reahl.component.i18n import Catalogue
from reahl.component.modelinterface import StandaloneFieldIndex, FieldIndex, Field, Event, ValidationConstraint,\
                                             Allowed, ExposedNames, Event, Action
from reahl.web.csrf import InvalidCSRFToken, CSRFToken, ExpiredCSRFToken

USE_PKG_RESOURCES=False
if sys.version_info < (3, 9):
    try:
        import importlib_resources
    except:
        USE_PKG_RESOURCES=True        
else:
    import importlib.resources as importlib_resources


_ = Catalogue('reahl-web')


class ValidationException(DomainException):
    """Indicates that one or more Fields received invalid data."""
    @classmethod
    def for_failed_validations(cls, failed_validation_constraints):
        detail_messages = [i.message for i in failed_validation_constraints]
        return cls(message=_.ngettext('An error occurred', 'Some errors occurred', len(detail_messages)), detail_messages=detail_messages)


class NoMatchingFactoryFound(Exception):
    pass


class NoEventHandlerFound(Exception):
    pass


class CannotCreate(NoMatchingFactoryFound):
    """Programmers raise this to indicate that the arguments given via URL to a View
       or UserInterface that is parameterised were invalid."""


class Url:
    """An Url represents an URL, and is used to modify URLs, or manipulate them in other ways. Construct it
       with an URL in a string."""
    @classmethod
    def get_current_url(cls, request=None):
        """Returns the Url requested by the current Request."""
        request = request or ExecutionContext.get_context().request
        return cls(str(request.url))
    
    def __init__(self, url_string):
        split_url = urllib.parse.urlsplit(url_string)
        self.scheme = split_url.scheme
        self.username = split_url.username
        self.password = split_url.password
        self.hostname = split_url.hostname
        self.port = split_url.port
        self.path = split_url.path
        self.query = split_url.query
        self.fragment = split_url.fragment

    def set_scheme(self, scheme):
        """Sets the scheme part of the Url (the http or https before the :), ensuring that the
           port is also correct accorging to the new scheme. Ports numbers are set from
           web.default_http_port and web.encrypted_http_port configuration settings."""
        self.scheme = scheme
        if self.port:
            config = ExecutionContext.get_context().config
            self.port = config.web.default_http_port
            if self.scheme == config.web.encrypted_http_scheme:
                self.port = config.web.encrypted_http_port

    def set_query_from(self, value_dict, doseq=False):
        """Sets the query string of this Url from a dictionary."""
        self.query = urllib.parse.urlencode(value_dict, doseq=doseq)

    def get_query_dict(self):
        return urllib.parse.parse_qs(self.query)
    
    @property
    def netloc(self):
        """Returns the `authority part of the URl as per RFC3968 <http://tools.ietf.org/html/rfc3986#section-3.2>`_,
           also sometimes referred to as the netloc part in Python docs."""
        netloc = ''
        if self.username: netloc += self.username
        if self.password: netloc += ':%s' % self.password
        if netloc:        netloc += '@'
        if self.hostname: netloc += self.hostname
        if self.port:     netloc += ':%s' % self.port
        return netloc

    def get_locale_split_path(self, locale=None):
        locale = locale or '[^/]+'
        match = re.match('/(?P<locale>%s)(?P<url>/.*|$)' % locale, self.path)
        if match:
            return match.groups()
        return (None, self.path)
        
    @property
    def is_network_absolute(self):
        """Answers whether this URL `is absolute according to RFC3986 <http://tools.ietf.org/html/rfc3986#section-4.3>`_ 
           (ie, whether the Url includes a scheme, hostname and port)."""
        return self.scheme and self.path and self.path.startswith('/')

    def make_network_absolute(self):
        """Ensures that this URL has a scheme, hostname and port matching that of the current Request URL."""
        # Note: It is tempting to want to use request.scheme, request.server_name and request.server_port
        #       in this method.
        #
        #       But, request.server_name can be different from request_url.hostname; and if this
        #       happens, and you use it here, the changed url will result in invalidating the existing
        #       session cookie on the client which is bound to the request_url.hostname by the browser.
        #
        request_url = Url.get_current_url()
        self.scheme = self.scheme or request_url.scheme
        self.hostname = self.hostname or request_url.hostname
        self.port = self.port or request_url.port

    def make_network_relative(self):
        """Removes the scheme, hostname and port from this URL."""
        self.scheme = ''
        self.hostname = ''
        self.port = ''

    def as_network_absolute(self):
        """Returns a new Url equal to this one, except that it does not contain a scheme, hostname or port."""
        absolute = Url(str(self))
        absolute.make_network_absolute()
        return absolute

    def make_locale_absolute(self, locale=None):
        """Ensures that this URL starts with a string indicating the current locale (if not using the default locale)."""
        context = ExecutionContext.get_context()
        locale = locale or context.interface_locale
        if locale != context.config.web.default_url_locale:
            self.path = '/%s%s' % (locale, self.path)
        
    def make_locale_relative(self):
        """Ensures that this URL does not include a starting path indicating locale."""
        locale = ExecutionContext.get_context().interface_locale
        locale, path = self.get_locale_split_path(locale=locale)
        self.path = path

    def as_locale_relative(self):
        """Returns a new Url equal to this one, except that it does not include the starting path indicating locale."""
        relative = Url(str(self))
        relative.make_locale_relative()
        return relative

    def with_new_locale(self, locale):
        """Returns a new Url equal to this one, but with a starting path for the locale given."""
        new_url = Url(str(self)).as_locale_relative()
        new_url.make_locale_absolute(locale=locale)
        return new_url
        
    def __str__(self):
        return urllib.parse.urlunsplit((self.scheme, self.netloc, self.path, self.query, self.fragment))

    def is_active_on(self, current_url, exact_path=False):
        """Answers whether this Url matches the `current_url`. If exact_path=False this Url
           also matches `current_url` if this Url is 'underneath' `current_url` in the Url
           hierarchy."""
        if exact_path:
            path_matches = current_url.path == self.path
        else:
            path_matches = current_url.path.startswith(self.path)

        if not path_matches:
            return False

        return self.query_is_subset(current_url)

    def is_currently_active(self, exact_path=False):
        """Answers whether this Url is currently active (see `is_active_on`)."""
        request = ExecutionContext.get_context().request
        return self.is_active_on(Url(request.url), exact_path=exact_path)

    def query_is_subset(self, other_url):
        """Answers whether name=value pairs present in this Url's query string is a subset
           of those present in `other_url`."""
        other_args = other_url.get_query_dict()
        self_args = self.get_query_dict()

        if not set(self_args).issubset(set(other_args)):
            return False

        if 'returnTo' in self_args:
            del self_args['returnTo']
        if 'returnTo' in other_args:
            del other_args['returnTo']
        other_values = dict([(key, other_args[key]) for key in self_args])
        return other_values == self_args


class InternalRedirect(Exception):
    pass


class EventHandler:
    """An EventHandler is used to transition the user to the View that matches `target` (a :class:`ViewFactory`),
       but only if the occurring Event matches `event`.
       """
    def __init__(self, user_interface, event, target):
        self.user_interface = user_interface
        self.event_name = event.name
        self.target = target

    def should_handle(self, event_occurrence):
        return self.event_name == event_occurrence.name

    def get_destination_absolute_url(self, event_occurrence):
        if self.target.matches_view(self.user_interface.controller.current_view):
            url = SubResource.get_parent_url()
        else:
            try:
                url = self.target.get_absolute_url(self.user_interface, **event_occurrence.arguments)
            except ValidationConstraint as ex:
                raise ProgrammerError('The arguments of %s are invalid for transition target %s: %s' % \
                    (event_occurrence, self.target, ex))
        return url


class Transition(EventHandler):
    """A Transition is a special kind of :class:`EventHandler`. Transitions are used to define
       how a user is transitioned amongst many Views in response to different Events that may occur.
       A Transition will only be used if its `source` (a :class:`ViewFactory`) matches the current View
       and if its `guard` (an :class:`Action`) returns True. If not specified, a `guard` is used which
       always the Transition to be used."""
    @arg_checks(source=IsInstance('reahl.web.fw:ViewFactory'), target=IsInstance('reahl.web.fw:ViewFactory'))
    def __init__(self, controller, event, source, target, guard=None):
        super().__init__(controller.user_interface, event, target)
        self.controller = controller
        self.source = source
        self.guard = guard if guard else Allowed(True)
    
    def should_handle(self, event_occurrence):
        return (self.source.matches_view(self.controller.current_view)) and \
               super().should_handle(event_occurrence) and \
               self.guard(event_occurrence)


class FactoryDict(set):
    def __init__(self, initial_set, *args):
        super().__init__(initial_set)
        self.args = args
        
    def get_factory_for(self, key):
        found_factory = None
        best_rating = 0
        for factory in self:
            rating = factory.is_applicable_for(key)
            if rating > best_rating:
                best_rating = rating
                found_factory = factory
        logging.getLogger(__name__).debug('Found factory: %s for "%s"' % (found_factory, key))
        return found_factory

    def __getitem__(self, key):
        found_factory = self.get_factory_for(key)
        if not found_factory:
            raise NoMatchingFactoryFound(key)

        return found_factory.create(key, *self.args)
        
    def get(self, key, default=None):
        try:
            return self[key]
        except NoMatchingFactoryFound:
            return default


class Controller:
    def __init__(self, user_interface):
        self.user_interface = user_interface
        self.event_handlers = []
        self.views = FactoryDict(set(), self.user_interface)
        self.clear_cache()

    def clear_cache(self):
        self.cached_views = {}

    def add_view_factory(self, view_factory):
        self.views.add(view_factory)
        return view_factory
    
    @property
    def relative_path(self):
        return self.user_interface.relative_path
    
    @property
    def current_view(self): 
        return self.view_for(self.relative_path)

    def view_for(self, relative_path, for_bookmark=False):
        try:
            view = self.cached_views[relative_path]
        except KeyError:
            view = self.views.get(relative_path, NoView(self.user_interface))
            if not for_bookmark:
                self.cached_views[relative_path] = view
        return view

    @arg_checks(event=IsInstance(Event), target=IsInstance('reahl.web.fw:ViewFactory', allow_none=True))
    def define_event_handler(self, event, target=None):
        event_handler = EventHandler(self.user_interface, event, target or self.current_view.as_factory())
        self.event_handlers.append(event_handler)
        return event_handler

    def add_transition(self, transition):
        self.event_handlers.append(transition)
        return transition

    def define_transition(self, event, source, target, guard=None):
        return self.add_transition(Transition(self, event, source, target, guard=guard))

    def define_local_transition(self, event, source, guard=None):
        return self.add_transition(Transition(self, event, source, source, guard=guard))

    def define_return_transition(self, event, source, guard=None):
        return self.add_transition(Transition(self, event, source, ReturnToCaller(source.as_bookmark(self.user_interface)).as_view_factory(), guard=guard))

    def has_event_named(self, name):
        for handler in self.event_handlers:
            if handler.event_name == name:
                return True
        return False

    def get_handler_for(self, event_ocurrence):
        for handler in self.event_handlers:
            if handler.should_handle(event_ocurrence):
                return handler
        raise NoEventHandlerFound(event_ocurrence.name)
    
    def handle_event(self, event_ocurrence):
        handler = self.get_handler_for(event_ocurrence)
        event_ocurrence.fire() # should only happen if a handler was found
        return handler.get_destination_absolute_url(event_ocurrence)


class UserInterface:
    """A UserInterface holds a collection of :class:`View` instances, each View with its own URL relative to the UserInterface itself.
       UserInterfaces can also contain other UserInterfaces. 
       
       Programmers create their own UserInterface class by inheriting from UserInterface, and overriding :meth:`UserInterface.assemble`
       to define the contents of the UserInterface.

       UserInterfaces are not instantiated by programmers, a UserInterface is defined as a sub-user_interface of a given parent UserInterface by
       calling the :meth:`UserInterface.define_user_interface` from inside the :meth:`UserInterface.assemble` method of its parent UserInterface.
       
       The class of UserInterface to be used as root for the entire web application is configured 
       via the `web.site_root` config setting.
    """
    def __init__(self, parent_ui, relative_base_path, slot_map, for_bookmark, name, **ui_arguments):
        self.relative_base_path = relative_base_path #: The path where this UserInterface starts, relative to its parent UserInterface
        self.parent_ui = parent_ui           #: The UserInterface onto which this UserInterface is grafted
        self.slot_map = slot_map                     #: A dictionary mapping names of Slots as used in this 
                                                     #: UserInterface, to those of its parent UserInterface
        self.name = name                             #: A name which is unique amongst all UserInterfaces in the application
        self.relative_path = ''                     #: The path of the current Url, relative to this UserInterface
        self.page_factory = None
        self.error_view_factory = None
        if not for_bookmark:
            self.update_relative_path()
        self.sub_uis = FactoryDict(set())
        self.controller = Controller(self)
        self.assemble(**ui_arguments)
        if not self.error_view_factory:
            self.define_default_error_view()
        self.sub_resources = FactoryDict(set())
        if not self.name:
            raise ProgrammerError('No .name set for %s. This should be done in the call to .define_user_interface or in %s.assemble().' % \
                                      (self, self.__class__.__name__))

    @property
    def current_view(self):
        """The :class:`View` which is targetted by the URL of the current :class:webob.Request."""
        return self.view_for(self.relative_path)

    @property
    def base_path(self):
        """The path this UserInterface has in the current web application. It is appended to the URLs of all :class:`View` s
           in this UserInterface."""
        return self.make_full_path(self.parent_ui, self.relative_base_path)

    @property
    def root_ui(self):
        if self.parent_ui:
            return self.parent_ui.root_ui 
        else:
            return self

    @classmethod 
    def make_full_path(cls, parent_ui, relative_path):
        if parent_ui:
            path = parent_ui.base_path + relative_path
            if path.startswith('//'):
                return path[1:]
            return path
        return relative_path

    def assemble(self, **ui_arguments):
        """Programmers override this method in order to define the contents of their UserInterface. This mainly
           means defining Views or other UserInterfaces inside the UserInterface being assembled. The default
           implementation of `assemble` is empty, so there's no need to call the super implementation
           from an overriding implementation."""

    def update_relative_path(self):
        current_path = Url.get_current_url().as_locale_relative().path
        relative_path = self.get_relative_path_for(current_path)
        self.set_relative_path(relative_path)

    def set_relative_path(self, relative_path):
        self.relative_path = relative_path

    def register_resource_factory(self, regex_factory):
        self.sub_resources.add(regex_factory)

    def sub_resource_for(self, path):
        try:
            return self.sub_resources[path]
        except NoMatchingFactoryFound:
            raise HTTPNotFound()

    @arg_checks(widget_class=IsSubclass('reahl.web.fw:Widget'))
    def define_page(self, widget_class, *args, **kwargs):
        """Called from `assemble` to create the :class:`WidgetFactory` to use when the framework
           needs to create a Widget for use as the page for this UserInterface. Pass the class of
           Widget that will be constructed in `widget_class`.  Next, pass all the arguments that should
           be passed to `widget_class` upon construction, except the first one (its `view`).
        """
        ArgumentCheckedCallable(widget_class, explanation='define_page was called with arguments that do not match those expected by %s' % widget_class).checkargs(NotYetAvailable('view'), *args, **kwargs)

        self.page_factory = widget_class.factory(*args, **kwargs)
        return self.page_factory

    def define_error_view(self, page):
        self.error_view_factory = self.define_view('/error', _('Error'), page=page)

    def define_default_error_view(self):
        if self.page_factory:
            self.define_error_view(self.page_factory.get_error_page_factory())
        else:
            self.define_error_view(Widget.factory().get_error_page_factory())

    def get_bookmark_for_error(self, message, error_source_bookmark):
        return self.error_view_factory.as_bookmark(self) + self.error_view_factory.page_factory.widget_class.get_widget_bookmark_for_error(message, error_source_bookmark)

    def page_slot_for(self, view, page, local_slot_name):
        if page.created_by is self.page_factory:
            return local_slot_name
        try:
            name = self.slot_map[local_slot_name]
        except KeyError:
            message = 'When trying to plug %s into %s: slot "%s" of %s is not mapped. Mapped slots: %s' % \
                (view, page, local_slot_name, self, self.slot_map.keys())
            raise ProgrammerError(message)
        if not self.parent_ui:
            return name
        return self.parent_ui.page_slot_for(view, page, name)

    def split_fields_and_hardcoded_kwargs(self, assemble_args):
        fields = {}
        hardcoded = {}
        for name, value in assemble_args.items():
            if isinstance(value, Field):
                fields[name] = value
            else:
                hardcoded[name] = value
        return fields, hardcoded

    def define_view(self, relative_path, title=None, page=None, detour=False, view_class=None, read_check=None, write_check=None, cacheable=False, **assemble_args):
        """Called from `assemble` to specify how a :class:`View` will be created when the given URL (`relative_path`)
           is requested from this UserInterface.
        
           :keyword title: The title to be used for the :class:`View`.
           :keyword page: A :class:`WidgetFactory` that will be used as the page to be rendered for this :class:`View` (if specified).
           :keyword detour: If True, marks this :class:`View` as the start of a detour (A series of
             :class:`View`\s which can return the user to where the detour was first entered from). 
           :keyword view_class: The class of :class:`View` to be constructed (in the case of parameterised :class:`View` s).
           :keyword read_check: A no-arg function returning a boolean value. It will be called to determine whether the current 
             user is allowed to see this :class:`View` or not.
           :keyword write_check: A no-arg function returning a boolean value. It will be called to determine whether the current 
           :keyword cacheable: Whether this View can be cached.
             user is allowed to perform any actions linked to this :class:`View` or not.
           :keyword assemble_args: keyword arguments that will be passed to the `assemble` of this :class:`View` upon creation

           ..versionchanged:: 4.0
             Removed slot_definitions keyword argument, rather use :meth:`ViewFactory.set_slot`.
        """
        title = title or _('Untitled')
        path_argument_fields, passed_kwargs = self.split_fields_and_hardcoded_kwargs(assemble_args)

        view_class = view_class or UrlBoundView
        ArgumentCheckedCallable(view_class.assemble, '.define_view() was called with incorrect arguments for %s' % view_class.assemble).checkargs(NotYetAvailable('self'), **assemble_args)

        factory = ViewFactory(ParameterisedPath(relative_path, path_argument_fields), title,
                              page_factory=page, detour=detour, view_class=view_class, 
                              read_check=read_check, write_check=write_check, cacheable=cacheable, view_kwargs=passed_kwargs)
        self.add_view_factory(factory)
        return factory

    def define_regex_view(self, path_regex, path_template, view_class=None, factory_method=None, read_check=None, write_check=None, **assemble_args):
        """Called from `assemble` to create a :class:`ViewFactory` for a parameterised :class:`View` that will 
           be created when an URL is requested that matches `path_regex`. The arguments of the parameterised :class:`View`
           are parsed from a matching URL using named groups in `path_regex`. These named arguments are again 
           passed to the `assemble` of the :class:`View` upon construction.
        
           :param path_regex: The regex referring to the :class:`View`. It should contain a named group for each argument expected
             by the `assemble` method of the parameterised :class:`View`.
           :param path_template: A string containing a template which can be used to construct an actual URL, given the arguments
             of this parameterised :class:`View`. This string will be used to construct a :class:`string.Template`,
             and should contain references to variables named for each argument expexted by the `assemble` method
             of the parameterised :class:`View`.
           :keyword view_class: The class of :class:`View` which is to be constructed.
           :keyword factory_method: Pass a method that will be called to create a :class:`View` instead of passing `view_class` 
             if you'd like.
           :keyword read_check:
             Same as with `define_view`.
           :keyword write_check:
             Same as with `define_view`. 
           :keyword assemble_args:
             Same as with `define_view`.
        """
        path_argument_fields, passed_kwargs = self.split_fields_and_hardcoded_kwargs(assemble_args)

        if not factory_method:
            view_class = view_class or UrlBoundView
            ArgumentCheckedCallable(view_class.assemble, explanation='.define_regex_view() was called with incorrect arguments for %s' % view_class.assemble).checkargs(NotYetAvailable('self'), **assemble_args)

        factory = ViewFactory(RegexPath(path_regex, path_template, path_argument_fields), None,
                              view_class=view_class, factory_method=factory_method, read_check=read_check, write_check=write_check, **passed_kwargs)
        self.add_view_factory(factory)
        return factory

    def add_view_factory(self, view_factory):
        self.controller.add_view_factory(view_factory)
        return view_factory

    def define_transition(self, event, source, target, guard=None):
        """Creates a :class:`Transition` that will allow a user to be transitioned from `source` to `target` 
           (both of type :class:`ViewFactory`), upon the occurrence of an :class:`Event` that matches
           `event`.
        """
        return self.controller.define_transition(event, source, target, guard=guard)

    def define_return_transition(self, event, source, guard=None):
        """Creates a :class:`Transition` that returns a user to the :class:`View` the user was on
           before visiting a detour :class:`View`.
        """
        return self.controller.define_return_transition(event, source, guard=guard)

    def define_local_transition(self, event, source, guard=None):
        """Creates a :class:`Transition` that lets the user stay on the current :class:`View`.
        """
        return self.controller.define_local_transition(event, source, guard=guard)

    def define_redirect(self, relative_path, bookmark):
        """Defines an URL that will cause the user to be redirected to the given :class:`Bookmark` whenever
           visited."""
        def create_redirect_view(*args, **kwargs):
            return RedirectView(self, relative_path, bookmark)
        return self.add_view_factory(ViewFactory(RegexPath(relative_path, relative_path, {}), None, factory_method=create_redirect_view))

    def add_user_interface_factory(self, ui_factory):
        self.sub_uis.add(ui_factory)
        return ui_factory

    def define_user_interface(self, path, ui_class, slot_map, name=None, **assemble_args):
        """Called from `assemble` to specify how a :class:`UserInterface` will be created when the given path
           is visited in this :class:`UserInterface`.
           
           :param path: The path for which the :class:`UserInterface` will be constructed.
           :param ui_class: The class of :class:`UserInterface` which will be constructed.
           :param slot_map: The current :class:`UserInterface` defines contents for some :class:`Slots`. The `ui_class` :class:`UserInterface`
             which is effectively grafted onto the current :class:`UserInterface`, also defined :class:`Slots` using its own names.
             This dictionary states how the names used in the grafted :class:`UserInterface` map to the names used by the 
             current :class:`UserInterface`.
           :keyword name: A name for the :class:`UserInterface` that is grafted on. The name should be unique in an application.
           :keyword assemble_args: Keyword arguments that will be passed to the `assemble` method of the grafted :class:`UserInterface`
             after construction.
        """
        path_argument_fields, passed_kwargs = self.split_fields_and_hardcoded_kwargs(assemble_args)
        ArgumentCheckedCallable(ui_class.assemble, explanation='.define_user_interface() was called with incorrect arguments for %s' % ui_class.assemble).checkargs(NotYetAvailable('self'), **assemble_args)

        ui_factory = UserInterfaceFactory(self, ParameterisedPath(path, path_argument_fields), slot_map, ui_class, name, **passed_kwargs)
        self.add_user_interface_factory(ui_factory)
        return ui_factory

    def define_regex_user_interface(self, path_regex, path_template, ui_class, slot_map, name=None, **assemble_args):
        """Called from `assemble` to create a :class:`UserInterfaceFactory` for a parameterised :class:`UserInterface` that will 
           be created when an URL is requested that matches `path_regex`. See also `define_regex_view`.
           
           Arguments are similar to that of `define_regex_view`, except for:
           
           :param slot_map: (See `define_user_interface`.)
           :keyword name: (See `define_user_interface`.)
        """
        path_argument_fields, passed_kwargs = self.split_fields_and_hardcoded_kwargs(assemble_args)
        ArgumentCheckedCallable(ui_class.assemble, explanation='.define_regex_user_interface() was called with incorrect arguments for %s' % ui_class.assemble).checkargs(NotYetAvailable('self'), **assemble_args)

        regex_path = RegexPath(path_regex, path_template, path_argument_fields)
        ui_factory = UserInterfaceFactory(self, regex_path, slot_map, ui_class, name, **passed_kwargs)
        self.add_user_interface_factory(ui_factory)
        return ui_factory

    def get_user_interface_for_full_path(self, full_path):
        relative_path = self.get_relative_path_for(full_path)
        matching_sub_ui = self.sub_uis.get(relative_path)
        if matching_sub_ui:
            target_ui, factory =  matching_sub_ui.get_user_interface_for_full_path(full_path)
            return (target_ui, factory or self.page_factory)
        return self, self.page_factory

    def define_static_directory(self, path):
        """Defines an URL which is mapped to a directory from which files will be served directly.
           The URL is mapped to a similarly named subdirectory of the `static root` of the web application,
           as configured by the setting `web.static_root`.
        """
        ui_name = 'static_%s' % path
        ui_factory = UserInterfaceFactory(self, RegexPath(path, path, {}), IdentityDictionary(), StaticUI, ui_name, files=DiskDirectory(path))
        return self.add_user_interface_factory(ui_factory)

    def define_static_files(self, path, files):
        """Defines an URL which is mapped to serve the list of static files given.
        """
        ui_name = 'static_%s' % path
        ui_factory = UserInterfaceFactory(self, RegexPath(path, path, {}), IdentityDictionary(), StaticUI, ui_name, files=FileList(files))
        return self.add_user_interface_factory(ui_factory)

    def get_relative_path_for(self, full_path):
        if self.base_path == '/':
            return full_path
        return full_path[len(self.base_path):]
    
    def get_absolute_url_for(self, relative_path):
        if self.base_path == '/':
            new_path = relative_path
        else:
            new_path = self.base_path+relative_path
        url = Url(new_path).as_network_absolute()
        url.make_locale_absolute()
        return url

    @arg_checks(relative_path=IsInstance(str))
    def get_bookmark(self, description=None, relative_path=None, query_arguments=None, ajax=False):
        """Returns a :class:`Bookmark` for the :class:`View` present on `relative_path`.
        
           :keyword description: By default the :class:`Bookmark` will use the title of the target :class:`View` as 
             its description, unless overridden by passing `description`.
           :keyword query_arguments: A dictionary containing arguments that should be put onto the query string of the
             Url of the Bookmark.
           :keyword ajax: Links to Bookmarks for which ajax=True are changed browser-side to enable
             ajax-related functionality. This is used by the framework and is not meant
             to be set by a programmer.
        """
        view = self.view_for(relative_path)
        if not view.exists:
            raise ProgrammerError('no such bookmark (%s)' % relative_path)
        return view.as_bookmark(description=description, query_arguments=query_arguments, ajax=ajax)

    def get_view_for_full_path(self, full_path):
        relative_path = self.get_relative_path_for(full_path)
        if relative_path:
            view = self.view_for(relative_path)
        else:
            view = UserInterfaceRootRedirectView(self)
        return view

    def view_for(self, relative_path, for_bookmark=False):
        return self.controller.view_for(relative_path, for_bookmark=for_bookmark)


class StaticUI(UserInterface):
    def create_view(self, relative_path, user_interface, file_path=None):
        return FileView(user_interface, self.files.create(file_path))

    def assemble(self, files=None):
        self.files = files
        self.define_regex_view('(?P<file_path>.*)', '${file_path}', factory_method=self.create_view, file_path=Field())


class Bookmark:
    """Like a bookmark in a browser, an instance of this class is a way to refer to a View in a WebApplication
       that takes into account where the View is relative to the root of the URL hierarchy of the application.
    
       Bookmark should not generally be constructed directly by a programmer, use one of the following to
       obtain a Bookmark:
       
       - :meth:`UrlBoundView.as_bookmark`
       - :meth:`ViewFactory.as_bookmark`
       - :meth:`UserInterface.get_bookmark`
       - :meth:`Bookmark.for_widget`
       
       :param base_path: The entire path of the UserInterface to which the target View belongs.
       :param relative_path: The path of the target View, relative to its UserInterface.
       :param description: The textual description to be used by links to the target View.
       :keyword query_arguments: A dictionary containing name, value mappings to be put onto the query string of the href of this Bookmark.
       :keyword ajax: (not for general use).
       :keyword detour: Set this to True, to indicate that the target View is marked as being a detour (See :class:`UrlBoundView`).
       :keyword exact: (not for general use).
       :keyword locale: Force the Bookmark to be for a page in the given locale, instead of using the current locale (default).
       :keyword read_check: A no-args callable, usually the read_check of the target View. If it returns True, the current user will be allowed to see (but not click) links representing this Bookmark.
       :keyword write_check: A no-args callable, usually the write_check of the target View. If it returns True, the current user will be allowed to click links representing this Bookmark.

       .. versionchanged:: 3.2
          Added the locale kwarg.

    """
    @classmethod
    def for_widget(cls, description, query_arguments=None, **bookmark_kwargs):
        """Creates a "page-internal" Bookmark for a Widget with the arguments as specified.
        
           :param description: The textual description that will be used in links created for this Bookmark.
           :keyword query_arguments: A dictionary containing the arguments the target Widget should have when a user
                                   follows a link.
           :keyword bookmark_kwargs: Keyword arguments sent as-is to the constructor of Bookmark.
        """
        return Bookmark('', '', description, query_arguments=query_arguments, ajax=True, **bookmark_kwargs)

    def __init__(self, base_path, relative_path, description, query_arguments=None, ajax=False, detour=False, exact=True, locale=None, read_check=None, write_check=None):
        self.base_path = base_path
        self.relative_path = relative_path
        self.description = description
        self.query_arguments = query_arguments or {}
        self.ajax = ajax
        self.detour = detour
        self.exact = exact
        self.locale = locale
        self.read_check = read_check
        self.write_check = write_check

    def with_description(self, description):
        """Returns a new Bookmark, like this one, except that it has `description` for its description."""
        return Bookmark(self.base_path, self.relative_path, description, query_arguments=self.query_arguments, ajax=self.ajax,
                        detour=self.detour, read_check=self.read_check, write_check=self.write_check)

    @property
    def href(self):
        path = (self.base_path + self.relative_path).replace('//','/')
        url = Url(path)
        query_arguments = OrderedDict(sorted(self.query_arguments.items()))
        url.set_query_from(query_arguments)
        if self.detour:
            request = ExecutionContext.get_context().request
            if not url.is_currently_active(exact_path=True):
                query_arguments['returnTo'] = request.url
            elif 'returnTo' in request.params:
                query_arguments['returnTo'] = request.params['returnTo']
                
        url.make_locale_absolute(locale=self.locale)
        url.set_query_from(query_arguments)
        return url

    @property
    def is_page_internal(self):
        """Answers whether this Bookmark is for a Widget on the current page only."""
        return self.ajax and not (self.base_path or self.relative_path)

    def on_view(self, view):
        """For page-internal Bookmarks, answers a new Bookmark which is to the current Bookmark, but on the given View.
        
        .. versionadded:: 3.2
        """
        if view is view.user_interface.current_view:
            request = ExecutionContext.get_context().request
            query_arguments = request.GET
        else:
            query_arguments = {}
        return view.as_bookmark(query_arguments=query_arguments) + self
        
    def combine_checks(self, own_check, other_check):
        def combined_check():
            own_passes = not own_check or own_check()
            other_passes = not other_check or other_check()
            return all([own_passes, other_passes])
        return combined_check

    def __add__(self, other):
        """You can add a page-internal Bookmark to the Bookmark for a View."""
        if not other.is_page_internal:
            raise ProgrammerError('only page-internal Bookmarks can be added to other bookmarks')
        query_arguments = {}
        query_arguments.update(self.query_arguments)
        query_arguments.update(other.query_arguments)
        return Bookmark(self.base_path, self.relative_path, other.description, query_arguments=query_arguments,
                        ajax=other.ajax, detour=self.detour, 
                        read_check=self.combine_checks(self.read_check, other.read_check), 
                        write_check=self.combine_checks(self.write_check, other.write_check))

class RedirectToScheme(HTTPSeeOther):
    def __init__(self, scheme):
        self.scheme = scheme
        super().__init__(location=str(self.compute_target_url()))

    def compute_target_url(self):
        context = ExecutionContext.get_context()
        url = Url(context.request.url)
        url.set_scheme(self.scheme)
        return url


class Redirect(HTTPSeeOther):
    """An exception that can be raised by a :class:`ViewPreCondition` to send the user to a different
       View (matching `target`, a ViewFactory).
    """
    def __init__(self, target):
        self.target = target
        super().__init__(location=str(self.compute_target_url()))
     
    def compute_target_url(self):
        return self.target.href.as_network_absolute()


class Detour(Redirect):
    """An exception that can be raised by a :class:`ViewPreCondition` to send the user temporarily to a different
       View (matching `target`, a ViewFactory). If `return_to` (also a ViewFactory) is specified, and a user triggers
       a :class:`Return`, the user will be returned to a View matching `return_to`. If `return_to` is
       not specified, the user will be returned to the View for which the :class:`ViewPreCondition` failed initially.
    """
    def __init__(self, target, return_to=None):
        self.return_to = return_to or ReturnToCurrent()
        super().__init__(target)

    def compute_target_url(self):
        redirect_url = super().compute_target_url()
        qs = redirect_url.get_query_dict()
        qs['returnTo'] = [str(self.return_to.href.as_network_absolute())]
        redirect_url.set_query_from(qs, doseq=True)
        return redirect_url


class Return(Redirect):
    """An exception that can be raised by a :class:`ViewPreCondition` to send the user back to a View which originally
       failed a PreCondition that sent the user elsewhere via a :class:`Detour`.
    """
    def __init__(self, default):
        super().__init__(ReturnToCaller(default))


class WidgetList(list):
    def render(self):
        return ''.join([child.render() for child in self])

    def get_js(self, context=None):
        js = []
        for child in self:
            js.extend(child.get_js(context=context))
        return js

    @property
    def is_security_sensitive(self):
        for child in self:
            if child.is_security_sensitive:
                return True
        return False


class Layout:
    """A Layout is used to change what a Widget looks like by (e.g.) changing what css classes are used
       by the Widget, or by letting you add children to a Widget in customised ways.
    """

    def __init__(self):
        self.widget = None

    @property
    def view(self):
        return self.widget.view

    def apply_to_widget(self, widget):
        if self.widget:
            raise ProgrammerError('Already used by %s' % self.widget)
        self.widget = widget
        self.customise_widget()

    def customise_widget(self):
        """Override this method in subclasses to allow your Layout to change its Widget upon construction.
           There is no need to call super(), as the superclass implementation does nothing.
        """
        pass



class Widget:
    """Any user interface element in Reahl is a Widget. A direct instance of this class will not display anything when rendered. 
       A User interface is composed of Widgets by adding other Widgets to a Widget such as this one,
       forming a whole tree of Widgets.
    
       :param view: The current View.
       :keyword read_check: A no-arg callable. If it returns True, the Widget will be rendered for the current user, else not.
       :keyword write_check: A no-arg callable. If it returns True, the current user is allowed to write to this Widget.
                        The act of writing to a Widget is defined differently for subclasses of Widget. On this high level,
                        the Widget will also merely be displayed to the user if the user can write to the Widget.
    """
    exists = True
    @classmethod
    def factory(cls, *widget_args, **widget_kwargs):
        """Obtains a Factory for this Widget. A Factory for this Widget is merely an object that will be used by the 
           framework to instantiate the Widget only once needed. Pass the exact arguments and keyword arguments 
           that you would have passed to the Widget's constructor, except the very first argument of Widgets: the `view`.
        """
        return WidgetFactory(cls, *widget_args, **widget_kwargs)

    @classmethod
    def get_error_page_factory(cls, *widget_args, **widget_kwargs):
        return PlainErrorPage.factory()

    @arg_checks(view=IsInstance('reahl.web.fw:View'))
    def __init__(self, view, read_check=None, write_check=None):
        self.children = WidgetList()         #: All the Widgets that have been added as children of this Widget,
                                             #: in order of being added.
        self.view = view                     #: The current view, as passed in at construction
        self.priority = None
        self.mime_type = 'text/html'
        self.encoding = 'utf-8'
        self.default_slot_definitions = {}
        self.slot_contents = {}
        self.marked_as_security_sensitive = False
        self.set_arguments()
        self.read_check = read_check         #:
        self.write_check = write_check       #:
        self.created_by = None               #: The factory that was used to create this Widget
        self.layout = None                   #: The Layout used for visual layout of this Widget
        
    def use_layout(self, layout):
        """Attaches the given Layout to this Widget. The Layout is also given a chance to customise the Widget.
        
           Returns the original (modified) Widget for convenience.
        
           :param layout: A Layout to be used in the construction of this Widget.
        """
       
        if self.layout: 
            raise ProgrammerError('Already using a layout: %s' % self.layout)
        self.layout = layout
        self.layout.apply_to_widget(self)
        return self

    def set_creating_factory(self, factory):
        self.created_by = factory

    @property
    def is_refresh_enabled(self):
        return False

    def fire_on_refresh(self):
        pass

    query_fields = ExposedNames() 
    """Used to declare the arguments of this Widget on its class.

       Override this class attribute to declare arguments this Widget, each described
       by a :class:`~reahl.component.modelinterface.Field`. 

       When constructed, the Widget uses the names and validation details of each Field to 
       parse values for its arguments from the current query string. The resultant
       argument values are set as attributes on this Widget (with names matching the argument names).

       To declare arguments on your own Widget class, assign a ExposedNames instance to query_fields
       and then assign a single-argument callable for each Widget argument to it. This callable
       will be called with the Widget instance as argument, and should return a 
       :class:`~reahl.component.modelinterface.Field` describing it::

          class MyWidget(Widget):
              query_fields = ExposedNames()
              query_fields.my_argument = lambda i: Field()


       .. versionchanged:: 6.1
          This used to be set up using a method using an :class:`~reahl.component.modelinterface.exposed` decorator.

    """
    
    def get_concurrency_hash_digest(self):
        if not self.visible:
            return ''

        if ExecutionContext.get_context().config.web.debug_concurrency_hash:
            return self.get_concurrency_hash_digest_debug()

        concurrency_hash = hashlib.md5()
        is_empty = True
        for value in self.get_concurrency_hash_strings():
            is_empty = False
            concurrency_hash.update(value.encode('utf-8'))
        if is_empty:
            return ''
        else:
            concurrency_hash.update(str(self.disabled).encode('utf-8'))
            return concurrency_hash.hexdigest()

    def get_concurrency_hash_digest_debug(self):
        concurrency_hash = self.get_concurrency_hash_strings()

        if not concurrency_hash:
            return ''
        else:
            return '-'.join(list(concurrency_hash)+[str(self.disabled)])

    def get_concurrency_hash_strings(self):
        """Yields one or more strings representing the database value of this Widget. 

           This is used to determine whether or not the database has changed since a page was rendered, because if
           it did, the page is considered out of date and needs to be refreshed.

           By default only :class:`~reahl.web.ui.Input` participate in this algorithm, but you may override
           this method for your :class:`Widget` subclass to make it participate as well - presuming it
           can somehow be related to a value in the database.

           .. versionadded:: 5.0
        """
        for child in self.children:
            digest = child.get_concurrency_hash_digest()
            if digest:
                yield digest

    @property
    def has_changed_since_initial_view(self):
        return False

    @property
    def coactive_widgets(self):
        return [widget for child in self.children for widget in child.coactive_widgets]

    @property
    def ancestral_coactive_widgets(self):
        return []

    def accept_disambiguated_input(self, disambiguated_input):
        self.query_fields.accept_input(disambiguated_input, ignore_validation=True)

    def update_construction_state(self, disambiguated_input):
        for field in self.query_fields.values():
            field.update_valid_value_in_disambiguated_input(disambiguated_input)

    def set_arguments(self):
        widget_arguments = self.view.get_construction_state()
        self.query_fields.accept_input(widget_arguments, ignore_validation=True)

    def add_default_slot(self, slot_name, widget_factory):
        """If this Widget contains a :class:`Slot` named `slot_name`, and no contents are available to be plugged into
           this Slot, the given `widget_factory` will be used to populate the Slot by default.
        """
        self.default_slot_definitions[slot_name] = widget_factory
        return widget_factory

    def set_as_security_sensitive(self):
        """Call this method to explicitly mark this Widget as being security sensitive. It may be necessary to call 
           this method when the automatic mechanisms for determining the security sensitivity of a Widget do not suffice.
        """
        self.marked_as_security_sensitive = True

    @property
    def is_security_sensitive(self):
        """Answers whether this Widget should be secured when communicating with the user browser."""
        return self.marked_as_security_sensitive or\
               self.read_check_is_specified or\
               self.children.is_security_sensitive

    @property
    def read_check_is_specified(self):
        return self.read_check and hasattr(self.read_check, 'is_specified') and self.read_check.is_specified

    def set_priority(self, secondary=None, primary=None):
        if primary: 
            self.priority = 'primary'
        elif secondary:
            self.priority = 'secondary'

    @arg_checks(child=IsInstance('reahl.web.fw:Widget'))
    def add_child(self, child):
        """Adds another Widget (`child`) as a child Widget of this one. 
        
        :returns: the added child for convenience."""
        self.children.append(child)
        return child
        
    @arg_checks(child=IsInstance('reahl.web.fw:Widget'))
    def insert_child(self, index, child):
        """Adds another Widget (`child`) as a child Widget of this one, at `index` position amongst existing children."""
        self.children.insert(index, child)
        return child

    def add_children(self, children):
        """Adds all Widgets in `children` children Widgets of this one. 

        :returns: the list of added children for convenience."""
        for child in children:
            self.add_child(child)
        return children

    def clear_children(self):
        self.children[:] = []

    def render_contents(self):
        return self.children.render()

    def render(self):
        """Returns an HTML representation of this Widget. (Not for general use, may be useful for testing.)"""
        if self.visible:
            return self.render_contents()
        else:
            return ''

    def can_read(self):
        return (not self.read_check) or self.read_check()

    def can_write(self):
        return self.can_read() and ((not self.write_check) or self.write_check())
        
    @property   
    def disabled(self):
        """Answers whether this Widget should be rendered to the current user in such a way that the user will
           see the Widget, but not be able to interact with it."""
        return not self.can_write()

    @property
    def visible(self):
        """Answers whether this Widget should be rendered to the current user at all."""
        return self.can_write() or self.can_read()

    def get_contents_js(self, context=None):
        return self.children.get_js(context=context)

    def render_contents_js(self):
        js = set(self.get_contents_js(context='#%s' % self.css_id))
        result = '<script type="text/javascript">' 
        result += ''.join(sorted(js))
        result += '</script>'
        return result

    def get_js(self, context=None):
        """Override this method if your Widget needs JavaScript to be activated on the browser side."""
        return self.get_contents_js(context=context)
    
    @property
    def user_interface(self):
        """The current UserInterface."""
        return self.view.user_interface

    @property
    def controller(self):
        return self.view.controller
    
    def define_event_handler(self, event, target=None):
        """Defines (and returns) an :class:`EventHandler` that will allow an Event matching `event` from
           any View on which this Widget is placed. If given, the user will be transitioned to a View 
           matching `target` (a ViewFactory) in response to the Event.
        """
        return self.controller.define_event_handler(event, target=target)

    def check_slots(self, view):
        slots_to_plug_in = {self.user_interface.page_slot_for(view, self, local_slot_name)
                                for local_slot_name in view.slot_definitions.keys()}
        slots_available = set(self.available_slots)
        if not slots_to_plug_in.issubset(slots_available):
            invalid_slots = slots_to_plug_in - slots_available
            invalid_slots = ','.join(invalid_slots)
            available_slots = ','.join(slots_available)

            message = 'An attempt was made to plug Widgets into the following slots that do not exist on page %s: %s\n' % (self, invalid_slots)
            message += '(expected one of these slot names: %s)\n' % available_slots
            message += 'View %s plugs in the following:\n' % view
            for local_slot_name, factory in view.slot_definitions.items():
                page_slot_name = self.user_interface.page_slot_for(view, self, local_slot_name)
                message += '%s is plugged into slot "%s", which is mapped to slot "%s"' % \
                (factory, local_slot_name, page_slot_name)

            raise ProgrammerError(message)

    def parent_widget_pairs(self, own_parent_set):
        yield self, own_parent_set
        children_parent_set = own_parent_set.union({self})

        for child in self.children:
            for widget, parent_set in child.parent_widget_pairs(children_parent_set):
                yield widget, parent_set    

    def contained_widgets(self):
        for child in self.children:
            yield child
            for widget in child.contained_widgets():
                yield widget

    @property
    def is_runtime_checking_enabled(self):
        config = ExecutionContext.get_context().config
        return config.reahlsystem.runtime_checking_enabled

    is_Form = False
    is_Input = False
    def check_form_related_programmer_errors(self):
        inputs = []
        forms = []

        for widget in itertools.chain([self], self.contained_widgets()):
            if widget.is_Form:
                forms.append(widget)
            elif widget.is_Input:
                inputs.append(widget)

        self.check_forms_unique(forms)
        self.check_all_inputs_forms_exist(forms, inputs)

    def check_all_inputs_forms_exist(self, forms_found_on_page, inputs_on_page):
        for i in inputs_on_page:
            if i.form not in forms_found_on_page:
                message = 'Could not find form for %s. Its form, %s is not present on the current page' \
                          % (str(i), str(i.form))
                raise ProgrammerError(message)

    def check_forms_unique(self, forms):
        checked_forms = {}
        for form in forms:
            if form.css_id not in checked_forms.keys():
                checked_forms[form.css_id] = form
            else:
                existing_form = checked_forms[form.css_id]
                message = 'More than one form was added using the same unique_name: %s and %s' % (form, existing_form)
                raise ProgrammerError(message)

    def plug_in(self, view):
        self.check_slots(view)
        
        for local_slot_name, widget_factory in view.slot_definitions.items():
            self.slot_contents[self.user_interface.page_slot_for(view, self, local_slot_name)] = widget_factory.create(view)
        for slot_name, widget_factory in self.default_slot_definitions.items():
            if slot_name not in self.slot_contents.keys():
                self.slot_contents[slot_name] = widget_factory.create(view)
        self.slot_contents['reahl_header'] = HeaderContent(self)
        self.slot_contents['reahl_footer'] = FooterContent(self)
        self.fill_slots(self.slot_contents)
        self.attach_out_of_bound_widgets(view.out_of_bound_widgets)
        if self.is_runtime_checking_enabled:
            self.check_form_related_programmer_errors()

    @property
    def available_slots(self):
        slots = {}
        for child in self.children:
            slots.update(child.available_slots)
        return slots
    
    def fill_slots(self, slot_contents):
        for name, slot in self.available_slots.items():
            widget = slot_contents.get(name, None)
            if widget:
                slot.fill(widget)

    def attach_out_of_bound_widgets(self, widgets):
        for child in self.children:
            child.attach_out_of_bound_widgets(widgets)

    def get_out_of_bound_container(self):
        container = [widget for widget in [child.get_out_of_bound_container() for child in self.children]
                          if widget]
        if not container:
            return None
        assert len(container) == 1
        return container[0]


class ErrorWidget(Widget):
    query_fields = ExposedNames()
    query_fields.error_message = lambda i: Field(default=_('An error occurred'))
    query_fields.error_source_href = lambda i: Field(default='#')

    @classmethod
    def get_widget_bookmark_for_error(cls, error_message, error_source_bookmark):
        return Bookmark.for_widget('', query_arguments={'error_message': error_message, 'error_source_href': error_source_bookmark.href if error_source_bookmark else ''})


class PlainErrorPage(ErrorWidget):
    def render_contents(self):
        return u'''<html><head><title>Error</title></head>
                         <body><h1>An error occurred:</h1> <p>%s <a href="%s">Ok</a></p></body>
                   </html>''' % (self.error_message, self.error_source_href)



class ViewPreCondition:
    """A ViewPreCondition can be used to control whether a user can visit a particular View or not. If the 
       `condition_callable` returns False, `exception` will be raised. Useful exceptions exist, like :class:`Detour` 
       and :class:`Return`.
       
       :param condition_callable: A no-arg callable indicating whether this condition is satisfied (returns True) 
                                  or not (returns False).
       :keyword exception: An exception to be raised if this condition is not satisfied.
    """
    def __init__(self, condition_callable, exception=Exception()):
        self.condition_callable = condition_callable
        self._exception = exception
    
    @property
    def exception(self):
        return self._exception

    def is_true(self, *args, **kwargs):
        return self.condition_callable(*args, **kwargs)

    def check(self, *args, **kwargs):
        if not self.is_true(*args, **kwargs):
            request = ExecutionContext.get_context().request
            if request.method.lower() not in ['get', 'head']:
                raise HTTPNotFound()
            raise self.exception

    def negated(self, exception=None):
        def condition_callable(*args, **kwargs):
            return not self.condition_callable(*args, **kwargs)
        return ViewPreCondition(condition_callable, exception or self.exception)


class RatedMatch:
    def __init__(self, match, rating):
        self.match = match
        self.rating = rating


class RegexPath:
    """Represents a relative path of the URL of a parameterised View. The path is a combination of
       path elements and values for arguments to the View that are embedded in the path.
       
       :param regex: If a given path string has to be matched against this RegexPath, the string `regex` is used
                     as a regular expression to check for a match, and also to identify the input for the argument values
                     embedded in the URL path. As such, the regular expression in `regex` should contain a group named 
                     for each parameter of the View (as named in `argument_fields`.
       :param template: A string containing a `PEP-292 <http://www.python.org/dev/peps/pep-0292/>`_ template which
                        is used to form an URL, given values for all the arguments of the View. The template should contain
                        a variable expansion for each parameter of the View (as named in `argument_fields`).
       :param argument_fields: A dictionary which maps argument names of the View to instances of 
                               :class:`reahl.component.modelinterface.Field` that can be used to input (and parse)
                               or output the argument values of the View. 
    """
    def __init__(self, regex, template, argument_fields):
        self.regex = regex
        self.template = template
        self.argument_fields = argument_fields

    def __hash__(self):
        return hash(self.regex)

    def parse_arguments(self, relative_path):
        return self.parse_arguments_from_fields(self.argument_fields, relative_path)

    def get_base_part_in(self, relative_path):
        return self.match_foreign_view(relative_path).match.group('base_path')

    def get_relative_part_in(self, relative_path):
        return self.match_foreign_view(relative_path).match.group('relative_path')

    def has_relative_part_in(self, relative_path):
        matched = self.match_foreign_view(relative_path).match
        return (matched and matched.group('relative_path')) is not None

    def get_relative_path_from(self, arguments):
        arguments_as_input = self.get_arguments_as_input(arguments)
        return string.Template(self.template).substitute(arguments_as_input)

    def match(self, relative_path):
        match = re.match(self.regex, relative_path)
        rating = 1 if match else 0
        return RatedMatch(match, rating)

    def match_view(self, relative_path):
        view_regex = '(?P<view_path>^%s)(/?_.*)?(\?.*)?$' % self.regex  # Note: if the path_regex ends in / the / in the last bit should not be
                                                   #       there, else it should. I don't know how to make this more precise.
        match = re.match(view_regex, relative_path)
        rating = len(match.group('view_path')) if match else 0
        return RatedMatch(match, rating)

    def match_foreign_view(self, relative_path):
        own_path = '' if self.regex == '/' else self.regex
        foreign_view_regex = '^(?P<base_path>%s)(?P<relative_path>/.*(/?_.*)?(\?.*)?)?$' % own_path  # Note: if the path_regex ends in / the / in the last bit should not be
                                                   #       there, else it should. I don't know how to make this more precise.
        match = re.match(foreign_view_regex, relative_path)
        rating = len(match.group('base_path'))+1 if match else 0
        return RatedMatch(match, rating)

    def get_temp_url_argument_field_index(self, for_fields, data_dict=None):
        data_dict = data_dict or {}
        fields = StandaloneFieldIndex(data_dict)
        fields.update_copies(for_fields)
        return fields

    def parse_arguments_from_fields(self, for_fields, relative_path):
        if not for_fields:
            return {}
        assert isinstance(relative_path, str) # Scaffolding for Py3 port
        matched_arguments = self.match(relative_path).match.groupdict()
        fields = self.get_temp_url_argument_field_index(for_fields)

        raw_input_values = MultiDict()
        raw_input_values.update([(argument_name, urllib.parse.unquote(value or ''))
                                 for argument_name, value in matched_arguments.items()])
        fields.accept_input(raw_input_values.dict_of_lists())
        return fields.as_kwargs()

    def get_arguments_as_input(self, arguments):
        fields = self.get_temp_url_argument_field_index(self.argument_fields, arguments)
        fields.validate_defaults()
        return fields.as_input_kwargs()


class ParameterisedPath(RegexPath):
    """Represents a relative path of the URL of a View which is parameterised. The first element of such a
       path (its `discriminator`) is a chosen URL. Subsequent path elements of the path are the values for 
       the arguments of the parameterised View, embedded in the path.
       
       
       :param discriminator: The first element of a ParameterisedPath, used to match it against an URL in a string.
       :param argument_fields: A dictionary which maps argument names of the View to instances of 
                               :class:`reahl.component.modelinterface.Field` that can be used to input (from an URL) 
                               or output (to an URL) the arguments of the View. 
    """
    def __init__(self, discriminator, argument_fields):
        regex = self.make_regex(discriminator, argument_fields)
        template = self.make_template(discriminator, argument_fields)
        super().__init__(regex, template, argument_fields)

    def make_regex(self, discriminator, argument_fields):
        arguments_part = ''
        for argument_name in argument_fields.keys():
            arguments_part += '(/(?P<%s>[^/]*))' % argument_name

        if discriminator.endswith('/') and arguments_part.startswith('(/'):
            arguments_part = arguments_part[:1]+arguments_part[2:]
        return discriminator+arguments_part

    def make_template(self, discriminator, argument_fields):
        arguments_part = ''
        for argument_name in argument_fields.keys():
            arguments_part += '/${%s}' % argument_name

        if discriminator.endswith('/') and arguments_part.startswith('(/'):
            arguments_part = arguments_part[:1]+arguments_part[2:]
        return discriminator+arguments_part


class Factory:
    def __init__(self, factory_method):
        super().__init__()
        self.factory_method = factory_method

    def create(self, *args, **kwargs):
        return self.factory_method(*args, **kwargs)


class FactoryFromUrlRegex(Factory):
    def __init__(self, regex_path, factory_method, factory_kwargs):
        self.regex_path = regex_path
        self.factory_kwargs = factory_kwargs
        super().__init__(factory_method)

    def create(self, relative_path, *args, **kwargs):
        try:
            create_kwargs = self.create_kwargs(relative_path, **kwargs)
            create_args = self.create_args(relative_path, *args)
            return super().create(*create_args, **create_kwargs)
        except TypeError as ex:
            if len(inspect.trace()) == 1:
                # Note: we modify the args, and then just raise, because we want the original stack trace
                ex.args = (ex.args[0]+' (from regex "%s")' % self.regex_path.regex,)
            raise

    def is_applicable_for(self, relative_path):
        return self.regex_path.match_view(relative_path).rating

    def create_kwargs(self, relative_path, **kwargs):
        create_kwargs = {}
        create_kwargs.update(kwargs)
        create_kwargs.update(self.regex_path.parse_arguments(relative_path))
        create_kwargs.update(self.factory_kwargs)
        return create_kwargs
    
    def create_args(self, relative_path, *args):
        return (relative_path,)+args


class UserInterfaceFactory(FactoryFromUrlRegex):
    @arg_checks(regex_path=IsInstance(RegexPath), ui_class=IsSubclass(UserInterface))
    def __init__(self, parent_ui, regex_path, slot_map, ui_class, ui_name, **ui_kwargs):
        super().__init__(regex_path, ui_class, ui_kwargs)
        self.slot_map = slot_map
        self.parent_ui = parent_ui
        self.ui_name = ui_name
        self.predefined_uis = []

    def __str__(self):
        return '<Factory for %s named %s>' % (self.factory_method, self.ui_name)

    def predefine_user_interface(self, ui_factory):
        self.predefined_uis.append(ui_factory)
        
    def get_relative_part_in(self, full_path):
        return self.regex_path.get_relative_part_in(full_path)

    def create(self, relative_path, for_bookmark=False, *args):
        user_interface = super().create(relative_path, for_bookmark, *args)
        for predefined_ui in self.predefined_uis:
            user_interface.add_user_interface_factory(predefined_ui)
        return user_interface 

    def create_from_url_args(self, for_bookmark=False, **url_args):
        relative_path = self.regex_path.get_relative_path_from(url_args)
        return self.create(relative_path, for_bookmark=for_bookmark)

    def create_args(self, relative_path, *args):
        relative_base_path = self.regex_path.get_base_part_in(relative_path) or '/'
        return (self.parent_ui, relative_base_path, self.slot_map)+args+(self.ui_name,)

    def get_bookmark(self, *ui_args, **bookmark_kwargs):
        ui_relative_path = self.regex_path.get_relative_path_from(ui_args)
        user_interface = self.create(ui_relative_path, for_bookmark=True) 
        return user_interface.get_bookmark(**bookmark_kwargs)

    def is_applicable_for(self, relative_path):
        return self.regex_path.match_foreign_view(relative_path).rating


class SubResourceFactory(FactoryFromUrlRegex):
    def __init__(self, regex_path, factory_method):
        super().__init__(regex_path, factory_method, {})

    def create_args(self, relative_path, *args):
        return args


class ViewFactory(FactoryFromUrlRegex):
    """Used to specify to the framework how it should create a
    :class:`View`, once needed. This class should not be instantiated
    directly. Programmers should use
    :meth:`UserInterface.define_view` and related methods to specify
    what Views a UserInterface should have. These methods return the
    ViewFactory so created.

    In the `.assemble()` of a UserInterface, ViewFactories are passed
    around to denote Views as the targets of Events or the source and
    target of Transitions.
    """
    def __init__(self, regex_path, title, slot_definitions=None, page_factory=None, detour=False, view_class=None, factory_method=None, read_check=None, write_check=None, cacheable=False, view_kwargs=None):
        self.detour = detour
        self.preconditions = []
        self.title = title
        self.slot_definitions = slot_definitions or {}
        self.view_class = view_class or UrlBoundView
        self.read_check = read_check
        self.write_check = write_check
        self.cacheable = cacheable
        self.page_factory = page_factory
        super().__init__(regex_path, factory_method or self.create_view, view_kwargs or {})

    def create_args(self, relative_path, *args):
        if SubResource.is_for_sub_resource(relative_path):
            relative_path = SubResource.get_view_path_for(relative_path)
        return (relative_path,)+args

    def create_view(self, relative_path, user_interface, **view_arguments):
        return self.view_class(user_interface, relative_path, self.title,
                               slot_definitions=dict(self.slot_definitions),
                               page_factory=self.page_factory,
                               detour=self.detour,
                               read_check=self.read_check,
                               write_check=self.write_check,
                               cacheable=self.cacheable,
                               **view_arguments)

    def __str__(self):
        return '<ViewFactory for %s>' % self.view_class

    def __hash__(self):
        return hash(self.regex_path)

    def __eq__(self, other):
        return hash(other) == hash(self)

    def get_relative_path(self, **arguments):
        """Returns a string containing the path this View would have relative to its UserInterface, 
           given the arguments passed.
        
           :kwarg url_arguments: Values for the arguments of the parameterised View to which the relative_path 
                                 should lead. (Just omit these if the target View is not parameterised.)
        """
        return self.regex_path.get_relative_path_from(arguments)

    def matches_view(self, view):
        return self.is_applicable_for(view.relative_path)

    def get_absolute_url(self, user_interface, **arguments):
        url = user_interface.get_absolute_url_for(self.get_relative_path(**arguments))
        url.query = self.get_query_string()
        return url

    def get_query_string(self):
        request = ExecutionContext.get_context().request
        return_to = request.GET.get('returnTo')
        if return_to:
            return urllib.parse.urlencode({'returnTo': return_to})
        return ''

    def add_precondition(self, precondition):
        """Adds the given precondition to the View that will be created by this ViewFactory. (See :class:`ViewPreCondition`.)"""
        self.preconditions.append(precondition)
        return precondition

    def set_slot(self, name, contents):
        """Supplies a Factory (`contents`) for how the contents of the :class:`Slot` named `name` should be created."""
        self.slot_definitions[name] = contents

    def set_page(self, page_factory):
        """Supplies a Factory for the page to be used when displaying the :class:`View` created by this ViewFactory."""
        self.page_factory = page_factory

    def as_bookmark(self, user_interface, description=None, query_arguments=None, ajax=False, locale=None, **url_arguments):
        """Returns a :class:`Bookmark` to the View this Factory represents.

           :param user_interface: The user_interface where this ViewFactory is defined.
           :keyword description: A textual description which will be used on links that represent the Bookmark on the user interface.
           :keyword query_arguments: A dictionary with (name, value) pairs to put on the query string of the Bookmark.
           :keyword ajax: (not for general use)
           :keyword locale: (See :class:`Bookmark`.)
           :keyword url_arguments: Values for the arguments of the parameterised View to which the Bookmark should lead. (Just
                                 omit these if the target View is not parameterised.)
        """
        relative_path = self.get_relative_path(**url_arguments)
        view = self.create(relative_path, user_interface)
        return view.as_bookmark(description=description, query_arguments=query_arguments, ajax=ajax, locale=locale)

    def create(self, relative_path, *args, **kwargs):
        try:
            instance = super().create(relative_path, *args, **kwargs)
        except ValidationConstraint as ex:
            message = 'The arguments contained in URL "%s" are not valid for %s: %s' % (relative_path, self, ex)
            raise ProgrammerError(message)
        for condition in self.preconditions:
            instance.add_precondition(condition)
        return instance


class WidgetFactory(Factory):
    """An object used by the framework to create a Widget, once needed.

       :param widget_class: The kind of Widget to be constructed.
       :param widget_args:  All the arguments needed by `widget_class` except the first argument of Widgets: `view`
       :keyword widget_kwargs: All the keyword arguments of `widget_class`.
    """
    def __init__(self, widget_class, *widget_args, **widget_kwargs):
        ArgumentCheckedCallable(widget_class, explanation='An attempt was made to create a WidgetFactory for %s with arguments that do not match what is expected for %s' % (widget_class, widget_class)).checkargs(NotYetAvailable('view'), *widget_args, **widget_kwargs)

        super().__init__(self.create_widget)
        self.widget_class = widget_class
        self.widget_args = widget_args
        self.widget_kwargs = widget_kwargs
        self.default_slot_definitions = {}
        self.layout = None

    def use_layout(self, layout):
        """If called on the factory, .use_layout will be called in the Widget created, passing along the given layout.

           :param layout: A layout to be used with the newly created Widget
        """
        self.layout = layout
        return self

    def create_widget(self, view):
        widget = self.widget_class(view, *self.widget_args, **self.widget_kwargs)
        if self.layout:
            widget.use_layout(self.layout)
        for name, widget_factory in self.default_slot_definitions.items():
            widget.add_default_slot(name, widget_factory)
        widget.set_creating_factory(self)
        return widget

    def add_default_slot(self, name, widget_factory):
        """Specify a `widget_factory` to be used to create the contents of the :class:`reahl.web.ui.Slot`
           named `name` if no contents are supplied by other means for the Slot.
        """
        self.default_slot_definitions[name] = widget_factory
        return widget_factory

    def get_error_page_factory(self):
        return self.widget_class.get_error_page_factory(*self.widget_args, **self.widget_kwargs)

    def __str__(self):
        return '<WidgetFactory for %s>' % self.widget_class


class ViewPseudoFactory(ViewFactory):
    def __init__(self, bookmark):
        super().__init__(RegexPath('/', '/', {}), '')
        self.bookmark = bookmark

    def matches_view(self, view):
        return False

    def get_absolute_url(self, user_interface, **arguments):
        return self.bookmark.href.as_network_absolute()


class PseudoBookmark:
    def as_view_factory(self):
        return ViewPseudoFactory(self)

class ReturnToCaller(PseudoBookmark):
    def __init__(self, default):
        self.default = default

    @property
    def href(self):
        request = ExecutionContext.get_context().request
        if 'returnTo' in request.GET:
            return Url(request.GET['returnTo'])
        return self.default.href


class ReturnToCurrent(PseudoBookmark):
    @property
    def href(self):
        url = Url(ExecutionContext.get_context().request.url)
        url.make_network_relative()
        return url



class View:
    """A View is how Reahl denotes the target of any URL. Although there are many types of View (to deal with static files, 
      for example), the most used View is an :class:`UrlBoundView`.
    """
    exists = True
    is_dynamic = False

    def __init__(self, user_interface):
        super().__init__()
        self.user_interface = user_interface

    @property
    def view(self):
        return self

    @property
    def controller(self):
        return self.user_interface.controller

    def check_precondition(self):
        pass

    def check_rights(self, request_method):
        pass

    def as_resource(self, page):
        raise HTTPNotFound()

    def as_factory(self):
        def return_self(*args, **kwargs):
            return self
        return Factory(return_self)

    def resource_for(self, full_path, page):
        return self.as_resource(page)

    def add_resource(self, resource):
        url = resource.get_url().as_locale_relative()
        relative_path = url.path
        self.add_resource_factory(SubResourceFactory(RegexPath(relative_path, relative_path, {}), lambda: resource))
        return resource
    
    def add_resource_factory(self, factory):
        self.user_interface.register_resource_factory(factory)
        return factory


class UrlBoundView(View):
    """A View that is rendered to the browser when a user visits a particular URL on the site. An UrlBoundView
       defines how the named Slots of a page Widget should be populated for a particular URL.

       A programmer *should* create subclasses of UrlBoundView when creating parameterised Views. These subclasses
       *should not* implement their own `__init__` methods, rather use `.assemble()` for customisation.

       A programmer *should not* construct instances of this class (or its subclasses). Rather use
       `UserInterface.define_view` and related methods to define ViewFactories which the framework will 
       use at the correct time to instantiate an UrlBoundView.

       The `.view` of any Widget is an instance of UrlBoundView.
    """
    is_dynamic = True

    def as_factory(self):
        regex_path = ParameterisedPath(self.relative_path, {})
        return ViewFactory(regex_path, self.title,
                           slot_definitions=dict(self.slot_definitions),
                           page_factory=self.page_factory,
                           detour=self.detour,
                           view_class=self.__class__,
                           read_check=self.read_check,
                           write_check=self.write_check,
                           cacheable=self.cacheable)

    def __init__(self, user_interface, relative_path, title, slot_definitions=None, page_factory=None, detour=False, read_check=None, write_check=None, cacheable=False, **view_arguments):
        if re.match('/_([^/]*)$', relative_path):
            raise ProgrammerError('you cannot create UrlBoundViews with /_ in them - those are reserved URLs for SubResources')
        super().__init__(user_interface)
        self.out_of_bound_widgets = []
        self.relative_path = relative_path
        self.title = title                          #: The title of this View
        self.preconditions = []       
        self.slot_definitions = slot_definitions or {}
        self.detour = detour
        self.read_check = read_check or self.allowed    #: The UrlBoundView will only be allowed to be viewed if this no-arg callable returns True.
        self.write_check = write_check or self.allowed  #: The UrlBoundView will only be allowed to receive user input if this no-arg callable returns True.
        self.cacheable = cacheable
        self.page_factory = page_factory
        self.page = None
        self.assemble(**view_arguments)
        self.cached_session_data = None

    def allowed(self):
        return True

    def assemble(self):
        """This method is called (on the UrlBoundView) each time after an UrlBoundView was created for use during
           a single request cycle. Its main purpose is to deliver the values of the arguments of a parameterised 
           UrlBoundView. To have a parameterised View, you have to subclass UrlBoundView and override `.assemble`, 
           giving it a signature with keyword arguments that match the arguments specified when defining the View.

           Inside `.assemble` you can change the title of the View, the contents of the Slots that will be 
           populated by the View, or even the security check functions of the View -- differently, depending on
           the actual argument values received by this method. You may also want to first do a database lookup,
           for example, based on the argument values before finalising these details of the View.

           If argument values are received here that are invalid (such as the primary key of a database row which
           turns out not to exist), raise a :class:`CannotCreate` exception to indicate that. Doing that will
           result in the browser receiving an HTTP 404 error.
        """

    def __str__(self):
        return '<UrlBoundView "%s" on "%s">' % (self.title, self.relative_path)

    def create_page(self, for_path, default_page_factory):
        page_factory = self.page_factory or default_page_factory
        if not page_factory:
            raise ProgrammerError('there is no page defined for %s' % for_path)
        self.page = page_factory.create(self)
        self.page.plug_in(self)
        return self.page

    def set_slot(self, name, contents):
        """Supplies a Factory (`contents`) for the framework to use to create the contents of the Slot named `name`."""
        self.slot_definitions[name] = contents

    def set_page(self, page_factory):
        """Supplies a Factory for the page to be used when displaying this View."""
        self.page_factory = page_factory

    def resource_for(self, full_path, page):
        if SubResource.is_for_sub_resource(full_path):
            return self.user_interface.sub_resource_for(full_path)
        return super().resource_for(full_path, page)

    def as_resource(self, page):
        return ComposedPage(self, page)

    def add_precondition(self, precondition):
        """Adds a :class:`ViewPreCondition` to this UrlBoundView. The View will only be accessible if 
           the ViewPreCondition is satisfied."""
        self.preconditions.append(precondition)
        return precondition

    def check_precondition(self):
        for precondition in self.preconditions:
            precondition.check()

    def check_rights(self, request_method):
        if request_method.upper() in ['GET','HEAD']:
            allowed = self.read_check()
        else:
            allowed = self.write_check()
        if not allowed:
            raise HTTPForbidden()

    @property
    def is_current_view(self):
        return self.relative_path == self.user_interface.current_view.relative_path and self.user_interface is self.user_interface.current_view.user_interface

    def as_bookmark(self, description=None, query_arguments=None, ajax=False, locale=None):
        """Returns a Bookmark for this UrlBoundView.

           :keyword description: A textual description to be used by links representing this View to a user.
           :keyword query_arguments: A dictionary mapping names to values to be used for query string arguments.
           :keyword ajax: (not for general use)
           :keyword locale: (See :class:`Bookmark`.)

        .. versionchanged:: 3.2
           Added locale kwarg.

        """
        return Bookmark(self.user_interface.base_path, self.relative_path, 
                        description=description or self.title,
                        query_arguments=query_arguments, ajax=ajax, detour=self.detour,
                        locale=locale,
                        read_check=self.read_check, write_check=self.write_check)

    def add_out_of_bound_widget(self, out_of_bound_widget):
        self.out_of_bound_widgets.append(out_of_bound_widget)
        return out_of_bound_widget

    @property
    def full_path(self):
        return self.as_bookmark().href.path

    @property
    def persisted_userinput_class(self):
        config = ExecutionContext.get_context().config
        return config.web.persisted_userinput_class

    @property
    def persisted_exception_class(self):
        config = ExecutionContext.get_context().config
        return config.web.persisted_exception_class

    def set_construction_state_from_state_dict(self, construction_state_dict):
        url_encoded_state = urllib.parse.urlencode(construction_state_dict, doseq=True)
        self._construction_client_side_state = url_encoded_state

    @property
    def construction_client_side_state(self):
        if not hasattr(self, '_construction_client_side_state'):
            state = self.persisted_userinput_class.get_persisted_for_view(self, '__reahl_last_construction_client_side_state__', str)
            self._construction_client_side_state = state
        else:
            state = self._construction_client_side_state

        return state or ''

    @property
    def current_POSTed_client_side_state(self):
        if not hasattr(self, '_current_POSTed_client_side_state'):
            request = ExecutionContext.get_context().request
            client_state_string = request.POST.dict_of_lists().get('__reahl_client_side_state__', [''])[0]
            client_state = urllib.parse.parse_qs(client_state_string, keep_blank_values=True)
            client_state.update(request.POST)  # TODO: issue: request.POST is not in disambiguated format....
            client_state_string = urllib.parse.urlencode(client_state, doseq=True)
            self._current_POSTed_client_side_state = client_state_string
        else:
            client_state_string = self._current_POSTed_client_side_state
        return client_state_string

    @property
    @memoized
    def construction_client_side_state_as_dict_of_lists(self):
        return urllib.parse.parse_qs(self.construction_client_side_state, keep_blank_values=True)

    @property
    def current_POSTed_state_as_dict_of_lists(self):
        return urllib.parse.parse_qs(self.current_POSTed_client_side_state, keep_blank_values=True)

    def save_last_construction_state(self):
        self.clear_last_construction_state()
        self.persisted_userinput_class.add_persisted_for_view(self.view, '__reahl_last_construction_client_side_state__', self.construction_client_side_state, str)

    def clear_last_construction_state(self):
        self.persisted_userinput_class.remove_persisted_for_view(self.view, '__reahl_last_construction_client_side_state__')

    def get_construction_state(self):
        # This is the stuff a View needs to know before we can construct it properly (arguments and input values applicable for this view)
        request = ExecutionContext.get_context().request
        widget_arguments = request.GET.dict_of_lists()
        # TODO: deal with lists and list sentinels and so on
        widget_arguments.update(self.construction_client_side_state_as_dict_of_lists)
        return widget_arguments

    def clear_all_view_data(self):
        self.persisted_exception_class.clear_all_view_data(self)
        self.persisted_userinput_class.clear_all_view_data(self)
        

class RedirectView(UrlBoundView):
    def __init__(self, user_interface, relative_path, to_bookmark):
        super().__init__(user_interface, relative_path, '')
        self.to_bookmark = to_bookmark

    def as_resource(self, page):
        raise HTTPSeeOther(location=str(self.to_bookmark.href.as_network_absolute()))


class PseudoView(View):
    relative_path = '/'


class NoView(PseudoView):
    """A special kind of View to indicate that no View was found."""
    exists = False

class UserInterfaceRootRedirectView(PseudoView):
    def as_resource(self, page):
        raise HTTPSeeOther(location=str(self.user_interface.get_absolute_url_for('/').as_network_absolute()))
    


class HeaderContent(Widget):
    def __init__(self, page):
        super().__init__(page.view)
        self.page = page

    def render(self):
        context = ExecutionContext.get_context()
        token_string = context.session.get_csrf_token().as_signed_string()
        csrf_meta = '<meta name="csrf-token" content="%s">' % token_string
        config = context.config
        library_header_material = ''.join([library.header_only_material(self.page)
                                           for library in config.web.frontend_libraries])
        return csrf_meta+library_header_material

    


class FooterContent(Widget):
    def __init__(self, page):
        super().__init__(page.view)
        self.page = page

    def render(self):
        config = ExecutionContext.get_context().config
        return super().render() + ''.join([library.footer_only_material(self.page)
                        for library in config.web.frontend_libraries])


class Resource:
    def __init__(self, view):
        self.view = view

    @property
    def should_commit(self):
        return True

    @property
    def http_methods(self):
        regex = re.compile(r'handle_(?!(request)$)([a-z]+)?')
        methods = []
        for i in dir(self):
            match = regex.match(i)
            if match:
                methods.append(match.group(2))
        return sorted(methods)

    def handle_request(self, request):
        if request.method.lower() not in self.http_methods:
            return HTTPMethodNotAllowed(headers={'allow': ', '.join(self.http_methods)})

        method_handler = getattr(self, 'handle_%s' % request.method.lower())
        return method_handler(request)

    def cleanup_after_transaction(self):
        pass


class SubResource(Resource):
    """A Resource that a Widget can register underneath the URL of the View the Widget is present on.
       This can be used to create URLs for whatever purpose the Widget may need server-side URLs for.

       :param unique_name: A name for this subresource which will be unique in the UserInterface where it is used.
    """
    sub_regex = 'sub_resource'          """The regex used to match incoming URLs against the URL of this SubResource."""
    sub_path_template = 'sub_resource'  """A `PEP-292 <http://www.python.org/dev/peps/pep-0292/>`_ template in a string
                                            used to create an URL for this resource."""

    def __init__(self, view, unique_name):
        super().__init__(view)
        self.unique_name = unique_name

    @classmethod
    def factory(cls, view, unique_name, path_argument_fields, *args, **kwargs):
        """Returns a Factory which the framework will use, once needed, in order to create
           this SubResource.

           :param unique_name: The unique name used to construct the URL for this SubResource.
           :param path_argument_fields: A dictionary mapping the names of arguments to the SubResource to Fields that
                                        can be used to input or output values for these arguments.
           :param args:  Extra arguments to be passed directly to the __init__ of the SubResource when created.
           :keyword kwargs: Extra keyword arguments to be passed directly to the __init__ of the SubResource when created.
        """
        regex_path = RegexPath(cls.get_regex(unique_name), 
                               cls.get_path_template(unique_name),
                               path_argument_fields)
        return SubResourceFactory(regex_path, functools.partial(cls.create_resource, view, unique_name, *args, **kwargs))

    @classmethod
    def is_for_sub_resource(cls, path, for_exact_sub_path='.*'):
        return re.match('.*/_{1,2}%s$' % for_exact_sub_path, path)

    @classmethod
    def get_full_path_for(cls, current_path, sub_path):
        if cls.is_for_sub_resource(current_path, for_exact_sub_path=sub_path):
            full_path = current_path
        else:
            delimiter = '/_'
            if current_path.endswith('/'):
                delimiter = '__'
            full_path = '%s%s%s' % (current_path, delimiter, sub_path)
        return full_path

    @classmethod
    def get_path_template(cls, unique_name):
        return '%s_%s' % (unique_name, cls.sub_path_template)

    @classmethod
    def get_url_for(cls, unique_name, **kwargs):
        sub_path = cls.get_path_template(unique_name) % kwargs
        url = Url.get_current_url()
        view_path = url.path
        if SubResource.is_for_sub_resource(url.path):
            view_path = SubResource.get_view_path_for(url.path)
        url.path = cls.get_full_path_for(view_path, sub_path)
        url.make_network_relative()
        return url

    @classmethod
    def get_regex(cls, unique_name):
        current_path = Url.get_current_url().as_locale_relative().path
        match = re.match('(?P<current_view_path>.*)(?P<delimiter>/_{1,2})%s_%s$' % (unique_name, cls.sub_regex), current_path)
        if match:
            current_view_path = match.group('current_view_path')
            delimiter = match.group('delimiter')
            return '%s%s%s_%s' % (current_view_path, delimiter, unique_name, cls.sub_regex)
        delimiter = '/_'
        if current_path.endswith('/'):
            delimiter = '__'
        return '%s%s%s_%s' % (current_path, delimiter, unique_name, cls.sub_regex)

    @classmethod
    def parent_url_should_end_on_slash(cls, current_path):
        last_path_segment = current_path.split('/')[-1]
        return last_path_segment.startswith('__')

    @classmethod
    def get_view_path_for(cls, subresource_path):
        new_path = '/'.join(subresource_path.split('/')[:-1])
        if cls.parent_url_should_end_on_slash(subresource_path):
            new_path += '/'
        return new_path

    @classmethod
    def get_parent_url(cls): 
        current_path = Url.get_current_url().path
        new_path = cls.get_view_path_for(current_path)
        url = Url.get_current_url()
        url.path = new_path
        return url

    def get_url(self):
        """Returns the Url that resolves to this SubResource."""
        return self.get_url_for(self.unique_name)


class MethodResult:
    """A :class:`RemoteMethod` can be constructed to yield its results back to a browser in different
       ways. MethodResult is the superclass of all such different kinds of results.

       :keyword catch_exception: The class of Exeption for which this MethodResult will generate an exceptional Response\
                                 if thrown while the :class:`RemoteMethod` executes \
                                 (default: :class:`~reahl.component.exceptions.DomainException`).
       :keyword mime_type: The mime type to use as html content type when sending this MethodResult back to a browser.
       :keyword encoding: The encoding to use when sending this MethodResult back to a browser.
       :keyword replay_request: If True, first recreate everything (including this MethodResult) before generating \
            the final response in order to take possible changes made by the execution of the RemoteMethod into account.
            
       .. versionchanged:: 3.2
          Added the replay_request functionality.

       .. versionchanged:: 3.2
          Set the default for catch_exception to DomainException
    """
    def __init__(self, catch_exception=DomainException, mime_type='text/html', encoding='utf-8', replay_request=False):
        self.catch_exception = catch_exception
        self.mime_type = mime_type
        self.encoding = encoding
        self.replay_request = replay_request

    def create_response(self, return_value):
        """Override this in your subclass to create a :class:`webob.Response` for the given `return_value` which
           was returned when calling the RemoteMethod."""
        return Response(body=self.render(return_value), 
                        charset=self.encoding,
                        content_type=self.mime_type)
    
    def create_exception_response(self, exception):
        """Override this in your subclass to create a :class:`webob.Response` for the given `exception` instance
           which happened during execution of the RemoteMethod. This method will only be called when the exception
           is raised, and only if you specified for it to be caught using `catch_exception` when this MethodResult
           was created.
        """
        return Response(body=self.render_exception(exception),
                        charset=self.encoding,
                        content_type=self.mime_type)

    def render(self, return_value):
        """Instead of overriding `.create_response` to customise how `return_value` will be reported, 
           this method can be overridden instead, supplying only the body of a normal 200 Response."""
        return return_value

    def render_exception(self, exception):
        """Instead of overriding `.create_exception_response` to customise how `exception` will be reported, 
           this method can be overridden instead, supplying only the body of a normal 200 Response."""
        return str(exception)

    def get_response(self, return_value, is_internal_redirect):
        if self.replay_request and not is_internal_redirect:
            raise RegenerateMethodResult(return_value, None)
        response = self.create_response(return_value)
        response.content_type = self.mime_type
        response.charset = self.encoding
        return response

    def get_exception_response(self, exception, is_internal_redirect):
        if self.replay_request and not is_internal_redirect:
            raise RegenerateMethodResult(None, exception)
        response = self.create_exception_response(exception)
        response.content_type = self.mime_type
        response.charset = self.encoding
        return response


class RedirectAfterPost(MethodResult):
    """A MethodResult which will cause the browser to be redirected to the Url returned by the called
       RemoteMethod instead of actually returning the result for display. A RedirectAfterPost is meant to be
       used by the EventChannel only.

       :keyword mime_type: (See :class:`MethodResult`.)
       :keyword encoding: (See :class:`MethodResult`.)


       .. versionchanged:: 4.0
          Renamed content_type to mime_type and charset to encoding in line with MethodResult args.
    """
    def __init__(self, mime_type='text/html', encoding='utf-8'):
        super().__init__(catch_exception=DomainException, mime_type=mime_type, encoding=encoding)

    def create_response(self, return_value):
        next_url = return_value
        return HTTPSeeOther(location=str(next_url))
    
    def create_exception_response(self, exception):
        next_url = SubResource.get_parent_url()
        return HTTPSeeOther(location=str(next_url))


class JsonResult(MethodResult):
    """A MethodResult that can be used to let a RemoteMethod return its result to the browser
       in JSon format.

       :param result_field: A :class:`reahl.component.modelinterface.Field` instance to be used
                            for outputting the return value of the RemoteMethod as a string.
       :keyword kwargs: Other keyword arguments are sent to MethodResult, see :class:`MethodResult`.
    """
    redirects_internally = True
    def __init__(self, result_field, **kwargs):
        super().__init__(mime_type='application/json', encoding='utf-8', **kwargs)
        self.fields = FieldIndex(self)
        self.fields.result = result_field

    def render(self, return_value):
        self.result = return_value
        return self.fields.result.as_input()

    def render_exception(self, exception):
        if hasattr(exception, 'as_json'):
            return exception.as_json()
        else:
            return '"%s"' % str(exception)


class RegenerateMethodResult(InternalRedirect):
    def __init__(self, return_value, exception):
        super().__init__()
        self.return_value = return_value
        self.exception = exception

    def get_results(self):
        return (self.return_value, self.exception)


class WidgetResult(MethodResult):
    """A MethodResult used to render a given Widget (`result_widget`) back to the browser in response
       to a RemoteMethod being invoked. The HTML rendered is only the contents of the `result_widget`,
       not its containing HTML element. WidgetResult is one way in which to re-render a server-side Widget
       via Ajax inside a browser without refreshing an entire page in the process.

       A JavaScript `<script>` tag is rendered also, containing the JavaScript activating code for the 
       new contents of this refreshed Widget.

       .. versionchanged:: 6.1
          result_widget parameter changed to be a list, renamed to result_widgets.
          Deprecated kwarg as_json_and_result
    """

    def __init__(self, result_widgets, as_json_and_result=None):
        if as_json_and_result is None:
            as_json_and_result = True
        else:
            warnings.warn('DEPRECATED: as_json_and_result kwarg will be removed, and forced to True in 7.0', DeprecationWarning, stacklevel=1)            
        if not isinstance(result_widgets, list):
            warnings.warn('DEPRECATED: result_widgets should be a list', DeprecationWarning, stacklevel=1)
            result_widgets = [result_widgets]
        if not as_json_and_result and len(result_widgets) > 1:
            raise ProgrammerError('Only one result_widget allowed when as_json_and_result is True')

        mime_type = 'application/json' if as_json_and_result else 'text/html'
        super().__init__(mime_type=mime_type, encoding='utf-8', catch_exception=DomainException, replay_request=True)
        self.result_widgets = result_widgets
        self.as_json_and_result = as_json_and_result

    def render_as_json(self, exception):
        widgets_to_render = set()
        for widget in self.result_widgets:
            widgets_to_render.add(widget)
            widgets_to_render.update(self.get_coactive_widgets_recursively(widget))
        rendered_widgets = {widget.css_id: widget.render_contents() + widget.render_contents_js()
                            for widget in widgets_to_render}
        success = exception is None
        report_exception = str(exception) if exception and not exception.handled_inline else ''
        return json.dumps({ 'success': success, 'exception': report_exception, 'result': rendered_widgets })

    def get_coactive_widgets_recursively(self, widget):
        ancestral_widgets = []
        for current_widget, current_parents_set in widget.view.page.parent_widget_pairs(set([])):
            if current_widget is widget:
                coactive_parents = set(widget.coactive_widgets) & set(current_parents_set)
                if coactive_parents:
                    raise ProgrammerError('The coactive Widgets of %s include its ancestor(s): %s' % (widget, ','.join([str(i) for i in coactive_parents])))
                ancestral_widgets = [ancestral_widget 
                                        for parent in current_parents_set 
                                    for ancestral_widget in parent.ancestral_coactive_widgets]

        all_coactive_widgets = ancestral_widgets
        for direct_coactive_widget in widget.coactive_widgets:
            all_coactive_widgets.append(direct_coactive_widget)
            for indirect_coactive_widget in direct_coactive_widget.coactive_widgets:
                all_coactive_widgets.append(indirect_coactive_widget)

        descendant_widgets = set(widget.contained_widgets())
        coactive_widgets =  set(all_coactive_widgets) - descendant_widgets

        for coactive_widget in coactive_widgets.copy():
            descendant_widgets = set(coactive_widget.contained_widgets())
            coactive_widgets = coactive_widgets - descendant_widgets

        return coactive_widgets

    def render(self, return_value):
        if self.as_json_and_result:
            return self.render_as_json(None)
        return self.result_widgets[0].render_contents() + self.result_widgets[0].render_contents_js()

    def render_exception(self, exception):
        if self.as_json_and_result:
            return self.render_as_json(exception)
        return super().render_exception(exception)


class RemoteMethod(SubResource): 
    """A server-side method that can be invoked from a browser via an URL. The method will return its result
       back to the browser in different ways, depending on which type of `default_result` it is constructed 
       with.

       :param name: A unique name from which the URL of this RemoteMethod will be constructed.
       :param callable_object: A callable object which will receive either the raw query arguments (if immutable),
                               or the raw POST data (if not immutable) as keyword arguments.
       :param default_result: The :class:`MethodResult` returned by :meth:`RemoteMethod.make_result`.
       :keyword idempotent: Whether this method will yield the same side-effects and results when called more than
                            once, or not. Idempotent methods are accessible via GET method. Methods that are not idempotent
                            are accessible by POST http method.
       :keyword immutable: Pass True to guarantee that this method will not make changes in the database (the database
                           is rolled back to ensure this). Immutable methods are idempotent.
       :keyword method: The http method supported by this RemoteMethod is derived from whether it is idempotent or not. By default 
                        a RemoteMethod is accessible via http 'get' if it is idempotent, else by 'post'. This behaviour can be 
                        overridden by specifying an http method explicitly using the `method` keyword argument.
       :keyword disable_csrf_check: Pass True to prevent this RemoteMethod from doing the usual CSRF check.

        .. versionchanged:: 5.0
           idempotent and immutable kwargs split up into two and better defined.

        .. versionchanged:: 5.0
           method keyword argument added to explicitly state http method.

        .. versionchanged:: 5.2
           disable_csrf_check keyword argument added.

    """
    sub_regex = 'method'
    sub_path_template = 'method'

    def __init__(self, view, name, callable_object, default_result, idempotent=False, immutable=False, method=None, disable_csrf_check=False):
        super().__init__(view, name)
        self.idempotent = idempotent or immutable
        self.immutable = immutable
        self.callable_object = callable_object
        self.default_result = default_result
        self.caught_exception = None
        self.input_values = None
        self.method = method
        self.disable_csrf_check = disable_csrf_check

    @property
    def should_commit(self):
        return ((self.caught_exception is None) or getattr(self.caught_exception, 'commit', False)) and (not self.immutable)

    @property
    def name(self):
        return self.unique_name
    
    @property
    def http_methods(self):
        if self.method:
            return [self.method]
        if self.immutable or self.idempotent:
            return ['get']
        return ['post']

    def parse_arguments(self, input_values):
        return {k: v[0] for k, v in input_values.items()}

    def cleanup_after_exception(self, input_values, ex):
        """Override this method in a subclass to trigger custom behaviour after the method
           triggered a :class:`~reahl.component.exceptions.DomainException`."""
        
    def cleanup_after_success(self):
        """Override this method in a subclass to trigger custom behaviour after the method
           completed successfully."""

    def call_with_input(self, input_values, catch_exception):

        caught_exception = None
        return_value = None
        try:
            if not self.disable_csrf_check:
                self.check_csrf_header()
            return_value = self.callable_object(**self.parse_arguments(input_values))
        except catch_exception as ex:
            self.caught_exception = caught_exception = ex
            self.input_values = input_values
        return (return_value, caught_exception)

    def check_csrf_header(self):
        context = ExecutionContext.get_context()

        try:
            received_token_string = context.request.headers['X-CSRF-TOKEN']
        except KeyError:
            raise HTTPForbidden()
        try:
            received_token = CSRFToken.from_coded_string(received_token_string)
        except InvalidCSRFToken as ex:
            raise HTTPForbidden()
        if received_token.is_expired():
            raise ExpiredCSRFToken()
        if not context.session.get_csrf_token().matches(received_token):
            raise HTTPForbidden()

    def cleanup_after_transaction(self):
        super().cleanup_after_transaction()
        if self.caught_exception:
            self.cleanup_after_exception(self.input_values, self.caught_exception)
        else:
            self.cleanup_after_success()

    def make_result(self, input_values):
        """Override this method to be able to determine (at run time) what MethodResult to use
           for this method. The default implementation merely uses the `default_result` given
           during construction of the RemoteMethod.

           :param input_values: The current request.GET or request.POST depending on the request.method.
        """
        return self.default_result

    def handle_get_or_post(self, request, input_values):
        result = self.make_result(input_values)

        internal_redirect = getattr(request, 'internal_redirect', None)
        if internal_redirect:
            return_value, caught_exception = internal_redirect.get_results()
        else:
            return_value, caught_exception = self.call_with_input(input_values, result.catch_exception)

        if caught_exception:
            response = result.get_exception_response(caught_exception, internal_redirect is not None)
        else:
            response = result.get_response(return_value, internal_redirect is not None)

        return response

    def handle_post(self, request):
        return self.handle_get_or_post(request, request.POST.dict_of_lists())

    def handle_get(self, request):
        return self.handle_get_or_post(request, request.GET.dict_of_lists())


class CheckedRemoteMethod(RemoteMethod): 
    """A RemoteMethod whose input is governed by instances of :class:`Field` like input usually is.

       :param name: (See :class:`RemoteMethod`.)
       :param callable_object: (See :class:`RemoteMethod`.) Should expect a keyword argument for each key in `parameters`.
       :param result: (See :class:`RemoteMethod`.)
       :keyword idempotent: (See :class:`RemoteMethod`.)
       :keyword immutable: (See :class:`RemoteMethod`.)
       :keyword parameters: A dictionary containing a Field for each argument name expected.

       .. versionchanged:: 5.0
          Split immutable into immutable and idempotent kwargs.
    """
    def __init__(self, view, name, callable_object, result, idempotent=False, immutable=False, disable_csrf_check=False, **parameters):
        super().__init__(view, name, callable_object, result, idempotent=idempotent, immutable=immutable, disable_csrf_check=disable_csrf_check)
        self.parameters = FieldIndex(self)
        for name, field in parameters.items():
            self.parameters.set(name, field)

    def parse_arguments(self, input_values):
        exceptions = []
        for name, field in self.parameters.items():
            try:
                field.from_input(input_values.get(name, [''])[0])
            except ValidationConstraint as ex:
                exceptions.append(ex)
        if exceptions:
            raise ValidationException.for_failed_validations(exceptions)
        return self.parameters.as_kwargs()


class EventChannel(RemoteMethod):
    """A RemoteMethod used to receive Events originating from Buttons on Forms.

       Programmers should not need to work with an EventChannel directly.
    """
    def __init__(self, form, controller, name):
        super().__init__(form.view, name, self.delegate_event, None, idempotent=False, immutable=False, disable_csrf_check=True)
        self.controller = controller
        self.form = form

    def make_result(self, input_values):
        if '_noredirect' in input_values.keys():
            return WidgetResult([self.form.rendered_form])
        else:
            return RedirectAfterPost()

    def delegate_event(self, event=None):
        try:
            return self.controller.handle_event(event)
        except NoEventHandlerFound:
            raise ProgrammerError('No suitable handler found for event %s on %s' % (event.name, self.form.view))

    def parse_arguments(self, input_values):
        event = self.form.handle_form_input(input_values)
        return {'event': event}

    def cleanup_after_exception(self, input_values, ex):
        self.form.persisted_userinput_class.clear_for_view(self.form.view)
        self.form.cleanup_after_exception(input_values, ex)
        self.form.view.save_last_construction_state()
        
    def cleanup_after_success(self):
        self.form.cleanup_after_success()
        self.form.persisted_userinput_class.clear_for_view(self.form.view)
        self.form.view.clear_last_construction_state()


class ComposedPage(Resource):
    def __init__(self, view, page):
        super().__init__(view)
        self.page = page

    @property
    def should_commit(self):
        return False
        
    def handle_get(self, request):
        internal_redirect = getattr(request, 'internal_redirect', None)
        if internal_redirect:
            return self.render()
        else:
            # so that we can re-render on values that were updated in the domain from construction_state
            raise InternalRedirect()

    def render(self):
        return Response(
            body=self.page.render(),
            content_type=self.page.mime_type,
            charset=self.page.encoding,
            cache_control=self._response_cache_control())

    def _response_cache_control(self):
        if self.view.cacheable:
            config = ExecutionContext.get_context().config
            return 'max-age=%s' % config.web.cache_max_age
        else:
            return 'no-store'


class FileView(View):
    def __init__(self, user_interface, viewable_file):
        super().__init__(user_interface)
        self.viewable_file = viewable_file

    def as_resource(self, page):
        return StaticFileResource(self, 'static', self.viewable_file)

    @property
    def title(self):
        return self.viewable_file.name


class ViewableFile:
    def __init__(self, name, mime_type, encoding, size, mtime):
        self.name = name
        self.mime_type = mime_type
        self.encoding = encoding
        self.mtime = mtime
        self.size = size    


class FileOnDisk(ViewableFile):
    def __init__(self, full_path, relative_name):
        mime_type, encoding = mimetypes.guess_type(full_path)
        self.mime_type = mime_type or 'application/octet-stream' # So you can is_text() below
        if not encoding:
            # FIXME: This assumes all text files on disk are encoded with the system's preferred
            # encoding, which is nothing but a guess
            encoding = locale.getpreferredencoding() if self.is_text() else None

        self.full_path = full_path
        self.relative_name = relative_name
        st = os.stat(full_path)
        super().__init__(
            full_path,
            self.mime_type,
            encoding,
            st.st_size,
            st.st_mtime)

    def is_text(self):
        return self.mime_type and self.mime_type.startswith('text/')

    @contextmanager
    def open(self):
        open_file = io.open(self.full_path, mode='rb')
        try:
            yield open_file
        finally:
            open_file.close()

class FileFromBlob(ViewableFile):
    def __init__(self, name, content_bytes, mime_type, encoding, size, mtime):
        if not isinstance(content_bytes, bytes):
            raise ProgrammerError('content_bytes should be bytes')

        super().__init__(name, mime_type, encoding, size, mtime)
        self.content_bytes = content_bytes
        self.relative_name = name

    @contextmanager
    def open(self):
        yield io.BytesIO(self.content_bytes)


class PackagedFile(FileOnDisk):
    def __init__(self, egg_name, package_name, relative_name):
        self.egg_name = egg_name

        if USE_PKG_RESOURCES:
            directory_name = package_name.replace('.', '/')
            egg_relative_name = '/'.join([directory_name, relative_name])
            full_path = pkg_resources.resource_filename(pkg_resources.Requirement.parse(egg_name), egg_relative_name)
        else:
            full_path = str(importlib_resources.files(package_name) / relative_name)

        super().__init__(full_path, relative_name)


class ConcatenatedFile(FileOnDisk):
    def __init__(self, relative_name, contents):
        self.temp_file = self.concatenate(relative_name, contents)
        super().__init__(self.temp_file.name, relative_name)
     
    def minifier(self, relative_name):
        class NoOpMinifier:
            def minify(self, input_stream, output_stream):
                for line in input_stream:
                    output_stream.write(line)
        
        class JSMinifier:
            def minify(self, input_stream, output_stream):
                text = io.StringIO()
                for line in input_stream:
                    text.write(line)

                output_stream.write(rjsmin.jsmin(text.getvalue()))

        class CSSMinifier:
            def minify(self, input_stream, output_stream):
                text = io.StringIO()
                for line in input_stream:
                    text.write(line)
                output_stream.write(rcssmin.cssmin(text.getvalue()))

        context = ExecutionContext.get_context()
        if context.config.reahlsystem.debug:
            return NoOpMinifier()

        if relative_name.endswith('.css'):
            return CSSMinifier()
        elif relative_name.endswith('.js'):
            return JSMinifier()
        else:
            return NoOpMinifier()

    def create_temp_file(self, suffix):
        """Since NamedTemporaryFile does not work on windows, we need to create our own"""

        (file_handle, path) = tempfile.mkstemp(suffix=suffix)
        os.close(file_handle)
        open_file = open(path, 'w+')
        
        def close_temp_file(open_file):
            import os
            open_file.close()
            os.remove(open_file.name)
        atexit.register(close_temp_file, open_file)

        return open_file

    def concatenate(self, relative_name, contents):
        temp_file = self.create_temp_file(relative_name)
        for inner_file in contents:
            with open(inner_file.full_path) as opened_inner_file:
                self.minifier(relative_name).minify(opened_inner_file, temp_file)
        temp_file.flush()
        return temp_file


class FileFactory(Factory):
    def create_file(self, relative_path):
        raise NoMatchingFactoryFound(relative_path)

    
class FileList(FileFactory):
    def __init__(self, files):
        super().__init__(self.create_file)
        self.files = files
        
    def create_file(self, relative_path):
        path = relative_path[1:]
        for file_ in self.files:
            if file_.relative_name == path:
                return file_
        raise NoMatchingFactoryFound(relative_path)


class DiskDirectory(FileFactory):
    def __init__(self, root_path):
        super().__init__(self.create_file)
        self.root_path = root_path

    def create_file(self, relative_path):
        path = relative_path[1:]
        context = ExecutionContext.get_context()
        static_root = context.config.web.static_root
        relative_path = self.root_path.split('/')+path.split('/')
        full_path = os.path.join(static_root, *relative_path)
        logging.getLogger(__name__).debug('Request is for static file "%s"' % full_path)
        if os.path.isfile(full_path):
            return FileOnDisk(full_path, relative_path)
        raise NoMatchingFactoryFound(relative_path)


class FileDownload(Response):
    chunk_size = 4096
    def __init__(self, a_file):
        self.file = a_file 
        super().__init__(app_iter=self, conditional_response=True)
        self.content_type = self.file.mime_type if self.file.mime_type else None
        self.charset = self.file.encoding if self.file.encoding else None
        self.content_length = str(self.file.size) if (self.file.size is not None) else None
        self.last_modified = datetime.fromtimestamp(self.file.mtime)
        self.etag = ('%s-%s-%s' % (self.file.mtime,
                                   self.file.size,
                                   abs(hash(self.file.name))))

    def __iter__(self):
        return self.app_iter_range(start=0)
            
    def app_iter_range(self, start=0, end=None):
        length_of_file = self.file.size
        if not end or end >= length_of_file:
            end = length_of_file - 1
        if start < 0:
            start = 0
        if start >= end:
            yield b''
            return
        current = start or 0

        with self.file.open() as fileobj:
            fileobj.seek(current)
            # Invariant: everything < current has been processed
            while current+self.chunk_size <= end+1:
                chunk = fileobj.read(self.chunk_size)
                yield chunk
                current += self.chunk_size
            # Postcondition: everything < end+1-chunk-size has been processed

            if current < end+1:
                leftover_size = end-current+1
                chunk = fileobj.read(leftover_size)
                yield chunk


class StaticFileResource(SubResource):
    sub_regex = '(?P<filename>[^/]+)'
    sub_path_template = '%(filename)s'

    def get_url(self):
        return self.get_url_for(self.unique_name, filename=self.file.name)

    def __init__(self, view, unique_name, a_file):
        super().__init__(view, unique_name)
        self.file = a_file

    def handle_get(self, request):
        return FileDownload(self.file)


class MissingForm(Resource):
    def __init__(self, view, root_ui, target_ui):
        super().__init__(view)
        self.root_ui = root_ui
        self.target_ui = target_ui

    def handle_post(self, request):
        return Redirect(self.root_ui.get_bookmark_for_error(_('Something changed on the server while you were busy. You cannot perform this action anymore.'), 
                                                            self.view.as_bookmark(self.target_ui)))

    def cleanup_after_transaction(self):
        self.view.clear_all_view_data()


class CouldNotConstructResource(Exception):
    def __init__(self, current_view, root_ui, target_ui, exception):
        super().__init__()
        self.current_view = current_view
        self.root_ui = root_ui
        self.target_ui = target_ui
        self.__cause__ = exception

class UncaughtError(Redirect):
    def __init__(self, view, root_ui, target_ui, exception):
        error_source_bookmark = view.as_bookmark(target_ui) if view else None
        target_bookmark = root_ui.get_bookmark_for_error(str(exception), error_source_bookmark)
        super().__init__(target_bookmark)



class IdentityDictionary:
    """A dictionary which has values equal to whatever key is asked for. An IdentityDictionary is
       sometimes useful when mapping between Slot names, etc."""
    def __getitem__(self, x): return x


class ReahlWSGIApplication:
    """A web application. This class should only ever be instantiated in a WSGI script, using the `from_directory`
       method.

       .. versionchanged:: 4.0
          Renamed from ReahlApplication to ReahlWSGIApplication
    """

    @classmethod
    def from_directory(cls, directory, strict_checking=True, start_on_first_request=False):
        """Create a ReahlWSGIApplication given the `directory` where its configuration is stored.

        :keyword strict_checking: If False, exceptions will not be raised when dangerous defaulted config is present.
        :keyword start_on_first_request: If True, the app is started when the first request is served.

        .. versionchanged:: 5.0
           Added strict_checking kwarg.

        .. versionchanged:: 5.0
           Added start_on_first_request.

        """
        config = StoredConfiguration(directory, strict_checking=strict_checking)
        config.configure()
        return cls(config, start_on_first_request=start_on_first_request)

    def __init__(self, config, start_on_first_request=False):
        self.start_on_first_request = start_on_first_request
        self.start_lock = threading.Lock()
        self.started = False
        self.request_lock = threading.Lock()
        self.config = config
        self.system_control = SystemControl(self.config)
        with ExecutionContext(name='%s.__init__()' % self.__class__.__name__) as context:
            context.config = self.config
            context.system_control = self.system_control
            self.root_user_interface_factory = UserInterfaceFactory(None, RegexPath('/', '/', {}), IdentityDictionary(), self.config.web.site_root, 'site_root')
            self.add_reahl_static_files()

    def add_reahl_static_files(self):
        static_files = self.config.web.frontend_libraries.packaged_files()
        self.define_static_files('/static', static_files)
        return static_files

    def define_static_files(self, path, files):
        ui_name = 'static_%s' % path
        ui_factory = UserInterfaceFactory(None, RegexPath(path, path, {}), IdentityDictionary(), StaticUI, ui_name, files=FileList(files))
        self.root_user_interface_factory.predefine_user_interface(ui_factory)
        return ui_factory

    def start(self):
        """Starts the ReahlWSGIApplication by "connecting" to the database. What "connecting" means may differ
           depending on the persistence mechanism in use. It could include enhancing classes for persistence, etc."""
        self.should_disconnect = False
        with ExecutionContext(name='%s.start()' % self.__class__.__name__) as context:
            context.config = self.config
            context.system_control = self.system_control
            if not self.system_control.connected:
                self.system_control.connect()
                self.should_disconnect = True
        self.started = True

    def stop(self):
        """Stops the ReahlWSGIApplication by "disconnecting" from the database. What "disconnecting" means may differ
           depending on the persistence mechanism in use."""
        with ExecutionContext(name='%s.stop()' % self.__class__.__name__) as context:
            context.config = self.config
            context.system_control = self.system_control
            if self.should_disconnect and self.system_control.connected:
                self.system_control.disconnect()

    def resource_for(self, request):
        root_ui = target_ui = current_view = None
        
        try:
            url = Url.get_current_url(request=request).as_locale_relative()
            logging.getLogger(__name__).debug('Finding Resource for URL: %s' % url.path)
            try:
                root_ui = self.root_user_interface_factory.create(url.path)
            except:
                root_ui = UserInterface(None, '/', {}, False, '__emergency_error_root_ui')
                if url.path != root_ui.get_bookmark_for_error('', None).href.as_locale_relative().path:
                    raise

            target_ui, page_factory = root_ui.get_user_interface_for_full_path(url.path)
            # TODO: FEATURE ENVY BELOW:
            logging.getLogger(__name__).debug('Found UserInterface %s' % target_ui)
            current_view = target_ui.get_view_for_full_path(url.path)
            logging.getLogger(__name__).debug('Found View %s' % current_view)

            current_view.check_precondition()
            current_view.check_rights(request.method)
            if current_view.is_dynamic:
                page = current_view.create_page(url.path, page_factory)
                self.check_scheme(page.is_security_sensitive)
            else:
                page = None

            try:
                return current_view.resource_for(url.path, page)
            except HTTPNotFound:
                if self.is_form_submit(url.path, request):
                    return MissingForm(current_view, root_ui, target_ui)
                else:
                    raise
        except HTTPException:
            raise
        except Exception as ex:
            raise CouldNotConstructResource(current_view, root_ui, target_ui, ex)

    def is_form_submit(self, full_path, request):
        return SubResource.is_for_sub_resource(full_path) and request.method == 'POST' and any(name.endswith('_reahl_database_concurrency_digest') for name in request.POST.keys())

    def check_scheme(self, security_sensitive):
        scheme_needed = self.config.web.default_http_scheme
        if security_sensitive:
            scheme_needed = self.config.web.encrypted_http_scheme

        request = ExecutionContext.get_context().request
        if request.scheme.lower() != scheme_needed.lower():
            raise RedirectToScheme(scheme_needed)

    def create_context_for_request(self):
        return ExecutionContext(name='%s.create_context_for_request()' % self.__class__.__name__)

    @contextmanager
    def serialise_requests(self):
        try:
            self.request_lock.acquire()
            yield
        finally:
            self.request_lock.release()
            
    @contextmanager
    def allow_parallel_requests(self):
        yield
    
    @property
    def concurrency_manager(self):
        if self.config.reahlsystem.serialise_parallel_requests:
            return self.serialise_requests()
        return self.allow_parallel_requests()

    def ensure_started(self):
        if not self.started: # performance optimisation, instead of using locks
            with self.start_lock:
                if not self.started:
                    self.start()

    def __call__(self, environ, start_response):
        if self.start_on_first_request:
            self.ensure_started()
        if not self.started and self.config.strict_checking:
            raise ProgrammerError('%s is not started. Did you mean to set start_on_first_request=True?' % self)
        request = Request(environ, charset='utf8')
        context = self.create_context_for_request()
        context.config = self.config
        context.request = request
        context.system_control = self.system_control
        with context, self.concurrency_manager:
            with self.system_control.nested_transaction():
                self.config.web.session_class.initialise_web_session_on(context)
                context.session.set_last_activity_time()
            try:
                try:
                    with self.system_control.nested_transaction() as veto:
                        veto.should_commit = False
                        resource = None
                        try:
                            resource = self.resource_for(request)
                            response = resource.handle_request(request) 
                            veto.should_commit = resource.should_commit
                        except InternalRedirect as e:
                            if resource:
                                resource.cleanup_after_transaction()
                            request.internal_redirect = e
                            resource = self.resource_for(request)
                            response = resource.handle_request(request) 
                            veto.should_commit = resource.should_commit
                            if not veto.should_commit:
                                context.config.web.session_class.preserve_session(context.session)
                    if not veto.should_commit:
                        context.config.web.session_class.restore_session(context.session) # Because the rollback above nuked it
                    if resource:
                        resource.cleanup_after_transaction()
                        
                except HTTPException as e:
                    response = e
                except DisconnectionError as e:
                    response = HTTPInternalServerError(unicode_body=str(e))
                except CouldNotConstructResource as e:
                    if self.config.reahlsystem.debug:
                        raise e.__cause__ from None
                    else:
                        #TODO: constuct a fake view, and pass that in
                        response = UncaughtError(e.current_view, e.root_ui, e.target_ui, e.__cause__)
                except Exception as e:
                    if self.config.reahlsystem.debug:
                        raise e
                    else:
                        logging.getLogger(__name__).exception(e)
                        response = UncaughtError(resource.view, resource.view.user_interface.root_ui, resource.view.user_interface, e)

                context.session.set_session_key(response)
                
            finally:
               self.system_control.finalise_session()
               
            for chunk in response(environ, start_response):
                yield chunk

