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

"""Am implementation of Reahl using SqlAlchemy Declarative.

Run 'reahl componentinfo reahl-web-declarative' for configuration information.

"""

import random
import hmac
import hashlib
import urllib.parse
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, BigInteger, LargeBinary, PickleType, String, UnicodeText, ForeignKey, DateTime
from sqlalchemy.orm import relationship, deferred
from sqlalchemy import event
from sqlalchemy.inspection import inspect

from reahl.sqlalchemysupport import Session, Base
from reahl.component.eggs import ReahlEgg
from reahl.component.config import Configuration
from reahl.component.context import ExecutionContext
from reahl.web.interfaces import UserSessionProtocol, UserInputProtocol, PersistedExceptionProtocol, PersistedFileProtocol
from reahl.web.csrf import CSRFToken
from reahl.web.fw import Url

class InvalidKeyException(Exception):
    pass

class UserSession(Base, UserSessionProtocol):
    """An implementation of :class:`reahl.web.interfaces.UserSessionProtocol` of the Reahl framework."""

    __tablename__ = 'usersession'

    id = Column(Integer, primary_key=True)
    discriminator = Column('row_type', String(40))
    __mapper_args__ = {
        'polymorphic_identity':'usersession',
        'polymorphic_on': discriminator}

    idle_lifetime = Column(Integer(), nullable=False, default=0)
    last_activity = Column(DateTime(), nullable=False, default=datetime.now)

    salt = Column(String(40), nullable=False)
    secure_salt = Column(String(40), nullable=False)

    @classmethod
    def remove_dead_sessions(cls, now=None):
        now = now or datetime.now()
        if now.minute > 0 and now.minute < 5:
            config = ExecutionContext.get_context().config
            cutoff = now - timedelta(seconds=config.web.session_lifetime)
            Session.query(cls).filter(cls.last_activity <= cutoff).delete()

    @classmethod
    def for_current_session(cls):
        return ExecutionContext.get_context().session

    @classmethod
    def initialise_web_session_on(cls, context):
        context.session = cls.get_or_create_session()

    @classmethod
    def preserve_session(cls, session):
        Session.expunge(session)

    @classmethod
    def restore_session(cls, session):
        Session.add(session)

    def __init__(self, **kwargs):
        self.generate_salt()
        self.last_activity = datetime.fromordinal(1)
        self.set_idle_lifetime(False)
        super().__init__(**kwargs)

    def get_csrf_token(self):
        key = ExecutionContext.get_context().config.web.csrf_key
        message = self.as_key()
        return CSRFToken(value=hmac.new(key.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha1).hexdigest())

    def is_secured(self):
        context = ExecutionContext.get_context()
        return self.is_within_timeout(context.config.web.idle_secure_lifetime) \
               and context.request.scheme == 'https' \
               and self.secure_cookie_is_valid()

    def is_active(self):
        return self.is_within_timeout(self.idle_lifetime)

    def is_within_timeout(self, timeout):
        return self.last_activity + timedelta(seconds=timeout) > datetime.now()

    def set_last_activity_time(self):
        self.last_activity = datetime.now()

    def set_idle_lifetime(self, use_max):
        config = ExecutionContext.get_context().config
        self.idle_lifetime = config.web.idle_lifetime_max if use_max else config.web.idle_lifetime

    @classmethod
    def from_key(cls, key):
        try:
            web_session_id, salt = key.split(':')
        except ValueError:
            raise InvalidKeyException()
        sessions = Session.query(cls).filter_by(id=web_session_id)
        if sessions.count() == 1 and sessions.one().salt == salt:
            return sessions.one()
        raise InvalidKeyException()

    def as_key(self):
        Session.flush() # To make sure .id is populated
        return '%s:%s' % (str(self.id), self.salt)

    def secure_cookie_is_valid(self):
        context = ExecutionContext.get_context()
        try:
            salt = context.request.cookies[context.config.web.secure_key_name]
            return self.secure_salt == salt
        except KeyError:
            return False

    @classmethod
    def get_or_create_session(cls):
        web_session = None
        session_key = cls.get_session_key()
        if session_key:
            try:
                web_session = cls.from_key(session_key)
            except InvalidKeyException:
                pass

        if not web_session:
            web_session = cls()
            Session.add(web_session)

        return web_session

    @classmethod
    def get_session_key(cls):
        context = ExecutionContext.get_context()
        try:
            raw_cookie = context.request.cookies[context.config.web.session_key_name]
            return urllib.parse.unquote(raw_cookie)
        except KeyError:
            return None

    def set_session_key(self, response):
        context = ExecutionContext.get_context()
        session_cookie = self.as_key()
        response.set_cookie(context.config.web.session_key_name, urllib.parse.quote(session_cookie), path='/', samesite='Strict')
        if self.is_secured():
            response.set_cookie(context.config.web.secure_key_name, urllib.parse.quote(self.secure_salt), secure=True, path='/',
                                max_age=context.config.web.idle_secure_lifetime, samesite='Strict')

    def generate_salt(self):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZqwertyuiopasdfghjklzxcvbnm0123456789'
        self.salt = ''.join([random.choice(alphabet) for x in list(range(40))])
        self.secure_salt = ''.join([random.choice(alphabet) for x in list(range(40))])        

    def get_interface_locale(self):
        context = ExecutionContext.get_context()
        if not hasattr(context, 'request'):
            return 'en_gb'

        url = Url.get_current_url()
        possible_locale, path = url.get_locale_split_path()
        supported_locales = ReahlEgg.get_languages_supported_by_all(context.config.reahlsystem.root_egg)
        if possible_locale:
            if possible_locale in supported_locales:
                return possible_locale
        return context.config.web.default_url_locale


