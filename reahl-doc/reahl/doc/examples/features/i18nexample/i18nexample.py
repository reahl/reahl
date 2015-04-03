from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface, Url, UserInterface
from reahl.web.ui import Menu, HorizontalLayout, P, HTML5Page
from reahl.component.i18n import Translator

_ = Translator('reahl-doc')


class TranslatedUI(UserInterface):
    def assemble(self):
        self.define_view('/some_page', title=_('Translated example'), 
                                       page=HomePage.factory())


class HomePage(HTML5Page):
    def __init__(self, view):
        super(HomePage, self).__init__(view, style='basic')

        menu = Menu.from_languages(view).use_layout(HorizontalLayout())
        self.body.add_child(menu)

        current_url = Url.get_current_url()
        message = _('This is a translated string. The current URL is "%s".') \
                    % current_url.path
        self.body.add_child(P(view, text=message))








