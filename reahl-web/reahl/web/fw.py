# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
"""

import atexit
import sys
import tempfile
import mimetypes
import inspect
import new
from datetime import datetime, timedelta
import pkg_resources
import os
import os.path
import re
import random
import copy
import glob
import json
import string
import threading
import urllib
import urlparse
import functools
import itertools
import StringIO
import logging
from contextlib import contextmanager
from pkg_resources import Requirement

from webob import Request, Response
from webob.exc import HTTPException, HTTPNotFound, HTTPMethodNotAllowed, HTTPSeeOther, HTTPInternalServerError, HTTPBadRequest, HTTPForbidden
from webob.request import DisconnectionError

import slimit
import cssmin

from reahl.component.exceptions import DomainException, ProgrammerError, IncorrectArgumentError, checkargs_explained, IsInstance, IsSubclass, arg_checks, NotYetAvailable
from reahl.component.context import ExecutionContext
from reahl.component.dbutils import SystemControl
from reahl.component.i18n import Translator
from reahl.component.modelinterface import StandaloneFieldIndex, FieldIndex, Field, ValidationConstraint,\
                                             Allowed, exposed, UploadedFile, Event
from reahl.component.config import StoredConfiguration                                             
from reahl.component.decorators import memoized, deprecated
from reahl.component.eggs import ReahlEgg

_ = Translator(u'reahl-web')

class ValidationException(DomainException):
    """Indicates that one or more Fields received invalid data."""
    def as_user_message(self):
        return _(u'Invalid data supplied')


class NoMatchingFactoryFound(Exception):
    pass

class NoEventHandlerFound(Exception):
    pass

class CannotCreate(NoMatchingFactoryFound):
    """Programmers raise this to indicate that the arguments given via URL to a View
       or UserInterface that is parameterised were invalid."""
    pass

class Url(object):
    """An Url represents an URL, and is used to modify URLs, or manipulate them in other ways. Construct it
       with an URL in a string."""
    @classmethod
    def get_current_url(cls, request=None):
        """Returns the Url requested by the current Request."""
        request = request or WebExecutionContext.get_context().request
        return cls(unicode(request.url))
    
    def __init__(self, url_string):
        split_url = urlparse.urlsplit(url_string)
        self.scheme = split_url.scheme     #:
        self.username = split_url.username #:
        self.password = split_url.password #:
        self.hostname = split_url.hostname #:
        self.port = split_url.port         #:
        self.path = split_url.path         #:
        self.query = split_url.query       #:
        self.fragment = split_url.fragment #:

    def set_scheme(self, scheme):
        """Sets the scheme part of the Url (the http or https before the :), ensuring that the
           port is also correct accorging to the new scheme. Ports numbers are set from
           web.default_http_port and web.encrypted_http_port configuration settings."""
        self.scheme = scheme
        if self.port:
            config = WebExecutionContext.get_context().config
            self.port = config.web.default_http_port
            if self.scheme == config.web.encrypted_http_scheme:
                self.port = config.web.encrypted_http_port

    def set_query_from(self, value_dict):
        """Sets the query string of this Url from a dictionary."""
        self.query = urllib.urlencode(value_dict)

    @property
    def netloc(self):
        """Returns the `authority part of the URl as per RFC3968 <http://tools.ietf.org/html/rfc3986#section-3.2>`_, 
           also sometimes referred to as the netloc part in Python docs."""
        netloc = u''
        if self.username: netloc += self.username
        if self.password: netloc += u':%s' % self.password
        if netloc:        netloc += u'@'
        if self.hostname: netloc += self.hostname
        if self.port:     netloc += u':%s' % self.port
        return netloc

    def get_locale_split_path(self, locale=None):
        locale = locale or u'[^/]+'
        match = re.match(u'/(?P<locale>%s)(?P<url>/.*|$)' % locale, self.path)
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
        self.scheme = u''
        self.hostname = u''
        self.port = u''

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
            self.path = u'/%s%s' % (locale, self.path)
        
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
        
    def __unicode__(self):
        return urlparse.urlunsplit((self.scheme, self.netloc, self.path, self.query, self.fragment))

    def __str__(self):
        return str(unicode(self))

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
        request = WebExecutionContext.get_context().request
        return self.is_active_on(Url(request.url), exact_path=exact_path)

    def query_is_subset(self, other_url):
        """Answers whether name=value pairs present in this Url's query string is a subset
           of those present in `other_url`."""
        other_args = urlparse.parse_qs(other_url.query)
        self_args = urlparse.parse_qs(self.query)

        if not set(self_args).issubset(set(other_args)):
            return False

        other_values = dict([(key, other_args[key]) for key in self_args])
        return other_values == self_args


class WebExecutionContext(ExecutionContext):
    def set_request(self, request):
        self.request = request

    def initialise_web_session(self):
        with self:
            session_class = self.config.web.session_class
            self.set_session( session_class.get_or_create_session() )
    
    def handle_wsgi_call(self, wsgi_app, environ, start_response):
        with self:
            with wsgi_app.concurrency_manager:
                with self.system_control.nested_transaction():
                    self.initialise_web_session()
                try:
                    resource = wsgi_app.resource_for(self.request)
                    response = resource.handle_request(self.request) 
                except HTTPException, e:
                    response = e
                except DisconnectionError, e:
                    response = HTTPInternalServerError(body=unicode(e))
                self.session.set_session_key(response)
                for chunk in response(environ, start_response):
                    yield str(chunk)
                self.session.set_last_activity_time()
                self.system_control.finalise_session()


class EventHandler(object):
    """An EventHandler is used to transition the user to the View that matches `target` (a :class:`ViewFactory`),
       but only if the occurring Event matches `event`.
       """
    def __init__(self, user_interface, event, target):
        self.user_interface = user_interface
        self.event_name = event.name
        self.target = target

    def should_handle(self, event_ocurrence):
        return self.event_name == event_ocurrence.name

    def get_destination_absolute_url(self, event_ocurrence):
        if self.target.matches_view(self.user_interface.controller.current_view):
            url = SubResource.get_parent_url()
        else:
            try:
                url = self.target.get_absolute_url(self.user_interface, **event_ocurrence.arguments)
            except ValidationConstraint, ex:
                raise ProgrammerError(u'The arguments of %s are invalid for transition target %s: %s' % \
                    (event_ocurrence, self.target, ex))
        return url


class Transition(EventHandler):
    """A Transition is a special kind of :class:`EventHandler`. Transitions are used to define
       how a user is transitioned amongst many Views in response to different Events that may occur.
       A Transition will only be used if its `source` (a :class:`ViewFactory`) matches the current View
       and if its `guard` (an :class:`Action`) returns True. If not specified, a `guard` is used which
       always the Transition to be used."""
    @arg_checks(source=IsInstance('reahl.web.fw:ViewFactory'), target=IsInstance('reahl.web.fw:ViewFactory'))
    def __init__(self, controller, event, source, target, guard=None):
        super(Transition, self).__init__(controller.user_interface, event, target)
        self.controller = controller
        self.source = source
        self.guard = guard if guard else Allowed(True)
    
    def should_handle(self, event_ocurrence):
        return (self.source.matches_view(self.controller.current_view)) and \
               super(Transition, self).should_handle(event_ocurrence) and \
               self.guard(event_ocurrence)


class FactoryDict(set):
    def __init__(self, initial_set, *args):
        super(FactoryDict, self).__init__(initial_set)
        self.args = args
        
    def get_factory_for(self, key):
        found_factory = None
        best_rating = 0
        for factory in self:
            rating = factory.is_applicable_for(key)
            if rating > best_rating:
                best_rating = rating
                found_factory = factory
        logging.debug('Found factory: %s for "%s"' % (found_factory, key))
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


class Controller(object):
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

    @arg_checks(event=IsInstance(Event), target=IsInstance(u'reahl.web.fw:ViewFactory', allow_none=True))
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
        transition = Transition(self, event, source, source, guard=guard)
        self.event_handlers.append(transition)
        return transition

    def define_return_transition(self, event, source, guard=None):
        transition = Transition(self, event, source, ReturnToCaller(source.as_bookmark(self.user_interface)).as_view_factory(), guard=guard)
        self.event_handlers.append(transition)
        return transition


    def define_transition(self, event, source, target, guard=None):
        transition = Transition(self, event, source, target, guard=guard)
        self.event_handlers.append(transition)
        return transition

    def define_local_transition(self, event, source, guard=None):
        transition = Transition(self, event, source, source, guard=guard)
        self.event_handlers.append(transition)
        return transition

    def define_return_transition(self, event, source, guard=None):
        transition = Transition(self, event, source, ReturnToCaller(source.as_bookmark(self.user_interface)).as_view_factory(), guard=guard)
        self.event_handlers.append(transition)
        return transition

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


class UserInterface(object):
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
        self.relative_path = u''                     #: The path of the current Url, relative to this UserInterface
        self.page_factory = None
        if not for_bookmark:
            self.update_relative_path()
        self.sub_uis = FactoryDict(set())
        self.controller = Controller(self)
        self.assemble(**ui_arguments)
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

    @classmethod 
    def make_full_path(cls, parent_ui, relative_path):
        if parent_ui:
            path = parent_ui.base_path + relative_path
            if path.startswith(u'//'):
                return path[1:]
            return path
        return relative_path

    @property
    def current_view(self):
        """The :class:`View` which is targetted by the URL of the current :class:webob.Request."""
        return self.controller.view_for(self.relative_path)

    def assemble(self, **ui_arguments):
        """Programmers override this method in order to define the contents of their UserInterface. This mainly
           means defining Views or other UserInterfaces inside the UserInterface being assembled. The default
           implementation of `assemble` is empty, so there's no need to call the super implementation
           from an overriding implementation."""
        pass

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

    @arg_checks(widget_class=IsSubclass(u'reahl.web.fw:Widget'))
    def define_page(self, widget_class, *args, **kwargs):
        """Called from `assemble` to create the :class:`WidgetFactory` to use when the framework
           needs to create a Widget for use as the page for this UserInterface. Pass the class of
           Widget that will be constructed in `widget_class`.  Next, pass all the arguments that should
           be passed to `widget_class` upon construction, except the first one (its `view`).
        """
        checkargs_explained(u'define_page was called with arguments that do not match those expected by %s' % widget_class, 
                            widget_class.__init__, NotYetAvailable(u'view'), *args, **kwargs)

        self.page_factory = widget_class.factory(*args, **kwargs)
        return self.page_factory

    @deprecated(u'Please use .define_page() instead.')
    def define_main_window(self, *args, **kwargs):
        return self.define_page(*args, **kwargs)

    def page_slot_for(self, view, page, local_slot_name):
        if page.created_by is self.page_factory:
            return local_slot_name
        try:
            name = self.slot_map[local_slot_name]
        except KeyError:
            message = u'When trying to plug %s into %s: slot "%s" of %s is not mapped. Mapped slots: %s' % \
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

    def define_view(self, relative_path, title=None, page=None, slot_definitions=None, detour=False, view_class=None, read_check=None, write_check=None, cacheable=False, **assemble_args):
        """Called from `assemble` to specify how a :class:`View` will be created when the given URL (`relative_path`)
           is requested from this UserInterface.
        
           :param title: The title to be used for the :class:`View`.
           :param page: A :class:`WidgetFactory` that will be used as the page to be rendered for this :class:`View` (if specified).
           :param slot_definitions: A dictionary stating which :class:`WidgetFactory` to use for plugging in which :class:`Slot`.
           :param detour: Specifies whether this :class:`View` is a :class:`Detour` or not.
           :param view_class: The class of :class:`View` to be constructed (in the case of parameterised :class:`View` s).
           :param read_check: A no-arg function returning a boolean value. It will be called to determine whether the current 
             user is allowed to see this :class:`View` or not.
           :param write_check: A no-arg function returning a boolean value. It will be called to determine whether the current 
           :param cacheable: Whether this View can be cached.
             user is allowed to perform any actions linked to this :class:`View` or not.
           :param assemble_args: keyword arguments that will be passed to the `assemble` of this :class:`View` upon creation
        """
        title = title or _(u'Untitled')
        slot_definitions = slot_definitions or {}
        path_argument_fields, passed_kwargs = self.split_fields_and_hardcoded_kwargs(assemble_args)

        view_class = view_class or UrlBoundView
        checkargs_explained(u'.define_view() was called with incorrect arguments for %s' % view_class.assemble, 
                            view_class.assemble, **assemble_args)

        factory = ViewFactory(ParameterisedPath(relative_path, path_argument_fields), title, slot_definitions, 
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
           :param view_class: The class of :class:`View` which is to be constructed.
           :param factory_method: Pass a method that will be called to create a :class:`View` instead of passing `view_class` 
             if you'd like.
           :param read_check:
             Same as with `define_view`.
           :param write_check:
             Same as with `define_view`. 
           :param assemble_args:
             Same as with `define_view`.
        """
        path_argument_fields, passed_kwargs = self.split_fields_and_hardcoded_kwargs(assemble_args)

        if not factory_method:
            view_class = view_class or UrlBoundView
            checkargs_explained(u'.define_regex_view() was called with incorrect arguments for %s' % \
                            view_class.assemble, view_class.assemble, **assemble_args)

        factory = ViewFactory(RegexPath(path_regex, path_template, path_argument_fields), None, {}, 
                              view_class=view_class, factory_method=factory_method, read_check=None, write_check=None, **passed_kwargs)
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
        return self.add_view_factory(ViewFactory(RegexPath(relative_path, relative_path, {}), None, {}, factory_method=create_redirect_view))

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
           :param name: A name for the :class:`UserInterface` that is grafted on. The name should be unique in an application.
           :param assemble_args: Keyword arguments that will be passed to the `assemble` method of the grafted :class:`UserInterface`
             after construction.
        """
        path_argument_fields, passed_kwargs = self.split_fields_and_hardcoded_kwargs(assemble_args)
        checkargs_explained(u'.define_user_interface() was called with incorrect arguments for %s' % ui_class.assemble, 
                            ui_class.assemble,  **assemble_args)

        ui_factory = UserInterfaceFactory(self, ParameterisedPath(path, path_argument_fields), slot_map, ui_class, name, **passed_kwargs)
        self.add_user_interface_factory(ui_factory)
        return ui_factory

    @deprecated(u'Please use .define_user_interface() instead')
    def define_region(self, *args, **kwargs):
        return self.define_user_interface(*args, **kwargs)

    def define_regex_user_interface(self, path_regex, path_template, ui_class, slot_map, name=None, **assemble_args):
        """Called from `assemble` to create a :class:`UserInterfaceFactory` for a parameterised :class:`UserInterface` that will 
           be created when an URL is requested that matches `path_regex`. See also `define_regex_view`.
           
           Arguments are similar to that of `define_regex_view`, except for:
           
           :param slot_map: (See `define_user_interface`.)
           :param name: (See `define_user_interface`.)
        """
        path_argument_fields, passed_kwargs = self.split_fields_and_hardcoded_kwargs(assemble_args)
        checkargs_explained(u'.define_regex_user_interface() was called with incorrect arguments for %s' % ui_class.assemble, 
                            ui_class.assemble,  **assemble_args)

        regex_path = RegexPath(path_regex, path_template, path_argument_fields)
        ui_factory = UserInterfaceFactory(self, regex_path, slot_map, ui_class, name, **passed_kwargs)
        self.add_user_interface_factory(ui_factory)
        return ui_factory

    @deprecated(u'Please use .define_regex_user_interface() instead')
    def define_regex_region(self, *args, **kwargs):
        return self.define_regex_user_interface(*args, **kwargs)

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
           as configured, as configured by the setting `web.static_root`.
        """
        ui_name = u'static_%s' % path
        ui_factory = UserInterfaceFactory(self, RegexPath(path, path, {}), IdentityDictionary(), StaticUI, ui_name, files=DiskDirectory(path))
        return self.add_user_interface_factory(ui_factory)

    def define_static_files(self, path, files):
        """Defines an URL which is mapped to serve the list of static files given.
        """
        ui_name = u'static_%s' % path
        ui_factory = UserInterfaceFactory(self, RegexPath(path, path, {}), IdentityDictionary(), StaticUI, ui_name, files=FileList(files))
        return self.add_user_interface_factory(ui_factory)

    def get_relative_path_for(self, full_path):
        if self.base_path == u'/':
            return full_path
        return full_path[len(self.base_path):]
    
    def get_absolute_url_for(self, relative_path):
        if self.base_path == u'/':
            new_path = relative_path
        else:
            new_path = self.base_path+relative_path
        url = Url(new_path).as_network_absolute()
        url.make_locale_absolute()
        return url

    @arg_checks(relative_path=IsInstance(basestring))
    def get_bookmark(self, description=None, relative_path=None, query_arguments=None, ajax=False):
        """Returns a :class:`Bookmark` for the :class:`View` present on `relative_path`.
        
           :param description: By default the :class:`Bookmark` will use the title of the target :class:`View` as 
             its description, unless overridden by passing `description`.
           :param query_arguments: A dictionary containing arguments that should be put onto the query string of the
             Url of the Bookmark.
           :param ajax: Links to Bookmarks for which ajax=True are changed browser-side to enable
             ajax-related functionality. This is used by the framework and is not meant
             to be set by a programmer.
        """
        view = self.view_for(relative_path)
        if not view.exists:
            raise ProgrammerError(u'no such bookmark (%s)' % relative_path)
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