class SessionData(Base):
    __tablename__ = 'sessiondata'

    id = Column(Integer, primary_key=True)
    discriminator = Column('row_type', String(40))
    __mapper_args__ = {
        'polymorphic_identity': 'sessiondata',
        'polymorphic_on': discriminator}
    
    web_session_id = Column(Integer, ForeignKey('usersession.id', ondelete='CASCADE'), index=True)
    web_session = relationship(UserSession)

    view_path = Column(UnicodeText, nullable=False)
    ui_name = Column(UnicodeText, nullable=False)
    channel_name = Column(UnicodeText, nullable=True)

    @classmethod
    def clear_for_form(cls, form):
        for stale in cls.find_for_cached(form.view, form=form):
            cls.delete_cached(form.view, stale)

    @classmethod
    def clear_for_view(cls, view):
        for stale in cls.find_for_cached(view, form=None):
            cls.delete_cached(view, stale)

    @classmethod
    def clear_all_view_data(cls, view):
        web_session = ExecutionContext.get_context().session
        items = Session.query(cls).filter_by(web_session=web_session, view_path=view.full_path, ui_name=view.user_interface.name)
        for stale in items:
            cls.delete_cached(view, stale)

    @classmethod
    def find_all_cached(cls, view):
        if view.cached_session_data is None:

            @event.listens_for(Session(), 'after_soft_rollback')
            def clear_cache(session, previous_transaction):
                view.cached_session_data = None

            web_session = ExecutionContext.get_context().session
            query = Session.query(SessionData).filter_by(web_session=web_session, view_path=view.full_path, ui_name=view.user_interface.name)
            view.cached_session_data = query.all()

        return [i for i in view.cached_session_data if isinstance(i, cls)]


    @classmethod
    def find_for_cached(cls, view, form=None):
        assert (not form) or (form.view is view)
        channel_name = form.channel_name if form else None
        return [i for i in cls.find_all_cached(view) if i.channel_name == channel_name]

    @classmethod
    def save_for_cached(cls, view, form=None, **kwargs):
        assert (not form) or (form.view is view)
        channel_name = form.channel_name if form else None
        web_session = ExecutionContext.get_context().session
        instance = cls(web_session=web_session, view_path=view.full_path, ui_name=view.user_interface.name, channel_name=channel_name, **kwargs)
        Session.add(instance)
        view.cached_session_data.append(instance)
        return instance

    @classmethod
    def delete_cached(cls, view, instance):
        if inspect(instance).persistent:
            Session.delete(instance)
        view.cached_session_data.remove(instance)

    __hash__ = None
    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.web_session == other.web_session and \
               self.ui_name == other.ui_name and \
               self.channel_name == other.channel_name

    def __neq__(self, other):
        return not self.__eq__(other)


class UserInput(SessionData, UserInputProtocol):
    """An implementation of :class:`reahl.web.interfaces.UserInputProtocol`. It represents
       a value that was input by a user."""
    __tablename__ = 'userinput'
    __mapper_args__ = {'polymorphic_identity': 'userinput'}
    id = Column(Integer, ForeignKey('sessiondata.id', ondelete='CASCADE'), primary_key=True)

    key = Column(UnicodeText, nullable=False)
    value = Column(UnicodeText, nullable=True)

    __hash__ = None
    def __eq__(self, other):
        return super().__eq__(other) and \
               self.key == other.key and \
               self.value == other.value

    @classmethod
    def get_previously_entered_for_form(cls, form, input_name, entered_input_type):
        return cls.get_previously_saved_for(form.view, form, input_name, entered_input_type)

    @classmethod
    def get_previously_saved_for(cls, view, form, key, value_type):
        values = [i.value for i in cls.find_for_cached(view, form=form) if i.key == key]
        if not values:
            return None

        if value_type is str:
            assert len(values) == 1, 'There are %s saved values for "%s", but there should only be one' % (len(values), key)
            return values[0]
        elif value_type is list:
            if len(values) == 1 and values[0] is None:
                return []
            return values
        else:
            assert None, 'Cannot persist values of type: %s' % value_type

    @classmethod
    def save_input_value_for_form(cls, form, input_name, value, entered_input_type):
        cls.save_value_for(form.view, form, input_name, value, entered_input_type)

    @classmethod
    def save_value_for(cls, view, form, key, value, value_type):
        for i in [e for e in cls.find_for_cached(view, form=form) if e.key == key]:
            cls.delete_cached(view, i)

        if value_type is str:
            assert isinstance(value, str), 'Cannot handle the value: ' + str(value)
            cls.save_for_cached(view, form=form, key=key, value=value)
        elif value_type is list:
            assert all([isinstance(i, str) for i in value]), 'Cannot handle the value: ' + str(value)
            if value:
                for i in value:
                    cls.save_for_cached(view, form=form, key=key, value=i)
            else:
                cls.save_for_cached(view, form=form, key=key, value=None)
        else:
            assert None, 'Cannot persist values of type: %s' % value_type

    @classmethod
    def get_persisted_for_view(cls, view, key, value_type):
        return cls.get_previously_saved_for(view, None, key, value_type)

    @classmethod
    def add_persisted_for_view(cls, view, key, value, value_type):
        cls.save_value_for(view, None, key, value, value_type)

    @classmethod
    def remove_persisted_for_view(cls, view, key):
        for previous in [i for i in cls.find_for_cached(view, form=None) if i.key == key]:
            cls.delete_cached(view, previous)

