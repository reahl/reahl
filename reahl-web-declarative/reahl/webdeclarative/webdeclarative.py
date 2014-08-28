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


from __future__ import unicode_literals
from __future__ import print_function
import six
import random
from abc import ABCMeta
from six.moves.urllib import parse as urllib_parse


from sqlalchemy import Column, Integer, BigInteger, LargeBinary, PickleType, String, UnicodeText, ForeignKey
from sqlalchemy.orm import relationship, deferred, backref
from sqlalchemy.ext.declarative import DeclarativeMeta

from reahl.sqlalchemysupport import Session, Base
from reahl.component.eggs import ReahlEgg
from reahl.component.config import Configuration
from reahl.component.migration import Migration
from reahl.web.interfaces import WebUserSessionProtocol, UserInputProtocol, PersistedExceptionProtocol, PersistedFileProtocol
from reahl.domain.systemaccountmodel import UserSession
from reahl.web.fw import WebExecutionContext, Url


class InvalidKeyException(Exception):
    pass
    
class WebUserSession(six.with_metaclass(UserSession.__metaclass__, UserSession, WebUserSessionProtocol)):
    __tablename__ = 'webusersession'
    __mapper_args__ = {'polymorphic_identity': 'webusersession'}
    id = Column(Integer, ForeignKey('usersession.id', ondelete='CASCADE'), primary_key=True)

    salt = Column(String(40), nullable=False)
    secure_salt = Column(String(40), nullable=False)

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

    def is_secure(self):
        context = WebExecutionContext.get_context()
        return super(WebUserSession, self).is_secure() \
               and context.request.scheme == 'https' \
               and self.secure_cookie_is_valid()

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
        session_cookie = self.as_key().encode('utf-8')
        response.set_cookie(context.config.web.session_key_name, urllib_parse.quote(session_cookie), path='/')
        if self.is_secure():
            response.set_cookie(context.config.web.secure_key_name, urllib_parse.quote(self.secure_salt), secure=True, path='/',
                                max_age=context.config.accounts.idle_secure_lifetime)

    def __init__(self, **kwargs):
        self.generate_salt()
        super(WebUserSession, self).__init__(**kwargs)

    def generate_salt(self):
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZqwertyuiopasdfghjklzxcvbnm0123456789'
        self.salt = ''.join([random.choice(alphabet) for x in list(range(40))])
        self.secure_salt = ''.join([random.choice(alphabet) for x in list(range(40))])        

    def get_interface_locale(self):
        context = WebExecutionContext.get_context()
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
    
    web_session_id = Column(Integer, ForeignKey('webusersession.id', ondelete='CASCADE'), index=True)
    web_session = relationship(WebUserSession)

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


class UserInputMeta(DeclarativeMeta, ABCMeta): pass
class UserInput(six.with_metaclass(UserInputMeta, SessionData, UserInputProtocol)):
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


class PersistedExceptionMeta(DeclarativeMeta, ABCMeta): pass
class PersistedException(six.with_metaclass(PersistedExceptionMeta, SessionData, PersistedExceptionProtocol)):
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


class PersistedFileMeta(DeclarativeMeta, ABCMeta): pass
class PersistedFile(six.with_metaclass(PersistedFileMeta, SessionData, PersistedFileProtocol)):
    __tablename__ = 'persistedfile'
    __mapper_args__ = {'polymorphic_identity': 'persistedfile'}
    id = Column(Integer, ForeignKey('sessiondata.id', ondelete='CASCADE'), primary_key=True)

    input_name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText, nullable=False)
    file_data = deferred(Column(LargeBinary, nullable=False)) 
    content_type = Column(UnicodeText, nullable=False)
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
        file_data = uploaded_file.file_obj.read()
        content_type = uploaded_file.content_type
        size = uploaded_file.size
        cls.new_for_form(form, input_name=input_name, filename=filename, file_data=file_data, content_type=content_type, size=size)

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
        config.web.session_class = WebUserSession
        config.web.persisted_exception_class = PersistedException
        config.web.persisted_userinput_class = UserInput
        config.web.persisted_file_class = PersistedFile