@deprecated(u'Region has been renamed to UserInterface, please use UserInterface instead')
class Region(UserInterface):
    pass


class StaticUI(UserInterface):
    def create_view(self, relative_path, user_interface, file_path=None):
        return FileView(user_interface, self.files.create(file_path))

    def assemble(self, files=None):
        self.files = files
        self.define_regex_view(u'(?P<file_path>.*)', u'${file_path}', factory_method=self.create_view, file_path=Field())


class Bookmark(object):
    """Like a bookmark in a browser, an instance of this class is a way to refer to a View in a WebApplication
       that takes into account where the View is relative to the root of the URL hierarchy of the application.
    
       Bookmark should not generally be constructed directly by a programmer, use one of the following to
       obtain a Bookmark:
       
       - `View.as_bookmark`
       - `UserInterface.get_bookmark`
       - `Bookmark.for_widget`
       
       :param base_path: The entire path of the UserInterface to which the target View belongs.
       :param relative_path: The path of the target View, relative to its UserInterface.
       :param description: The textual description to be used by links to the target View.
       :param query_arguments: A dictionary containing name, value mappings to be put onto the query string of the href of this Bookmark.
       :param ajax: (not for general use).
       :param detour: Set this to True, to indicate that the target View is marked as being a detour (See :class:`UrlBoundView`).
       :param exact: (not for general use).
       :param read_check: A no-args callable, usually the read_check of the target View. If it returns True, the current user will be allowed to see (but not click) links representing this Bookmark.
       :param write_check: A no-args callable, usually the write_check of the target View. If it returns True, the current user will be allowed to click links representing this Bookmark.
    """
    @classmethod
    def for_widget(cls, description, query_arguments=None, **bookmark_kwargs):
        """Creates a "page-internal" Bookmark for a Widget with the arguments as specified.
        
           :param description: The textual description that will be used in links created for this Bookmark.
           :param query_arguments: A dictionary containing the arguments the target Widget should have when a user
                                   follows a link.
           :param bookmark_kwargs: Keyword arguments sent as-is to the constructor of Bookmark.
        """
        return Bookmark(u'', u'', description, query_arguments=query_arguments, ajax=True, **bookmark_kwargs)

    def __init__(self, base_path, relative_path, description, query_arguments=None, ajax=False, detour=False, exact=True, read_check=None, write_check=None):
        self.base_path = base_path
        self.relative_path = relative_path
        self.description = description
        self.query_arguments = query_arguments or {}
        self.ajax = ajax
        self.detour = detour
        self.exact = exact
        self.read_check = read_check
        self.write_check = write_check

    def with_description(self, description):
        """Returns a new Bookmark, like this one, except that it has `description` for its description."""
        return Bookmark(self.base_path, self.relative_path, description, query_arguments=self.query_arguments, ajax=self.ajax,
                        detour=self.detour, read_check=self.read_check, write_check=self.write_check)

    @property
    def href(self):
        query_arguments = dict(self.query_arguments)
        if self.detour:
            request = WebExecutionContext.get_context().request
            query_arguments['returnTo'] = request.url
        path = (self.base_path + self.relative_path).replace(u'//',u'/')
        url = Url(path)
        url.make_locale_absolute()
        url.set_query_from(query_arguments)
        return url

    @property
    def is_page_internal(self):
        """Answers whether this Bookmark is for a Widget on the current page only."""
        return self.ajax and not (self.base_path or self.relative_path)

    def __add__(self, other):
        """You can add a page-internal Bookmark to the Bookmark for a View."""
        if not other.is_page_internal:
            raise ProgrammerError(u'only page-internal Bookmarks can be added to other bookmarks')
        query_arguments = {}
        query_arguments.update(self.query_arguments)
        query_arguments.update(other.query_arguments)
        return Bookmark(self.base_path, self.relative_path, other.description, query_arguments=query_arguments,
                        ajax=other.ajax, detour=self.detour, read_check=self.read_check, write_check=self.write_check)