class PersistedException(SessionData, PersistedExceptionProtocol):
    """An implementation of :class:`reahl.web.interfaces.PersistedExceptionProtocol`. It represents
       an Exception that was raised upon a user interaction."""
    __tablename__ = 'persistedexception'
    __mapper_args__ = {'polymorphic_identity': 'persistedexception'}
    id = Column(Integer, ForeignKey('sessiondata.id', ondelete='CASCADE'), primary_key=True)

    exception = Column(PickleType, nullable=False)
    input_name = Column(UnicodeText)

    def __eq__(self, other):
        return super().__eq__(other) and \
               self.exception == other.exception

    @classmethod
    def save_exception_for_form(cls, form, **kwargs):
        return cls.save_for_cached(form.view, form=form, **kwargs)

    @classmethod
    def for_input(cls, form, input_name):
        return [i for i in super().find_for_cached(form.view, form=form) if i.input_name == input_name]

    @classmethod
    def clear_for_form_except_inputs(cls, form):
        for stale in cls.for_input(form, None):
            cls.delete_cached(form.view, stale)

    @classmethod
    def clear_for_all_inputs(cls, form):
        for e in [i for i in super().find_for_cached(form.view, form=form) if i.input_name is not None]:
            cls.delete_cached(form.view, e)

    @classmethod
    def get_exception_for_form(cls, form):
        persisted = cls.for_input(form, None)
        if len(persisted) == 1:
            return persisted[0].exception
        return None

    @classmethod
    def get_exception_for_input(cls, form, input_name):
        persisted = cls.for_input(form, input_name)
        if len(persisted) == 1:
            return persisted[0].exception
        return None


class PersistedFile(SessionData, PersistedFileProtocol):
    """An implementation of :class:`reahl.web.interfaces.PersistedFileProtocol`. It represents
       a file that was input by a user."""
    __tablename__ = 'persistedfile'
    __mapper_args__ = {'polymorphic_identity': 'persistedfile'}
    id = Column(Integer, ForeignKey('sessiondata.id', ondelete='CASCADE'), primary_key=True)

    input_name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText, nullable=False)
    file_data = deferred(Column(LargeBinary, nullable=False)) 
    mime_type = Column(UnicodeText, nullable=False)
    size = Column(BigInteger, nullable=False)

    def __eq__(self, other):
        return super().__eq__(other) and \
               self.filename == other.filename and \
               self.input_name == other.input_name

    @property
    def file_obj(self):
        class LazyFileObj:
            def __init__(self, persisted_file):
                self.persisted_file = persisted_file
                self.position = 0
            def read(self):
                try:
                    return self.persisted_file.file_data[self.position:]
                finally:
                    self.position = len(self.persisted_file.file_data)-1
            def seek(self, position):
                self.position = position
        return LazyFileObj(self)

    @classmethod
    def get_persisted_for_form(cls, form, input_name):
        return [i for i in cls.find_for_cached(form.view, form=form) if i.input_name == input_name]

    @classmethod
    def add_persisted_for_form(cls, form, input_name, uploaded_file):
        filename = uploaded_file.filename
        file_data = uploaded_file.contents
        mime_type = uploaded_file.mime_type
        size = uploaded_file.size
        return cls.save_for_cached(form.view, form=form, input_name=input_name, filename=filename, file_data=file_data,
                                   mime_type=mime_type, size=size)

    @classmethod
    def remove_persisted_for_form(cls, form, input_name, filename):
        persisted = [i for i in cls.find_for_cached(form.view, form=form) if i.input_name == input_name and i.filename == filename]
        for persisted_file in persisted:
            cls.delete_cached(form.view, persisted_file)

    @classmethod
    def is_uploaded_for_form(cls, form, input_name, filename):
        return len([i for i in PersistedFile.find_for_cached(form.view, form=form) if i.input_name == input_name and i.filename == filename]) == 1
    

class WebDeclarativeConfig(Configuration):
    filename = 'web.webdeclarative.config.py'
    config_key = 'web.webdeclarative'

    def do_injections(self, config):
        config.web.session_class = UserSession
        config.web.persisted_exception_class = PersistedException
        config.web.persisted_userinput_class = UserInput
        config.web.persisted_file_class = PersistedFile


