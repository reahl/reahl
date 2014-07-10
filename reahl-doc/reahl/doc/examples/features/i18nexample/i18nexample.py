
from __future__ import unicode_literals
from __future__ import print_function
from reahl.web.fw import UserInterface, Url, UserInterface
from reahl.web.ui import HMenu
from reahl.web.ui import P
from reahl.web.ui import TwoColumnPage
from reahl.component.i18n import Translator

_ = Translator('reahl-doc')


class TranslatedUI(UserInterface):
    def assemble(self):
        self.define_view('/some_page', title=_('Translated example'), page=HomePage.factory())


class HomePage(TwoColumnPage):
    def __init__(self, view):
        super(HomePage, self).__init__(view, style='basic')

        self.header.add_child(HMenu.from_languages(view))

        current_url = Url.get_current_url()
        message = _('This is a translated string. The current URL is "%s".') % current_url.path
        self.main.add_child(P(view, text=message))