class RedirectToScheme(HTTPSeeOther):
    def __init__(self, scheme):
        self.scheme = scheme
        super(RedirectToScheme, self).__init__(location=str(self.compute_target_url()))

    def compute_target_url(self):
        context = WebExecutionContext.get_context()
        url = Url(context.request.url)
        url.set_scheme(self.scheme)
        return url


class Redirect(HTTPSeeOther):
    """An exception that can be raised by a :class:`ViewPreCondition` to send the user to a different
       View (matching `target`, a ViewFactory).
    """
    def __init__(self, target):
        self.target = target
        super(Redirect, self).__init__(location=str(self.compute_target_url()))
     
    def compute_target_url(self):
        return self.target.href.as_network_absolute()


class Detour(Redirect):
    """An exception that can be raised by a :class:`ViewPreCondition` to send the user temporarily to a different
       View (matching `target`, a ViewFactory). If `return_to` (also a ViewFactory) is specified, and a user triggers
       a :class:`ReturnTransition`, the user will be returned to a View matching `return_to`. If `return_to` is
       not specified, the user will be returned to the View for which the :class:`ViewPreCondition` failed initially.
    """
    def __init__(self, target, return_to=None):
        self.return_to = return_to or ReturnToCurrent()
        super(Detour, self).__init__(target)

    def compute_target_url(self):
        redirect_url = super(Detour, self).compute_target_url()
        qs = {'returnTo': str(self.return_to.href.as_network_absolute()) }
        redirect_url.set_query_from(qs)
        return redirect_url


class Return(Redirect):
    """An exception that can be raised by a :class:`ViewPreCondition` to send the user back to a View which originally
       failed a PreCondition that sent the user elsewhere via a :class:`Detour`.
    """
    def __init__(self, default):
        super(Return, self).__init__(ReturnToCaller(default))


class WidgetList(list):
    def render(self):
        return u''.join([child.render() for child in self])

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


class Widget(object):
    """Any user interface element in Reahl is a Widget. A direct instance of this class will not display anything
       when rendered. A User interface is composed of Widgets by adding other Widgets to a Widget such as this one,
       forming a whole tree of Widgets.
    
    :param view: The current View.
    :param read_check: A no-arg callable. If it returns True, the Widget will be rendered for the current user, else not.
    :param write_check: A no-arg callable. If it returns True, the current user is allowed to write to this Widget.
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

    @arg_checks(view=IsInstance(u'reahl.web.fw:View'))
    def __init__(self, view, read_check=None, write_check=None):
        self.children = WidgetList()         #: All the Widgets that have been added as children of this Widget,
                                             #: in order of being added.
        self.view = view                     #: The current view, as passed in at construction
        self.priority = None
        self.content_type = 'text/html'
        self.charset = 'utf-8'
        self.default_slot_definitions = {}
        self.slot_contents = {}
        self.marked_as_security_sensitive = False
        self.set_arguments_from_query_string()
        self.read_check = read_check         #:
        self.write_check = write_check       #:
        self.created_by = None               #: The factory that was used to create this Widget

    def set_creating_factory(self, factory):
        self.created_by = factory

    @exposed
    def query_fields(self, fields):
        """Override this method to parameterise this this Widget. The Widget will find its arguments from the current
           query string, using the names and validation details as given by the Field instances assigned to `fields`.
           
           The `@exposed query_fields` of a Widget is exactly like the `@exposed fields` used for input to a model object.
        """
        pass
        
    def set_arguments_from_query_string(self):
        request = WebExecutionContext.get_context().request
        self.query_fields.accept_input(request.GET)

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
        return self.read_check and hasattr(self.read_check, u'is_specified') and self.read_check.is_specified

    def set_priority(self, secondary=None, primary=None):
        if primary: 
            self.priority = u'primary'
        elif secondary:
            self.priority = u'secondary'

    @arg_checks(child=IsInstance(u'reahl.web.fw:Widget'))
    def add_child(self, child):
        """Adds another Widget (`child`) as a child Widget of this one."""
        self.children.append(child)
        return child
        
    @arg_checks(child=IsInstance(u'reahl.web.fw:Widget'))
    def insert_child(self, index, child):
        """Adds another Widget (`child`) as a child Widget of this one, at `index` position amongst existing children."""
        self.children.insert(index, child)
        return child

    def add_children(self, children):
        """Adds all Widgets in `children` children Widgets of this one."""
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
            return u''

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
        slots_to_plug_in = set([self.user_interface.page_slot_for(view, self, local_slot_name)
                                for local_slot_name in view.slot_definitions.keys()])
        slots_available = set(self.available_slots)
        if not slots_to_plug_in.issubset(slots_available):
            invalid_slots = slots_to_plug_in - slots_available
            invalid_slots = u','.join(invalid_slots)
            available_slots = u','.join(slots_available)

            message = u'An attempt was made to plug Widgets into the following slots that do not exist on page %s: %s\n' % (self, invalid_slots)
            message += u'(expected one of these slot names: %s)\n' % available_slots
            message += u'View %s plugs in the following:\n' % view
            for local_slot_name, factory in view.slot_definitions.items():
                page_slot_name = self.user_interface.page_slot_for(view, self, local_slot_name)
                message += '%s is plugged into slot "%s", which is mapped to slot "%s"' % \
                (factory, local_slot_name, page_slot_name)

            raise ProgrammerError(message)

    def get_forms(self):
        forms = []
        for child in self.children:
            forms.extend(child.get_forms())
        return forms

    def check_forms(self):
        checked_forms = {}
        for form in self.get_forms():
            if form.css_id not in checked_forms.keys():
                checked_forms[form.css_id] = form
            else:
                existing_form = checked_forms[form.css_id]
                message = u'More than one form was added using the same unique_name: %s and %s' % (form, existing_form)
                raise ProgrammerError(message)

    def plug_in(self, view):
        self.check_slots(view)
        
        for local_slot_name, widget_factory in view.slot_definitions.items():
            self.slot_contents[self.user_interface.page_slot_for(view, self, local_slot_name)] = widget_factory.create(view)
        for slot_name, widget_factory in self.default_slot_definitions.items():
            if slot_name not in self.slot_contents.keys():
                self.slot_contents[slot_name] = widget_factory.create(view)
        self.slot_contents[u'reahl_header'] = HeaderContent(self)
        self.slot_contents[u'reahl_footer'] = FooterContent(self)
        self.fill_slots(self.slot_contents)
        self.attach_out_of_bound_forms(view.out_of_bound_forms)
        self.check_forms()

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

    def attach_out_of_bound_forms(self, forms):
        for child in self.children:
            child.attach_out_of_bound_forms(forms)


class ViewPreCondition(object):
    """A ViewPreCondition can be used to control whether a user can visit a particular View or not. If the 
       `condition_callable` returns False, `exception` will be raised. Useful exceptions exist, like :class:`Detour` 
       and :class:`Return`.
       
       :param condition_callable: A no-arg callable indicating whether this condition is satisfied (returns True) 
                                  or not (returns False).
       :param exception: An exception to be raised if this condition is not satisfied.
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
            request = WebExecutionContext.get_context().request
            if request.method.lower() not in [u'get', u'head']:
                raise HTTPNotFound()
            raise self.exception

    def negated(self, exception=None):
        def condition_callable(*args, **kwargs):
            return not self.condition_callable(*args, **kwargs)
        return ViewPreCondition(condition_callable, exception or self.exception)


