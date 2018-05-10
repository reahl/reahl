
from __future__ import print_function, unicode_literals, absolute_import, division


from passlib.hash import pbkdf2_sha256

from sqlalchemy import Column, ForeignKey, Integer, Unicode, UnicodeText, String
from sqlalchemy.orm import relationship

from reahl.sqlalchemysupport import Session, Base, session_scoped

from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.ui import HTML5Page, P, Alert
from reahl.web.bootstrap.forms import Form, TextInput, Button, PasswordInput, ButtonLayout, FormLayout
from reahl.web.bootstrap.navs import Nav, TabLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.component.modelinterface import Action, EmailField, Event, PasswordField, exposed


class User(Base):
    __tablename__ = 'sesscope_user'
    
    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText, nullable=False) 
    name          = Column(UnicodeText, nullable=False)
    password_hash = Column(Unicode(1024), nullable=False)

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)
        
    def matches_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)


@session_scoped
class LoginSession(Base):
    __tablename__ = 'sessscope_loginsession'

    id              = Column(Integer, primary_key=True)
    current_user_id = Column(Integer, ForeignKey(User.id))
    current_user    = relationship(User)

    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email', required=True)
        fields.password = PasswordField(label='Password', required=True)

    @exposed
    def events(self, events):
        events.log_in = Event(label='Log in', action=Action(self.log_in))

    def log_in(self):
        matching_users = Session.query(User).filter_by(email_address=self.email_address)
        if matching_users.count() != 1:
            raise InvalidPassword()

        user = matching_users.one()
        if user.matches_password(self.password):
            self.current_user = user
        else:
            raise InvalidPassword()



class MenuPage(HTML5Page):
    def __init__(self, view, main_bookmarks):
        super(MenuPage, self).__init__(view)
        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', size=ResponsiveSize())).with_slots()
        self.layout.contents.use_layout(contents_layout)
        self.layout.header.add_child(Nav(view).use_layout(TabLayout()).with_bookmarks(main_bookmarks))


class InvalidPassword(DomainException):
    def as_user_message(self):
        return 'The email/password given do not match.'
    


class LoginForm(Form):
    def __init__(self, view, login_session):
        super(LoginForm, self).__init__(view, 'login')
        self.use_layout(FormLayout())
        if self.exception:
            self.add_child(Alert(view, self.exception.as_user_message(), 'warning'))

        self.layout.add_input(TextInput(self, login_session.fields.email_address))
        self.layout.add_input(PasswordInput(self, login_session.fields.password))

        self.define_event_handler(login_session.events.log_in)
        btn = self.add_child(Button(self, login_session.events.log_in))
        btn.use_layout(ButtonLayout(style='primary'))


class SessionScopeUI(UserInterface):
    def assemble(self):
        login_session = LoginSession.for_current_session()
        if login_session.current_user:
            user_name = login_session.current_user.name
        else:
            user_name = 'Guest'

        home = self.define_view('/', title='Home')
        home.set_slot('main', P.factory(text='Welcome %s' % user_name))

       
        login_page = self.define_view('/login', title='Log in')
        login_page.set_slot('main', LoginForm.factory(login_session))
        
        bookmarks = [i.as_bookmark(self) for i in [home, login_page]]
        self.define_page(MenuPage, bookmarks)






