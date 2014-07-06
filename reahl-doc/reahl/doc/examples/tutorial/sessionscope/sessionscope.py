from __future__ import unicode_literals
from __future__ import print_function
import hashlib

import elixir

from reahl.sqlalchemysupport import Session, metadata
from reahl.elixirsupport import session_scoped

from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup, HMenu,\
                         PasswordInput, ErrorFeedbackMessage
from reahl.component.modelinterface import Action
from reahl.component.modelinterface import EmailField
from reahl.component.modelinterface import Event
from reahl.component.modelinterface import PasswordField
from reahl.component.modelinterface import exposed



class User(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    
    email_address = elixir.Field(elixir.UnicodeText, required=True)
    name          = elixir.Field(elixir.UnicodeText, required=True)
    password_md5  = elixir.Field(elixir.String, required=True)

    def set_password(self, password):
        self.password_md5 = hashlib.md5(password).hexdigest()
        
    def matches_password(self, password):
        return self.password_md5 == hashlib.md5(password).hexdigest()


@session_scoped
class LoginSession(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata, tablename='tutorial_loginsession')

    current_user = elixir.ManyToOne(User)
    email_address = elixir.Field(elixir.UnicodeText)

    @exposed
    def fields(self, fields):
        fields.email_address = EmailField(label='Email', required=True)
        fields.password = PasswordField(label='Password', required=True)

    @exposed
    def events(self, events):
        events.log_in = Event(label='Log in', action=Action(self.log_in))

    def log_in(self):
        user = User.query.filter_by(email_address=self.email_address).one()
        if user.matches_password(self.password):
            self.current_user = user
        else:
            raise InvalidPassword()



class MenuPage(TwoColumnPage):
    def __init__(self, view, main_bookmarks):
        super(MenuPage, self).__init__(view, style='basic')
        self.header.add_child(HMenu.from_bookmarks(view, main_bookmarks))


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