class RatedMatch(object):
    def __init__(self, match, rating):
        self.match = match
        self.rating = rating


class RegexPath(object):
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
        return self.match_foreign_view(relative_path).match.group(u'base_path')

    def get_relative_part_in(self, relative_path):
        return self.match_foreign_view(relative_path).match.group(u'relative_path')

    def has_relative_part_in(self, relative_path):
        matched = self.match_foreign_view(relative_path).match
        return (matched and matched.group(u'relative_path')) is not None

    def get_relative_path_from(self, arguments):
        arguments_as_input = self.get_arguments_as_input(arguments)
        return string.Template(self.template).substitute(arguments_as_input)

    def match(self, relative_path):
        match = re.match(self.regex, relative_path)
        rating = 1 if match else 0
        return RatedMatch(match, rating)

    def match_view(self, relative_path):
        view_regex = u'(?P<view_path>^%s)(/?_.*)?(\?.*)?$' % self.regex  # Note: if the path_regex ends in / the / in the last bit should not be
                                                   #       there, else it should. I don't know how to make this more precise.
        match = re.match(view_regex, relative_path)
        rating = len(match.group(u'view_path')) if match else 0
        return RatedMatch(match, rating)

    def match_foreign_view(self, relative_path):
        own_path = u'' if self.regex == u'/' else self.regex
        foreign_view_regex = u'^(?P<base_path>%s)(?P<relative_path>/.*(/?_.*)?(\?.*)?)?$' % own_path  # Note: if the path_regex ends in / the / in the last bit should not be
                                                   #       there, else it should. I don't know how to make this more precise.
        match = re.match(foreign_view_regex, relative_path)
        rating = len(match.group(u'base_path'))+1 if match else 0
        return RatedMatch(match, rating)

    def get_temp_url_argument_field_index(self, for_fields, data_dict=None):
        data_dict = data_dict or {}
        fields = StandaloneFieldIndex(data_dict)
        fields.update_copies(for_fields)
        return fields

    def parse_arguments_from_fields(self, for_fields, relative_path):
        if not for_fields:
            return {}
        matched_arguments = self.match(relative_path).match.groupdict()
        fields = self.get_temp_url_argument_field_index(for_fields)
        raw_input_values = dict([(str(key), urllib.unquote(value or u''))
                                     for key, value in matched_arguments.items()])
        fields.accept_input(raw_input_values)
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
        super(ParameterisedPath, self).__init__(regex, template, argument_fields)

    def make_regex(self, discriminator, argument_fields):
        arguments_part = u''
        for argument_name in argument_fields.keys():
            arguments_part += u'(/(?P<%s>[^/]*))' % argument_name

        if discriminator.endswith(u'/') and arguments_part.startswith(u'(/'):
            arguments_part = arguments_part[:1]+arguments_part[2:]
        return discriminator+arguments_part

    def make_template(self, discriminator, argument_fields):
        arguments_part = u''
        for argument_name in argument_fields.keys():
            arguments_part += u'/${%s}' % argument_name

        if discriminator.endswith(u'/') and arguments_part.startswith(u'(/'):
            arguments_part = arguments_part[:1]+arguments_part[2:]
        return discriminator+arguments_part


class Factory(object):
    def __init__(self, factory_method):
        super(Factory, self).__init__()
        self.factory_method = factory_method

    def create(self, *args, **kwargs):
        return self.factory_method(*args, **kwargs)


class FactoryFromUrlRegex(Factory):
    def __init__(self, regex_path, factory_method, factory_kwargs):
        self.regex_path = regex_path
        self.factory_kwargs = factory_kwargs
        super(FactoryFromUrlRegex, self).__init__(factory_method)

    def create(self, relative_path, *args, **kwargs):
        try:
            create_kwargs = self.create_kwargs(relative_path, **kwargs)
            create_args = self.create_args(relative_path, *args)
            return super(FactoryFromUrlRegex, self).create(*create_args, **create_kwargs)
        except TypeError, ex:
            if len(inspect.trace()) == 1:
                # Note: we modify the args, and then just raise, because we want the original stack trace
                ex.args = (ex.args[0]+u' (from regex "%s")' % self.regex_path.regex,)
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
        super(UserInterfaceFactory, self).__init__(regex_path, ui_class, ui_kwargs)
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
        user_interface = super(UserInterfaceFactory, self).create(relative_path, for_bookmark, *args)
        for predefined_ui in self.predefined_uis:
            user_interface.add_user_interface_factory(predefined_ui)
        return user_interface 

    def create_from_url_args(self, for_bookmark=False, **url_args):
        relative_path = self.regex_path.get_relative_path_from(url_args)
        return self.create(relative_path, for_bookmark=for_bookmark)

    def create_args(self, relative_path, *args):
        relative_base_path = self.regex_path.get_base_part_in(relative_path) or u'/'
        return (self.parent_ui, relative_base_path, self.slot_map)+args+(self.ui_name,)

    def get_bookmark(self, *ui_args, **bookmark_kwargs):
        ui_relative_path = self.regex_path.get_relative_path_from(ui_args)
        user_interface = self.create(ui_relative_path, for_bookmark=True) 
        return user_interface.get_bookmark(**bookmark_kwargs)

    def is_applicable_for(self, relative_path):
        return self.regex_path.match_foreign_view(relative_path).rating


class SubResourceFactory(FactoryFromUrlRegex):
    def __init__(self, regex_path, factory_method):
        super(SubResourceFactory, self).__init__(regex_path, factory_method, {})

    def create_args(self, relative_path, *args):
        return args


