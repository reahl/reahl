


from reahl.web.fw import Region
from reahl.web.ui import TwoColumnPage, P, HMenu
from reahl.webelixirimpl import WebUserSession
from reahl.domainui.accounts import AccountRegion



class MenuPage(TwoColumnPage):
    def __init__(self, view, main_bookmarks):
        super(MenuPage, self).__init__(view, style=u'basic')
        self.header.add_child(HMenu.from_bookmarks(view, main_bookmarks))


class LoginApp(Region):
    def assemble(self):
        user_session = WebUserSession.for_current_session()
        if user_session.account:
            logged_in_as = user_session.account.email
        else:
            logged_in_as = u'Guest'

        home = self.define_view(u'/', title=u'Home')
        home.set_slot(u'main', P.factory(text=u'Welcome %s' % logged_in_as))

        class LegalBookmarks(object):
            terms_bookmark = home.as_bookmark(self, description=u'Terms of service')
            privacy_bookmark = home.as_bookmark(self, description=u'Privacy policy')
            disclaimer_bookmark = home.as_bookmark(self, description=u'Disclaimer')

        accounts = self.define_region(u'/accounts', AccountRegion,
                                      {u'main_slot': u'main'},
                                      name=u'accounts', bookmarks=LegalBookmarks)

        account_bookmarks = [accounts.get_bookmark(relative_path=relative_path) 
                             for relative_path in [u'/login', u'/register']]
        bookmarks = [home.as_bookmark(self)]+account_bookmarks
        self.define_main_window(MenuPage, bookmarks)



