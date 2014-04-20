
from reahl.web.fw import UserInterface, Url, UserInterface
from reahl.web.ui import TwoColumnPage, P, Panel, HMenu
from reahl.component.i18n import Translator

_ = Translator(u'reahl-doc')


class TranslatedUI(UserInterface):
    def assemble(self):
        self.define_view(u'/some_page', title=_(u'Translated example'), page=HomePage.factory())


class HomePage(TwoColumnPage):
    def __init__(self, view):
        super(HomePage, self).__init__(view, style=u'basic')

        self.header.add_child(HMenu.from_languages(view))

        current_url = Url.get_current_url()
        message = _(u'This is a translated string. The current URL is "%s".') % current_url.path
        self.main.add_child(P(view, text=message))