class ViewFactory(FactoryFromUrlRegex):
    """Used to specify to the framework how it should create a :class:`View`, once needed. This class should not be
       instantiated directly. Programmers should use `UserInterface.define_view` and related methods to specify what Views
       a UserInterface should have. These methods return the ViewFactory so created.

       In the `.assemble()` of a UserInterface, ViewFactories are passed around to denote Views as the targets of Events
       or the source and target of Transitions.
    """
    def __init__(self, regex_path, title, slot_definitions, page_factory=None, detour=False, view_class=None, factory_method=None, read_check=None, write_check=None, cacheable=False, view_kwargs=None):
        self.detour = detour
        self.preconditions = []
        self.title = title
        self.slot_definitions = dict(slot_definitions)
        self.view_class = view_class or UrlBoundView
        self.read_check = read_check
        self.write_check = write_check
        self.cacheable = cacheable
        self.page_factory = page_factory
        super(ViewFactory, self).__init__(regex_path, factory_method or self.create_view, view_kwargs or {})

    def create_args(self, relative_path, *args):
        if SubResource.is_for_sub_resource(relative_path):
            relative_path = SubResource.get_view_path_for(relative_path)
        return (relative_path,)+args

    def create_view(self, relative_path, user_interface, **view_arguments):
        return self.view_class(user_interface, relative_path, self.title, self.slot_definitions, page_factory=self.page_factory, detour=self.detour, read_check=self.read_check, write_check=self.write_check, cacheable=self.cacheable, **view_arguments)

    def __str__(self):
        return '<ViewFactory for %s>' % self.view_class

    def __hash__(self):
        return hash(self.regex_path)

    def __eq__(self, other):
        return hash(other) == hash(self)

    def get_relative_path(self, **arguments):
        return self.regex_path.get_relative_path_from(arguments)

    def matches_view(self, view):
        return self.is_applicable_for(view.relative_path)

    def get_absolute_url(self, user_interface, **arguments):
        url = user_interface.get_absolute_url_for(self.get_relative_path(**arguments))
        url.query = self.get_query_string()
        return url

    def get_query_string(self):
        request = ExecutionContext.get_context().request
        return_to = request.GET.get(u'returnTo')
        if return_to:
            return urllib.urlencode({u'returnTo': return_to})
        return u''

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

    def as_bookmark(self, user_interface, description=None, query_arguments=None, ajax=False, **url_arguments):
        """Returns a :class:`Bookmark` to the View this Factory represents.

           :param user_interface: The user_interface where this ViewFactory is defined.
           :param description: A textual description which will be used on links that represent the Bookmark on the user interface.
           :param query_arguments: A dictionary with (name, value) pairs to put on the query string of the Bookmark.
           :param ajax: (not for general use)
           :param url_arguments: Values for the arguments of the parameterised View to which the Bookmark should lead. (Just
                                 omit these if the target View is not parameterised.)
        """
        relative_path = self.get_relative_path(**url_arguments)
        view = self.create(relative_path, user_interface)
        return view.as_bookmark(description=description, query_arguments=query_arguments, ajax=ajax)

    def create(self, relative_path, *args, **kwargs):
        try:
            instance = super(ViewFactory, self).create(relative_path, *args, **kwargs)
        except ValidationConstraint, ex:
            message = u'The arguments contained in URL "%s" are not valid for %s: %s' % (relative_path, self, ex)
            raise ProgrammerError(message)
        for condition in self.preconditions:
            instance.add_precondition(condition)
        return instance


class WidgetFactory(Factory):
    """An object used by the framework to create a Widget, once needed.

       :param widget_class: The kind of Widget to be constructed.
       :param widget_args:  All the arguments needed by `widget_class` except the first argument of Widgets: `view`
       :param widget_kwargs: All the keyword arguments of `widget_class`.
    """
    def __init__(self, widget_class, *widget_args, **widget_kwargs):
        checkargs_explained(u'An attempt was made to create a WidgetFactory for %s with arguments that do not match what is expected for %s' % (widget_class, widget_class), widget_class.__init__, NotYetAvailable(u'view'), *widget_args, **widget_kwargs)

        super(WidgetFactory, self).__init__(self.create_widget)
        self.widget_class = widget_class
        self.widget_args = widget_args
        self.widget_kwargs = widget_kwargs
        self.default_slot_definitions = {}

    def create_widget(self, view):
        widget = self.widget_class(view, *self.widget_args, **self.widget_kwargs)
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

    def __str__(self):
        return '<WidgetFactory for %s>' % self.widget_class

class ViewPseudoFactory(ViewFactory):
    def __init__(self, bookmark):
        super(ViewPseudoFactory, self).__init__(RegexPath(u'/', u'/', {}), u'', {})
        self.bookmark = bookmark

    def matches_view(self, view):
        return False

    def get_absolute_url(self, user_interface, **arguments):
        return self.bookmark.href.as_network_absolute()


class PseudoBookmark(object):
    def as_view_factory(self):
        return ViewPseudoFactory(self)

class ReturnToCaller(PseudoBookmark):
    def __init__(self, default):
        self.default = default

    @property
    def href(self):
        request = WebExecutionContext.get_context().request
        if request.GET.has_key('returnTo'):
            return Url(request.GET['returnTo'])
        return self.default.href


class ReturnToCurrent(PseudoBookmark):
    @property
    def href(self):
        url = Url(WebExecutionContext.get_context().request.url)
        url.make_network_relative()
        return url



