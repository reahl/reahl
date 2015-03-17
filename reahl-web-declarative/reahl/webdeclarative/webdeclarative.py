# Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import print_function, unicode_literals, absolute_import, division
import six
import random
from six.moves.urllib import parse as urllib_parse
from datetime import datetime, timedelta



from sqlalchemy import Column, Integer, BigInteger, LargeBinary, PickleType, String, UnicodeText, ForeignKey, DateTime
from sqlalchemy.orm import relationship, deferred, backref
#from sqlalchemy import Column, Integer, ForeignKey, UnicodeText, String, DateTime, Boolean


from reahl.sqlalchemysupport import Session, Base
from reahl.component.eggs import ReahlEgg
from reahl.component.config import Configuration
from reahl.component.context import ExecutionContext
from reahl.component.migration import Migration
from reahl.component.decorators import deprecated
from reahl.web.interfaces import UserSessionProtocol, UserInputProtocol, PersistedExceptionProtocol, PersistedFileProtocol
from reahl.web.fw import WebExecutionContext, Url

class InvalidKeyException(Exception):
    pass

class UserSession(Base, UserSessionProtocol):
    """An implementation of :class:`reahl.web.interfaces.UserSessionProtocol` of the Reahl framework."""

    __tablename__ = 'usersession'

    id = Column(Integer, primary_key=True)
    discriminator = Column('row_type', String(40))
    __mapper_args__ = {'polymorphic_on': discriminator}

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

    def __init__(self, **kwargs):
        self.generate_salt()
        self.last_activity = datetime.fromordinal(1)
        self.set_idle_lifetime(False)
        super(UserSession, self).__init__(**kwargs)

    @deprecated('Please use LoginSession.is_logged_in(secured=True) instead.', '3.1')
    def is_secure(self):
        from reahl.systemaccountmodel import LoginSession
        return LoginSession.for_current_session().is_logged_in(secured=True)

    def is_secured(self):
        context = WebExecutionContext.get_context()
        return self.is_within_timeout(context.config.web.idle_secure_lifetime) \
               and context.request.scheme == 'https' \
               and self.secure_cookie_is_valid()

    @deprecated('Please use LoginSession.is_logged_in instead.', '3.1')
    def is_logged_in(self):
        from reahl.systemaccountmodel import LoginSession
        return LoginSession.for_current_session().is_logged_in()
        
    def is_active(self):
        return self.is_within_timeout(self.idle_lifetime)

    def is_within_timeout(self, timeout):
        return self.last_activity + timedelta(seconds=timeout) > datetime.now()

    def set_last_activity_time(self):
        self.last_activity = datetime.now()

    def set_idle_lifetime(self, use_max):
        config = WebExecutionContext.get_context().config
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
        return '%s:%s' % (six.text_type(self.id), self.salt)

    def secure_cookie_is_valid(self):
        context = WebExecutionContext.get_context()
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
        context = WebExecutionContext.get_context()
        try:
            raw_cookie = context.request.cookies[context.config.web.session_key_name]
            return urllib_parse.unquote(raw_cookie)
        except KeyError:
            return None

    def set_session_key(self, response):
        context = WebExecutionContext.get_context()
        session_cookie = self.as_key()
        response.set_cookie(context.config.web.session_key_name, urllib_parse.quote(session_cookie), path='/')
        if self.is_secured():
            response.set_cookie(context.config.web.secure_key_name, urllib_parse.quote(self.secure_salt), secure=True, path='/',
                                max_age=context.config.web.idle_secure_lifetime)

    def generate_salt(self):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZqwertyuiopasdfghjklzxcvbnm0123456789'
        self.salt = ''.join([random.choice(alphabet) for x in list(range(40))])
        self.secure_salt = ''.join([random.choice(alphabet) for x in list(range(40))])        

    def get_interface_locale(self):
        context = WebExecutionContext.get_context()
        if not hasattr(context, 'request'):
            return 'en_gb'

        request = context.request
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
    __mapper_args__ = {'polymorphic_on': discriminator}
    
    web_session_id = Column(Integer, ForeignKey('usersession.id', ondelete='CASCADE'), index=True)
    web_session = relationship(UserSession)

    ui_name = Column(UnicodeText, nullable=False)
    channel_name = Column(UnicodeText, nullable=False)

    @classmethod
    def clear_for_form(cls, form):
        for stale in cls.for_form(form).all():
            Session.delete(stale)

    @classmethod
    def for_form(cls, form):
        web_session = WebExecutionContext.get_context().session
        return Session.query(cls).filter_by(web_session=web_session, ui_name=form.user_interface.name, channel_name=form.channel_name)
    
    @classmethod
    def new_for_form(cls, form, **kwargs):
        web_session = WebExecutionContext.get_context().session
        instance = cls(web_session=web_session, ui_name=form.user_interface.name, channel_name=form.channel_name, **kwargs)
        Session.add(instance)
        return instance

    __hash__ = None
    def __eq__(self, other):
        return self.web_session == other.web_session and \
               self.ui_name == other.ui_name and \
               self.channel_name == other.channel_name

    def __neq__(self, other):
        return not self.__eq__(other)


