


from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup, Menu, HorizontalLayout,\
                         PasswordInput, ErrorFeedbackMessage
from reahl.web.pure import PageColumnLayout, UnitSize
from reahl.domain.systemaccountmodel import AccountManagementInterface, LoginSession



class MenuPage(HTML5Page):
    def __init__(self, view, main_bookmarks):
        super(MenuPage, self).__init__(view, style='basic')
        self.use_layout(PageColumnLayout(('main', UnitSize('1/3'))))
        self.layout.header.add_child(Menu.from_bookmarks(view, main_bookmarks).use_layout(HorizontalLayout()))


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
        login_session = LoginSession.for_current_session()
        if login_session.account:
            logged_in_as = login_session.account.email
        else:
            logged_in_as = 'Guest'

        home = self.define_view('/', title='Home')
        home.set_slot('main', P.factory(text='Welcome %s' % logged_in_as))

        login_page = self.define_view('/login', title='Log in')
        login_page.set_slot('main', LoginForm.factory())
        
        bookmarks = [i.as_bookmark(self) for i in [home, login_page]]
        self.define_page(MenuPage, bookmarks)



