


from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.navs import Nav, TabLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.domain.systemaccountmodel import LoginSession
from reahl.domainui.bootstrap.accounts import AccountUI



class MenuPage(HTML5Page):
    def __init__(self, view, main_bookmarks):
        super().__init__(view)
        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', size=ResponsiveSize(md=4))).with_slots()
        self.layout.contents.use_layout(contents_layout)
        self.layout.header.add_child(Nav(view).use_layout(TabLayout()).with_bookmarks(main_bookmarks))


class LegalNotice(P):
    def __init__(self, view, text, name):
        super().__init__(view, text=text, css_id=name)
        self.set_as_security_sensitive()


class LoginUI(UserInterface):
    def assemble(self):
        login_session = LoginSession.for_current_session()
        if login_session.account:
            logged_in_as = login_session.account.email
        else:
            logged_in_as = 'Guest'

        home = self.define_view('/', title='Home')
        home.set_slot('main', P.factory(text='Welcome %s' % logged_in_as))

        terms_of_service = self.define_view('/terms_of_service', title='Terms of service')
        terms_of_service.set_slot('main', LegalNotice.factory('The terms of services defined as ...', 'terms'))

        privacy_policy = self.define_view('/privacy_policy', title='Privacy policy')
        privacy_policy.set_slot('main', LegalNotice.factory('You have the right to remain silent ...', 'privacypolicy'))

        disclaimer = self.define_view('/disclaimer', title='Disclaimer')
        disclaimer.set_slot('main', LegalNotice.factory('Disclaim ourselves from negligence ...', 'disclaimer'))

        class LegalBookmarks:
            terms_bookmark = terms_of_service.as_bookmark(self)
            privacy_bookmark = privacy_policy.as_bookmark(self)
            disclaimer_bookmark = disclaimer.as_bookmark(self)

        accounts = self.define_user_interface('/accounts', AccountUI,
                                      {'main_slot': 'main'},
                                      name='accounts', bookmarks=LegalBookmarks)

        account_bookmarks = [accounts.get_bookmark(relative_path=relative_path) 
                             for relative_path in ['/login', '/register', '/registerHelp', '/verify']]
        bookmarks = [home.as_bookmark(self)]+account_bookmarks
        self.define_page(MenuPage, bookmarks)






