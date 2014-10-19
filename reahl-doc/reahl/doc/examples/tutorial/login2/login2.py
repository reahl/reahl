


from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, P, HMenu
from reahl.domain.systemaccountmodel import LoginSession
from reahl.domainui.accounts import AccountUI



class MenuPage(TwoColumnPage):
    def __init__(self, view, main_bookmarks):
        super(MenuPage, self).__init__(view, style='basic')
        self.header.add_child(HMenu.from_bookmarks(view, main_bookmarks))


class LoginUI(UserInterface):
    def assemble(self):
        login_session = LoginSession.for_current_session()
        if login_session.account:
            logged_in_as = login_session.account.email
        else:
            logged_in_as = 'Guest'

        home = self.define_view('/', title='Home')
        home.set_slot('main', P.factory(text='Welcome %s' % logged_in_as))

        class LegalBookmarks(object):
            terms_bookmark = home.as_bookmark(self, description='Terms of service')
            privacy_bookmark = home.as_bookmark(self, description='Privacy policy')
            disclaimer_bookmark = home.as_bookmark(self, description='Disclaimer')

        accounts = self.define_user_interface('/accounts', AccountUI,
                                      {'main_slot': 'main'},
                                      name='accounts', bookmarks=LegalBookmarks)

        account_bookmarks = [accounts.get_bookmark(relative_path=relative_path) 
                             for relative_path in ['/login', '/register']]
        bookmarks = [home.as_bookmark(self)]+account_bookmarks
        self.define_page(MenuPage, bookmarks)