class View(object):
    """A View is how Reahl denotes the target of any URL. Although there are many types of View (to deal with static files, 
      for example), the most used View is an :class:`UrlBoundView`.
    """
    exists = True
    is_dynamic = False

    def __init__(self, user_interface):
        super(View, self).__init__()
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

    def plug_into(self, page):
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

       A programmer *should* create subclasses of UrlBoundView when creating parameterised Views.

       A programmer *should not* construct instances of this class (or its subclasses). Rather use
       `UserInterface.define_view` and related methods to define ViewFactories which the framework will 
       use at the correct time to instantiate an UrlBoundView.

       The `.view` of any Widget is an instance of UrlBoundView.
    """
    is_dynamic = True

    def as_factory(self):
        regex_path = ParameterisedPath(self.relative_path, {})
        return ViewFactory(regex_path, self.title, self.slot_definitions, page_factory=self.page_factory, detour=self.detour, view_class=self.__class__, read_check=self.read_check, write_check=self.write_check, cacheable=self.cacheable)

    def __init__(self, user_interface, relative_path, title, slot_definitions, page_factory=None, detour=False, read_check=None, write_check=None, cacheable=False, **view_arguments):
        if re.match(u'/_([^/]*)$', relative_path):
            raise ProgrammerError(u'you cannot create UrlBoundViews with /_ in them - those are reserved URLs for SubResources')
        super(UrlBoundView, self).__init__(user_interface)
        self.out_of_bound_forms = []
        self.relative_path = relative_path
        self.title = title                          #: The title of this View
        self.preconditions = []       
        self.slot_definitions = slot_definitions
        self.detour = detour
        self.read_check = read_check or self.allowed
        self.write_check = write_check or self.allowed
        self.cacheable = cacheable
        self.page_factory = page_factory
        self.assemble(**view_arguments)

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
        pass

    def __str__(self):
        return u'<UrlBoundView "%s" on "%s">' % (self.title, self.relative_path)

    def plug_into(self, page):
        page.plug_in(self)  # Will create all Widgets specified by the View, and thus their SubResources if any

    def set_slot(self, name, contents):
        """Supplies a Factory (`contents`) for the framework to use to create the contents of the Slot named `name`."""
        self.slot_definitions[name] = contents

    def set_page(self, page_factory):
        """Supplies a Factory for the page to be used when displaying this View."""
        self.page_factory = page_factory

    def resource_for(self, full_path, page):
        if SubResource.is_for_sub_resource(full_path):
            return self.user_interface.sub_resource_for(full_path)
        return super(UrlBoundView, self).resource_for(full_path, page)

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
        if request_method.upper() in [u'GET',u'HEAD']:
            allowed = self.read_check()
        else:
            allowed = self.write_check()
        if not allowed:
            raise HTTPForbidden()

    def as_bookmark(self, description=None, query_arguments=None, ajax=False):
        """Returns a Bookmark for this UrlBoundView.

           :param description: A textual description to be used by links representing this View to a user.
           :param query_arguments: A dictionary mapping names to values to be used for query string arguments.
           :param ajax: (not for general use)
        """
        return Bookmark(self.user_interface.base_path, self.relative_path, 
                        description=description or self.title,
                        query_arguments=query_arguments, ajax=ajax, detour=self.detour,
                        read_check=self.read_check, write_check=self.write_check)

    def add_out_of_bound_form(self, out_of_bound_form):
        self.out_of_bound_forms.append(out_of_bound_form)
        return out_of_bound_form


class RedirectView(UrlBoundView):
    def __init__(self, user_interface, relative_path, to_bookmark):
        super(RedirectView, self).__init__(user_interface, relative_path, u'', {})
        self.to_bookmark = to_bookmark

    def as_resource(self, page):
        raise HTTPSeeOther(location=str(self.to_bookmark.href.as_network_absolute()))


class PseudoView(View):
    relative_path = u'/'


class NoView(PseudoView):
    """A special kind of View to indicate that no View was found."""
    exists = False

class UserInterfaceRootRedirectView(PseudoView):
    def as_resource(self, page):
        raise HTTPSeeOther(location=str(self.user_interface.get_absolute_url_for(u'/').as_network_absolute()))
    


class HeaderContent(Widget):
    main_widget = None
    def __init__(self, page):
        super(HeaderContent, self).__init__(page.view)
        self.page = page

    def header_only_material(self):
        result = u''
        # From: http://remysharp.com/2009/01/07/html5-enabling-script/ 
        result += u'\n<!--[if lt IE 9]>'
        result += u'<script src="/static/html5shiv-printshiv-3.6.3.js" type="text/javascript"></script>'
        result += u'<![endif]-->'
        # From: http://code.google.com/p/ie7-js/ 
        # Not sure if this does not perhaps interfere with YUI reset stuff? 
        result += u'\n<!--[if lte IE 9]>'  
        result += u'<script src="/static/IE9.js" type="text/javascript"></script>'
        result += u'<![endif]-->'  
        result += u'\n<script type="text/javascript" src="/static/reahl.js"></script>'
        result += u'\n<link rel="stylesheet" href="/static/reahl.css" type="text/css">' 
        return result

    def render_document_ready_material(self):
        result = u'\n<script type="text/javascript">\n'
        result += u'jQuery(document).ready(function($){\n'
        result += u'$(\'body\').addClass(\'enhanced\');\n'
        js = set()
        js.update(self.page.get_js())
        for item in js:
            result += item+u'\n'
        result += u'\n});'
        result += u'\n</script>\n'
        return result
        
    def render(self):
        return self.header_only_material() + self.render_document_ready_material()
    


class FooterContent(HeaderContent):
    def render(self):
        #from http://ryanpricemedia.com/2008/03/19/jquery-broken-in-internet-explorer-put-your-documentready-at-the-bottom/
        return u'<!--[if IE 6]>' + self.render_document_ready_material() +  u'<![endif]-->'


class Resource(object):
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

        method_handler = getattr(self, u'handle_%s' % request.method.lower())
        return method_handler(request)


class SubResource(Resource):
    """A Resource that a Widget can register underneath the URL of the View the Widget is present on.
       This can be used to create URLs for whatever purpose the Widget may need server-side URLs for.

       :param unique_name: A name for this subresource which will be unique in the UserInterface where it is used.
    """
    sub_regex = u'sub_resource'          """The regex used to match incoming URLs against the URL of this SubResource."""
    sub_path_template = u'sub_resource'  """A `PEP-292 <http://www.python.org/dev/peps/pep-0292/>`_ template in a string
                                            used to create an URL for this resource."""

    def __init__(self, unique_name):
        super(SubResource, self).__init__()
        self.unique_name = unique_name

    @classmethod
    def factory(cls, unique_name, path_argument_fields, *args, **kwargs):
        """Returns a Factory which the framework will use, once needed, in order to create
           this SubResource.

           :param unique_name: The unique name used to construct the URL for this SubResource.
           :param path_argument_fields: A dictionary mapping the names of arguments to the SubResource to Fields that
                                        can be used to input or output values for these arguments.
           :param args:  Extra arguments to be passed directly to the __init__ of the SubResource when created.
           :param kwargs: Extra keyword arguments to be passed directly to the __init__ of the SubResource when created.
        """
        regex_path = RegexPath(cls.get_regex(unique_name), 
                               cls.get_path_template(unique_name),
                               path_argument_fields)
        return SubResourceFactory(regex_path, functools.partial(cls.create_resource, unique_name, *args, **kwargs))

    @classmethod
    def is_for_sub_resource(cls, path, for_exact_sub_path=u'.*'):
        return re.match(u'.*/_{1,2}%s$' % for_exact_sub_path, path)

    @classmethod
    def get_full_path_for(cls, current_path, sub_path):
        if cls.is_for_sub_resource(current_path, for_exact_sub_path=sub_path):
            full_path = current_path
        else:
            delimiter = u'/_'
            if current_path.endswith(u'/'):
                delimiter = u'__'
            full_path = u'%s%s%s' % (current_path, delimiter, sub_path)
        return full_path

    @classmethod
    def get_path_template(cls, unique_name):
        return u'%s_%s' % (unique_name, cls.sub_path_template)

    @classmethod
    def get_url_for(cls, unique_name, **kwargs):
        sub_path = cls.get_path_template(unique_name) % kwargs
        context = WebExecutionContext.get_context()
        request = context.request
        url = Url.get_current_url()
        url.path = cls.get_full_path_for(url.path, sub_path)
        url.make_network_relative()
        return url

    @classmethod
    def get_regex(cls, unique_name):
        context = WebExecutionContext.get_context()
        current_path = Url.get_current_url().as_locale_relative().path
        match = re.match(u'(?P<current_view_path>.*)(?P<delimiter>/_{1,2})%s_%s$' % (unique_name, cls.sub_regex), current_path)
        if match:
            current_view_path = match.group(u'current_view_path')
            delimiter = match.group(u'delimiter')
            return u'%s%s%s_%s' % (current_view_path, delimiter, unique_name, cls.sub_regex)
        delimiter = u'/_'
        if current_path.endswith(u'/'):
            delimiter = u'__'
        return u'%s%s%s_%s' % (current_path, delimiter, unique_name, cls.sub_regex)

    @classmethod
    def parent_url_should_end_on_slash(cls, current_path):
        last_path_segment = current_path.split(u'/')[-1]
        return last_path_segment.startswith(u'__')

    @classmethod
    def get_view_path_for(cls, subresource_path):
        new_path = u'/'.join(subresource_path.split(u'/')[:-1])
        if cls.parent_url_should_end_on_slash(subresource_path):
            new_path += u'/'
        return new_path

    @classmethod
    def get_parent_url(cls): 
        request = ExecutionContext.get_context().request
        current_path = Url.get_current_url().path
        new_path = cls.get_view_path_for(current_path)
        url = Url.get_current_url()
        url.path = new_path
        return url

    def get_url(self):
        """Returns the Url that resolves to this SubResource."""
        return self.get_url_for(self.unique_name)


class MethodResult(object):
    """A :class:`RemoteMethod` can be constructed to yield its results back to a browser in different 
       ways. MethodResult is the superclass of all such different kinds of results.

       :param catch_exception: The class of Exeption to catch if thrown while the :class:`RemoteMethod` executes.
       :param content_type: The content type to use when sending this MethodResult back to a browser.
       :param charset: The charset to use when sending this MethodResult back to a browser.
    """
    def __init__(self, catch_exception=None, content_type='text/html', charset='utf-8'):
        self.catch_exception = catch_exception
        self.content_type = content_type
        self.charset = charset

    def create_response(self, return_value):
        """Override this in your subclass to create a :class:`webob.Response` for the given `return_value` which
           was returned when calling the RemoteMethod."""
        return Response(body=self.render(return_value))
    
    def create_exception_response(self, exception):
        """Override this in your subclass to create a :class:`webob.Response` for the given `exception` instance
           which happened during execution of the RemoteMethod. This method will only be called when the exception
           is raised, and only if you specified for it to be caught using `catch_exception` when this MethodResult
           was created.
        """
        return Response(body=self.render_exception(exception))

    def render(self, return_value):
        """Instead of overriding `.create_response` to customise how `return_value` will be reported, 
           this method can be overridden instead, supplying only the body of a normal 200 Response."""
        return return_value

    def render_exception(self, exception):
        """Instead of overriding `.create_exception_response` to customise how `exception` will be reported, 
           this method can be overridden instead, supplying only the body of a normal 200 Response."""
        return unicode(exception)

    def get_response(self, return_value):
        response = self.create_response(return_value)
        response.content_type = self.content_type
        response.charset = self.charset
        return response

    def get_exception_response(self, exception):
        response = self.create_exception_response(exception)
        response.content_type = self.content_type
        response.charset = self.charset
        return response

    
class RedirectAfterPost(MethodResult):
    """A MethodResult which will cause the browser to be redirected to the Url returned by the called
       RemoteMethod instead of actually returning the result for display. A RedirectAfterPost is meant to be
       used by the EventChannel only.

       :param content_type:
       :param charset:
    """
    def __init__(self, content_type='text/html', charset='utf-8'):
        super(RedirectAfterPost, self).__init__(catch_exception=DomainException, content_type=content_type, charset=charset)

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
       :param kwargs: Other keyword arguments are sent to MethodResult, see :class:`MethodResult`.
    """
    def __init__(self, result_field, **kwargs):
        super(JsonResult, self).__init__(content_type='application/json', charset='utf-8', **kwargs)
        self.fields = FieldIndex(self)
        self.fields.result = result_field
        
    def render(self, return_value):
        self.result = return_value
        return self.fields.result.as_input()

    def render_exception(self, exception):
        return u'"%s"' % unicode(exception)


class WidgetResult(MethodResult):
    """A MethodResult used to render a given Widget (`result_widget`) back to the browser in response
       to a RemoteMethod being invoked. The HTML rendered is only the contents of the `result_widget`,
       not its containing HTML element. WidgetResult is one way in which to re-render a server-side Widget
       via Ajax inside a browser without refreshing an entire page in the process.

       A JavaScript `<script>` tag is rendered also, containing the JavaScript activating code for the 
       new contents of this refreshed Widget.
    """

    def __init__(self, result_widget):
        super(WidgetResult, self).__init__(content_type='text/html', charset='utf-8', catch_exception=DomainException)
        self.result_widget = result_widget

    def render(self, return_value):
        result = self.result_widget.render_contents()
        js = set(self.result_widget.get_contents_js(context=u'#%s' % self.result_widget.css_id))
        result += u'<script type="text/javascript">' 
        result += u''.join(js)
        result += u'</script>'
        return result


