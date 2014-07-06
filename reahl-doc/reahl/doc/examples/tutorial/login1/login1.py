


from __future__ import unicode_literals
from __future__ import print_function
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup, HMenu,\
                         PasswordInput, ErrorFeedbackMessage
from reahl.systemaccountmodel import AccountManagementInterface, UserSession



class MenuPage(TwoColumnPage):
    def __init__(self, view, main_bookmarks):
        super(MenuPage, self).__init__(view, style='basic')
        self.header.add_child(HMenu.from_bookmarks(view, main_bookmarks))


class LoginForm(Form):
    def __init__(self, view):
        super(LoginForm, self).__init__(view, 'login')
        
        accounts = AccountManagementInterface.for_current_session()

        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))

        self.add_child(LabelledBlockInput(TextInput(self, accounts.fields.email)))
        self.add_child(LabelledBlockInput(PasswordInput(self, accounts.fields.password)))

        self.define_event_handler(accounts.events.login_event)
        self.add_child(Button(self, accounts.events.login_event))


class LoginUI(UserInterface):
    def assemble(self):
        user_session = UserSession.for_current_session()
        if user_session.account:
            logged_in_as = user_session.account.email
        else:
            logged_in_as = 'Guest'

        home = self.define_view('/', title='Home')
        home.set_slot('main', P.factory(text='Welcome %s' % logged_in_as))

        login_page = self.define_view('/login', title='Log in')
        login_page.set_slot('main', LoginForm.factory())
        
        bookmarks = [i.as_bookmark(self) for i in [home, login_page]]
        self.define_page(MenuPage, bookmarks)



