
from reahl.component.i18n import Catalogue
from reahl.web.fw import UserInterface, Url, Widget
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.navs import Nav, PillLayout

_ = Catalogue('reahl-doc')


class TranslatedUI(UserInterface):
    def assemble(self):
        self.define_view('/some_page', title=_('Translated example'), 
                                       page=HomePage.factory())

class I18nExample(Widget):
    def __init__(self, view):
        super().__init__(view)

        menu = Nav(self.view).use_layout(PillLayout()).with_languages()
        self.add_child(menu)

        current_url = Url.get_current_url()
        message = _('This is a translated message. The current URL is "%s".') % current_url.path
        self.add_child(P(view, text=message))
        
        
class HomePage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.body.add_child(I18nExample(view))








