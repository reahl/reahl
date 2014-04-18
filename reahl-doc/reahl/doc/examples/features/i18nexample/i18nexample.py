
from reahl.web.fw import UserInterface, Url, UserInterface
from reahl.web.ui import TwoColumnPage, P, Panel, HMenu
from reahl.component.i18n import Translator

_ = Translator(u'reahl-doc')


class SomeContents(Panel):
    def __init__(self, view):
        super(SomeContents, self).__init__(view)

        self.add_child(HMenu.from_languages(view))

        current_url = Url.get_current_url()
        message = _(u'This is a translated string. The current URL is "%s".') % current_url.path
        self.add_child(P(view, text=message))


class TranslatedUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style=u'basic')
        
        home = self.define_view(u'/some_page', title=_(u'Translated example'))
        home.set_slot(u'main', SomeContents.factory())





