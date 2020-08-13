



from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.forms import Form, TextInput, Button, FormLayout, PasswordInput
from reahl.web.bootstrap.navs import Nav, TabLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.domain.systemaccountmodel import AccountManagementInterface, LoginSession



class MenuPage(HTML5Page):
    def __init__(self, view, main_bookmarks):
        super().__init__(view)
        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', size=ResponsiveSize(md=4))).with_slots()
        self.layout.contents.use_layout(contents_layout)
        self.layout.header.add_child(Nav(view).use_layout(TabLayout()).with_bookmarks(main_bookmarks))


class LoginForm(Form):
    def __init__(self, view):
        super().__init__(view, 'login')
        self.use_layout(FormLayout())
        accounts = AccountManagementInterface.for_current_session()

        if self.exception:
            self.layout.add_alert_for_domain_exception(self.exception)

        self.layout.add_input(TextInput(self, accounts.fields.email))
        self.layout.add_input(PasswordInput(self, accounts.fields.password))

        self.define_event_handler(accounts.events.login_event)
        self.add_child(Button(self, accounts.events.login_event, style='primary'))


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