class NoRedirectAfterPost(WidgetResult):
    def render_as_json(self, exception):
        rendered_widget = super(NoRedirectAfterPost, self).render(None)
        success = exception is None
        return json.dumps({ u'success': success, u'widget': rendered_widget })
    
    def render(self, return_value):
        return self.render_as_json(None)
    
    def render_exception(self, exception):
        return self.render_as_json(exception)


class RemoteMethod(SubResource): 
    """A server-side method that can be invoked from a browser via an URL. The method will return its result
       back to the browser in different ways, depending on which type of `default_result` it is constructed 
       with.

       :param name: A unique name from which the URL of this RemoteMethod will be constructed.
       :param callable_object: A callable object which will receive either the raw query arguments (if immutable),
                               or the raw POST data (if not immutable) as keyword arguments.
       :param immutable: Whether this method will yield the same side-effects and results when called more than 
                         once, or not. Immutable methods are accessible via GET method, non-immutable methods
                         via POST.
    """
    sub_regex = u'method'
    sub_path_template = u'method'

    def __init__(self, name, callable_object, default_result, immutable=False):
        super(RemoteMethod, self).__init__(name)
        self.immutable = immutable
        self.callable_object = callable_object
        self.default_result = default_result

    @property
    def name(self):
        return self.unique_name
    
    @property
    def http_methods(self):
        if self.immutable:
            return ['get']
        return ['post']

    def parse_arguments(self, input_values):
        return dict(input_values)

    def cleanup_after_exception(self, input_values, ex):
        """Override this method in a subclass to trigger custom behaviour after the method
           triggered a :class:`DomainException`."""
        pass
        
    def cleanup_after_success(self):
        """Override this method in a subclass to trigger custom behaviour after the method
           completed successfully."""
        pass

    def call_with_input(self, input_values):
        return self.callable_object(**self.parse_arguments(input_values))

    def make_result(self, input_values):
        """Override this method to be able to determine (at run time) what MethodResult to use
           for this method. The default implementation merely uses the `default_result` given
           during construction of the RemoteMethod."""
        return self.default_result

    def handle_get_or_post(self, input_values):
        result = self.make_result(input_values)
        context = ExecutionContext.get_context()
        response = None
        try:
            with context.system_control.nested_transaction():
                return_value = self.call_with_input(input_values)
                response = result.get_response(return_value)
        except result.catch_exception, ex:
            context.initialise_web_session()  # Because the rollback above nuked it
            self.cleanup_after_exception(input_values, ex)
            response = result.get_exception_response(ex)
        else:
            self.cleanup_after_success()

        return response

    def handle_post(self, request):
        return self.handle_get_or_post(request.POST)

    def handle_get(self, request):
        return self.handle_get_or_post(request.GET)


class CheckedRemoteMethod(RemoteMethod): 
    """A RemoteMethod whose input is governed by instances of :class:`Field` like input usually is.

       :param name: (See :class:`RemoteMethod`.)
       :param callable_object: (See :class:`RemoteMethod`.) Should expect a keyword argument for each key in `parameters`.
       :param result: (See :class:`RemoteMethod`.)
       :param immutable: (See :class:`RemoteMethod`.)
       :param parameters: A dictionary containing a Field for each argument name expected.
    """
    def __init__(self, name, callable_object, result, immutable=False, **parameters):
        super(CheckedRemoteMethod, self).__init__(name, callable_object, result, immutable=immutable)
        self.parameters = FieldIndex(self)
        for name, field in parameters.items():
            self.parameters.set(name, field)

    def parse_arguments(self, input_values):
        exception = None
        for name, field in self.parameters.items():
            try:
                field.from_input(input_values.get(name, u''))
            except ValidationConstraint, ex:
                exception = ex
        if exception:
            raise ValidationException()
        return self.parameters.as_kwargs()


class EventChannel(RemoteMethod):
    """A RemoteMethod used to receive Events originating from Buttons on Forms.

       Programmers should not need to work with an EventChannel directly.
    """
    def __init__(self, form, controller, name):
        super(EventChannel, self).__init__(name, self.delegate_event, None, immutable=False)
        self.controller = controller
        self.form = form

    def make_result(self, input_values):
        if u'_noredirect' in input_values.keys():
            return NoRedirectAfterPost(self.form.rendered_form)
        else:
            return RedirectAfterPost()

    def delegate_event(self, event=None):
        try:
            return self.controller.handle_event(event)
        except NoEventHandlerFound:
            raise ProgrammerError(u'No suitable handler found for event %s on %s' % (event.name, self.form.view))

    def parse_arguments(self, input_values):
        event = self.form.handle_form_input(input_values)
        return {'event': event}

    def cleanup_after_exception(self, input_values, ex):
        self.form.cleanup_after_exception(input_values, ex)

    def cleanup_after_success(self):
        self.form.cleanup_after_success()



class ComposedPage(Resource):
    def __init__(self, view, page):
        super(ComposedPage, self).__init__()
        self.view = view
        self.page = page
        
    def handle_get(self, request):
        return self.render()
        
    def render(self):
        response = Response(body=self.page.render())
        response.content_type=self.page.content_type
        response.charset=self.page.charset
        if self.view.cacheable:
            config = ExecutionContext.get_context().config
            response.cache_control=u'max-age=%s' % unicode(config.web.cache_max_age)
        else:
            response.cache_control=u'no-cache'
        return response



class FileView(View):
    def __init__(self, user_interface, viewable_file):
        super(FileView, self).__init__(user_interface)
        self.viewable_file = viewable_file

    def as_resource(self, page):
        return StaticFileResource(u'static', self.viewable_file)

    @property
    def title(self):
        return self.viewable_file.name


class ViewableFile(object):
    def __init__(self, name, content_type, encoding, size, mtime):
        self.name = name
        self.content_type = content_type
        self.encoding = encoding
        self.mtime = mtime
        self.size = size    


class FileOnDisk(ViewableFile):
    def __init__(self, full_path, relative_name):
        content_type, encoding = mimetypes.guess_type(full_path)
        self.full_path = full_path
        self.relative_name = relative_name
        size = os.path.getsize(full_path)
        mtime = os.path.getmtime(self.full_path)
        super(FileOnDisk, self).__init__(full_path, content_type or 'application/octet-stream', encoding, size, mtime)

    @contextmanager
    def open(self):
        open_file = open(self.full_path, 'rb')
        try:
            yield open_file
        finally:
            open_file.close()


class FileFromBlob(ViewableFile):
    def __init__(self, name, file_obj, content_type, encoding, size, mtime):
        super(FileFromBlob, self).__init__(name, content_type, encoding, size, mtime)
        self.file_obj = file_obj
        self.relative_name = name

    @contextmanager
    def open(self):
        self.file_obj.seek(0)
        try:
            yield self.file_obj
        finally:
            self.file_obj.seek(0)


class PackagedFile(FileOnDisk):
    def __init__(self, egg, directory_name, relative_name):
        egg_relative_name = u'/'.join([directory_name, relative_name])
        full_path = pkg_resources.resource_filename(Requirement.parse(egg), egg_relative_name)
        super(PackagedFile, self).__init__(full_path, relative_name)


class ConcatenatedFile(FileOnDisk):
    def __init__(self, relative_name, contents):
        self.temp_file = self.concatenate(relative_name, contents)
        super(ConcatenatedFile, self).__init__(self.temp_file.name, relative_name)
     
    def minifier(self, relative_name):
        class NoOpMinifier(object):
            def minify(self, input_stream, output_stream):
                for line in input_stream:
                    output_stream.write(line)
        
        class JSMinifier(object):
            def minify(self, input_stream, output_stream):
                text = StringIO.StringIO()
                for line in input_stream:
                    text.write(line)
                output_stream.write(slimit.minify(text.getvalue(), mangle=True, mangle_toplevel=True))

        class CSSMinifier(object):
            def minify(self, input_stream, output_stream):
                text = StringIO.StringIO()
                for line in input_stream:
                    text.write(line)
                output_stream.write(cssmin.cssmin(text.getvalue()))

        context = WebExecutionContext.get_context()
        if context.config.reahlsystem.debug:
            return NoOpMinifier()

        if relative_name.endswith(u'.css'):
            return CSSMinifier()
        elif relative_name.endswith(u'.js'):
            return JSMinifier()
        else:
            return NoOpMinifier()

    def create_temp_file(self, suffix):
        """Since NamedTemporaryFile does not work on windows, we need to create our own"""

        (file_handle, path) = tempfile.mkstemp(suffix=suffix)
        os.close(file_handle)
        open_file = open(path,'w+b')
        
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
        super(FileList, self).__init__(self.create_file)
        self.files = files
        
    def create_file(self, relative_path):
        path = relative_path[1:]
        for file_ in self.files:
            if file_.relative_name == path:
                return file_
        raise NoMatchingFactoryFound(relative_path)


