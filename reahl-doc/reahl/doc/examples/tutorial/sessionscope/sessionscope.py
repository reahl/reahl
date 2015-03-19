
from __future__ import print_function, unicode_literals, absolute_import, division
import hashlib

from sqlalchemy import Column, ForeignKey, Integer, UnicodeText, String
from sqlalchemy.orm import relationship

from reahl.sqlalchemysupport import Session, Base, session_scoped

from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup, Menu,\
                         HorizontalLayout, PasswordInput, ErrorFeedbackMessage
from reahl.web.pure import PageColumnLayout, UnitSize
from reahl.component.modelinterface import Action
from reahl.component.modelinterface import EmailField
from reahl.component.modelinterface import Event
from reahl.component.modelinterface import PasswordField
from reahl.component.modelinterface import exposed



class User(Base):
    __tablename__ = 'sessionscope_user'
    
    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText, nullable=False) 
    name          = Column(UnicodeText, nullable=False)
    password_md5  = Column(String, nullable=False)

    def set_password(self, password):
        self.password_md5 = self.password_hash(password)
        
    def matches_password(self, password):
        return self.password_md5 == self.password_hash(password)

    def password_hash(self, password):
        return hashlib.md5(password.encode('utf-8')).hexdigest()


@session_scoped
class LoginSession(Base):
    __tablename__ = 'sessionscope_loginsession'

    id              = Column(Integer, primary_key=True)
    current_user_id = Column(Integer, ForeignKey(User.id))
    current_user    = relationship(User)
    email_address   = Column(UnicodeText)

    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email', required=True)
        fields.password = PasswordField(label='Password', required=True)

    @exposed
    def events(self, events):
        events.log_in = Event(label='Log in', action=Action(self.log_in))

    def log_in(self):
        user = Session.query(User).filter_by(email_address=self.email_address).one()
        if user.matches_password(self.password):
            self.current_user = user
        else:
            raise InvalidPassword()



class MenuPage(HTML5Page):
    def __init__(self, view, main_bookmarks):
        super(MenuPage, self).__init__(view, style='basic')
        self.use_layout(PageColumnLayout(('main', UnitSize('1/2'))))
        self.layout.header.add_child(Menu.from_bookmarks(view, main_bookmarks).use_layout(HorizontalLayout()))


class InvalidPassword(DomainException):
    def as_user_message(self):
        return 'The email/password given do not match.'
    


class LoginForm(Form):
    def __init__(self, view, login_session):
        super(LoginForm, self).__init__(view, 'login')
        
        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))

        self.add_child(LabelledBlockInput(TextInput(self, login_session.fields.email_address)))
        self.add_child(LabelledBlockInput(PasswordInput(self, login_session.fields.password)))

        self.define_event_handler(login_session.events.log_in)
        self.add_child(Button(self, login_session.events.log_in))


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