class UserInput(SessionData, UserInputProtocol):
    """An implementation of :class:`reahl.web.interfaces.UserInputProtocol`. It represents
       an value that was input by a user."""
    __tablename__ = 'userinput'
    __mapper_args__ = {'polymorphic_identity': 'userinput'}
    id = Column(Integer, ForeignKey('sessiondata.id', ondelete='CASCADE'), primary_key=True)

    key = Column(UnicodeText, nullable=False)
    value = Column(UnicodeText, nullable=False)

    __hash__ = None
    def __eq__(self, other):
        return super(UserInput, self).__eq__(other) and \
               self.key == other.key and \
               self.value == other.value

    @classmethod
    def get_previously_entered_for_form(cls, form, input_name):
        query = cls.for_form(form).filter_by(key=input_name)
        if query.count() > 0:
            return query.one().value
        else:
            return None

    @classmethod
    def save_input_value_for_form(cls, form, input_name, value):
        assert isinstance(value, six.text_type)
        cls.new_for_form(form, key=input_name, value=value)


class PersistedException(SessionData, PersistedExceptionProtocol):
    """An implementation of :class:`reahl.web.interfaces.PersistedExceptionProtocol`. It represents
       an Exception that was raised upon a user interaction."""
    __tablename__ = 'persistedexception'
    __mapper_args__ = {'polymorphic_identity': 'persistedexception'}
    id = Column(Integer, ForeignKey('sessiondata.id', ondelete='CASCADE'), primary_key=True)

    exception = Column(PickleType, nullable=False)
    input_name = Column(UnicodeText)

    def __eq__(self, other):
        return super(PersistedException, self).__eq__(other) and \
               self.exception == other.exception

    @classmethod
    def for_form(cls, form):
        return cls.for_input(form, None)

    @classmethod
    def for_input(cls, form, input_name):
        return super(PersistedException, cls).for_form(form).filter_by(input_name=input_name)

    @classmethod
    def clear_for_all_inputs(cls, form):
        for e in super(PersistedException, cls).for_form(form).filter(cls.input_name != None):
            Session.delete(e)

    @classmethod
    def get_exception_for_form(cls, form):
        persisted = cls.for_form(form)
        if persisted.count() == 1:
            return persisted.one().exception
        return None

    @classmethod
    def get_exception_for_input(cls, form, input_name):
        persisted = cls.for_input(form, input_name)
        if persisted.count() == 1:
            return persisted.one().exception
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
        return super(PersistedFile, self).__eq__(other) and \
               self.filename == other.filename and \
               self.input_name == other.input_name

    @property
    def file_obj(self):
        class LazyFileObj(object):
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
        query = cls.for_form(form).filter_by(input_name=input_name)
        return query.all()

    @classmethod
    def add_persisted_for_form(cls, form, input_name, uploaded_file):
        filename = uploaded_file.filename
        file_data = uploaded_file.contents
        mime_type = uploaded_file.mime_type
        size = uploaded_file.size
        cls.new_for_form(form, input_name=input_name, filename=filename, file_data=file_data, mime_type=mime_type, size=size)

    @classmethod
    def remove_persisted_for_form(cls, form, input_name, filename):
        persisted = cls.for_form(form).filter_by(input_name=input_name).filter_by(filename=filename)
        for persisted_file in persisted.all():
            Session.delete(persisted_file)

    @classmethod
    def is_uploaded_for_form(cls, form, input_name, filename):
        return PersistedFile.for_form(form).filter_by(input_name=input_name).filter_by(filename=filename).count() == 1
    

class WebDeclarativeConfig(Configuration):
    filename = 'web.webdeclarative.config.py'
    config_key = 'web.webdeclarative'

    def do_injections(self, config):
        config.web.session_class = UserSession
        config.web.persisted_exception_class = PersistedException
        config.web.persisted_userinput_class = UserInput
        config.web.persisted_file_class = PersistedFile