class DiskDirectory(FileFactory):
    def __init__(self, root_path):
        super(DiskDirectory, self).__init__(self.create_file)
        self.root_path = root_path

    def create_file(self, relative_path):
        path = relative_path[1:]
        context = WebExecutionContext.get_context()
        static_root = context.config.web.static_root
        relative_path = self.root_path.split('/')+path.split('/')
        full_path = os.path.join(static_root, *relative_path)
        logging.debug('Request is for static file "%s"' % full_path)
        if os.path.isfile(full_path):
            return FileOnDisk(full_path, relative_path)
        raise NoMatchingFactoryFound(relative_path)


class FileDownload(Response):
    chunk_size = 4096
    def __init__(self, a_file):
        self.file = a_file
        super(FileDownload, self).__init__(app_iter=self, conditional_response=True)
        self.content_type = (str(self.file.content_type) if self.file.content_type else None)
        self.content_encoding = (str(self.file.encoding) if self.file.encoding else None)
        self.content_length = (str(self.file.size) if (self.file.size is not None) else None)
        self.last_modified = datetime.fromtimestamp(self.file.mtime)
        self.etag = '%s-%s-%s' % (self.file.mtime,
                                  self.file.size, 
                                  abs(hash(self.file.name)))

    def __iter__(self):
        return self.app_iter_range(start=0)
            
    def app_iter_range(self, start=None, end=None):
        length_of_file = self.file.size
        if not end or end >= length_of_file:
            end = length_of_file - 1
        if start < 0:
            start = 0
        if start >= end:
            yield ''
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
    sub_regex = u'(?P<filename>[^/]+)'
    sub_path_template = u'%(filename)s'

    def get_url(self):
        return self.get_url_for(self.unique_name, filename=self.file.name)

    def __init__(self, unique_name, a_file):
        super(StaticFileResource, self).__init__(unique_name)
        self.file = a_file

    def handle_get(self, request):
        return FileDownload(self.file)


class IdentityDictionary(object):
    """A dictionary which has values equal to whatever key is asked for. An IdentityDictionary is
       sometimes useful when mapping between Slot names, etc."""
    def __getitem__(self, x): return x


class ReahlWSGIApplication(object):
    """A web application. This class should only ever be instantiated in a WSGI script, using the `from_directory`
       method."""

    @classmethod
    def from_directory(cls, directory):
        """Create a ReahlWSGIApplication given the `directory` where its configuration is stored."""
        config = StoredConfiguration(directory, strict_validation=True)
        config.configure()
        return cls(config)

    def __init__(self, config):
        self.request_lock = threading.Lock()
        self.config = config
        self.system_control = SystemControl(self.config)
        with WebExecutionContext() as context:
            context.set_config(self.config)
            context.set_system_control(self.system_control)
            self.root_user_interface_factory = UserInterfaceFactory(None, RegexPath(u'/', u'/', {}), IdentityDictionary(), self.config.web.site_root, u'site_root')
            self.add_reahl_static_files()

    def find_packaged_files(self, labelled):
        found_files = []
        eggs_in_order = ReahlEgg.get_all_relevant_interfaces(self.config.reahlsystem.root_egg)
        for egg in eggs_in_order:
            snippets = egg.find_attachments(labelled)
            for snippet in snippets:
                found_files.append(PackagedFile(egg.distribution.project_name, os.path.dirname(snippet.filename), os.path.basename(snippet.filename)))
        return found_files

    def add_reahl_static_files(self):
        misc = [] 
        jquery = [PackagedFile(u'reahl-web', u'reahl/web/static', u'jquery/jquery-1.8.1.js')]
        jquery_plugins = [PackagedFile(u'reahl-web', u'reahl/web/static', i) for i in
                          [u'jquery/jquery.cookie-1.0.js', 
                          u'jquery/jquery.metadata-2.1.js',
                          u'jquery/jquery.validate-1.10.0.modified.js',
                          u'jquery/jquery.ba-bbq-1.2.1.js',
                          u'jquery/jquery.blockUI-2.43.js',
                          u'jquery/jquery.form-3.14.js'
                          ]]
        jquery_ui = [PackagedFile(u'reahl-web', u'reahl/web/static', 'jquery-ui-1.10.3.custom.js')]
        css_files = [PackagedFile(u'reahl-web', u'reahl/web/static', i) for i in
                     [u'reset-fonts-grids.css', u'reahl.css']] 
        css_files += self.find_packaged_files(u'css')
        js_files = self.find_packaged_files(u'js')
        reahl_jquery_ui_plugins = [PackagedFile(u'reahl-web', u'reahl/web/static', i) for i in
                                   [
                                   u'reahl.validate.js',
                                   u'reahl.modaldialog.js',
                                   ]]

        static_files = [PackagedFile(u'reahl-web', u'reahl/web/static', u'html5shiv-printshiv-3.6.3.js'),
                        PackagedFile(u'reahl-web', u'reahl/web/static', u'IE9.js'),
                        ConcatenatedFile(u'reahl.js', misc+jquery+jquery_plugins+jquery_ui+reahl_jquery_ui_plugins+js_files),
                        ConcatenatedFile(u'reahl.css', css_files)]
        static_files += self.find_packaged_files(u'any')
        self.define_static_files(u'/static', static_files)

        shipped_style_files = [PackagedFile(u'reahl-web', u'reahl/web/static/css', u'basic.css')]
        self.define_static_files(u'/styles', shipped_style_files)

    def start(self, connect=True):
        """Starts the ReahlWSGIApplication by "connecting" to the database. What "connecting" means may differ
           depending on the persistence mechanism in use. It could include enhancing classes for persistence, etc."""
        self.should_disconnect = connect
        with ExecutionContext() as context:
            context.set_config(self.config)
            context.set_system_control(self.system_control)
            if connect:
                self.system_control.connect()
        
    def stop(self):
        """Stops the ReahlWSGIApplication by "disconnecting" from the database. What "disconnecting" means may differ
           depending on the persistence mechanism in use."""
        with ExecutionContext() as context:
            context.set_config(self.config)
            context.set_system_control(self.system_control)
            if self.should_disconnect:
                self.system_control.disconnect()

    def define_static_files(self, path, files):
        ui_name = u'static_%s' % path
        ui_factory = UserInterfaceFactory(None, RegexPath(path, path, {}), IdentityDictionary(), StaticUI, ui_name, files=FileList(files))
        self.root_user_interface_factory.predefine_user_interface(ui_factory)
        return ui_factory

    def get_target_ui(self, full_path):
        root_ui = self.root_user_interface_factory.create(full_path)
        target_ui, page = root_ui.get_user_interface_for_full_path(full_path)
        return (target_ui, page)

    def resource_for(self, request):
        url = Url.get_current_url(request=request)
        logging.debug('Finding Resource for URL: %s' % url.path)
        url.make_locale_relative()
        target_ui, page_factory = self.get_target_ui(url.path)
        # TODO: FEATURE ENVY BELOW:
        logging.debug('Found UserInterface %s' % target_ui)
        current_view = target_ui.get_view_for_full_path(url.path)
        logging.debug('Found View %s' % current_view)
        current_view.check_precondition()
        current_view.check_rights(request.method)
        if current_view.is_dynamic:
            page_factory = current_view.page_factory or page_factory
            if not page_factory:
                raise ProgrammerError(u'there is no page defined for %s' % url.path)
            page = page_factory.create(current_view)
            current_view.plug_into(page)
            self.check_scheme(page.is_security_sensitive)
        else:
            page = None

        return current_view.resource_for(url.path, page)

    def check_scheme(self, security_sensitive):
        scheme_needed = self.config.web.default_http_scheme
        if security_sensitive:
            scheme_needed = self.config.web.encrypted_http_scheme

        request = WebExecutionContext.get_context().request
        if request.scheme.lower() != scheme_needed.lower():
            raise RedirectToScheme(scheme_needed)

    def create_context_for_request(self):
        return WebExecutionContext()

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

    def __call__(self, environ, start_response):
        request = Request(environ, charset='utf8')
        new_context = self.create_context_for_request()
        new_context.set_config(self.config)
        new_context.set_request(request)
        new_context.set_system_control(self.system_control)

        return new_context.handle_wsgi_call(self, environ, start_response)


@deprecated(u'ReahlWebApplication has been renamed to ReahlWSGIApplication, please use ReahlWSGIApplication instead')
class ReahlWebApplication(ReahlWSGIApplication):
    pass


