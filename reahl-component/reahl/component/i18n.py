# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals, absolute_import, division
import gettext
import threading


from babel.support import Translations

from reahl.component.context import ExecutionContext
from reahl.component.config import ReahlSystemConfig


class SystemWideCatalogue(object):
    instance = None
    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = SystemWideCatalogue()
        return cls.instance

    def __init__(self):
        self.translations = {}
        self.map_lock = threading.Lock()

    def get_translation_for(self, locale, domain):
        translation = self.translations.get((locale, domain), None)
        if not translation:
            with self.map_lock:
                for package in ReahlSystemConfig().translation_packages:
                    for locale_dir in package.__path__:
                        if not isinstance(translation, Translations):
                            translation = Translations.load(dirname=locale_dir, locales=[locale], domain=domain)
                            # Babel 1.3 bug under Python 3: files is a filter object, not a list like in Python 2
                            translation.files = list(translation.files)
                        else:
                            translation.merge(Translations.load(dirname=locale_dir, locales=[locale], domain=domain))
                self.translations[(locale, domain)] = translation
        return translation or gettext.NullTranslations()

    @property
    def current_locale(self):
        return ExecutionContext.get_context().interface_locale

    def dgettext(self, domain, message):
        return self.get_translation_for(self.current_locale, domain).ugettext(message)

    def dngettext(self, domain, message_singular, message_plural, n):
        return self.get_translation_for(self.current_locale, domain).ungettext(message_singular, message_plural, n)


class Catalogue(object):
    """Create an instance of this class at the top of your module, in module scope and assign it to the name `_` for
       use in translating literal strings to the language of the current locale.

       .. note:: Don't ever `.call` an instance of Catalogue in module scope. It only works once the locale is known.
       
       :param domain: A name identifying which translation catalogue use with this Catalogue. Always set this
                      to the name of the component where the code resides where this Catalogue instance is instantiated.

       .. versionchanged:: 4.0
          Renamed to Catalogue (previously Translator)
    """
    def __init__(self, domain):
        self.domain = domain

    def __call__(self, message):
        """Returns a six.text_type literal containing a translation of `message` to the correct language according to the current locale.
        """
        return self.gettext(message)

    def gettext(self, message):
        """Returns a six.text_type literal containing a translation of `message` to the correct language according to the current locale.
        """
        return SystemWideCatalogue.get_instance().dgettext(self.domain, message)

    def ngettext(self, message_singular, message_plural, n):
        """Returns a six.text_type literal containing a translation of the given messages in the correct plural (or singular) 
           form of the target language for `n` items.
        """
        return SystemWideCatalogue.get_instance().dngettext(self.domain, message_singular, message_plural, n)

    @property
    def current_locale(self):
        """Returns a string identifying the current locale to be used for the interface."""
        return SystemWideCatalogue.get_instance().current_locale

