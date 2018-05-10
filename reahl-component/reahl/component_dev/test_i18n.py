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
from threading import Timer
import datetime

import babel.dates 

from reahl.stubble import stubclass, InitMonitor, EmptyStub

from reahl.component.context import ExecutionContext
from reahl.component.i18n import Catalogue, SystemWideCatalogue
from reahl.component.config import Configuration, ConfigSetting


@stubclass(ExecutionContext)
class LocaleContextStub(ExecutionContext):
    test_locale = 'af'
    @property
    def interface_locale(self):
        return self.test_locale


def test_basic_usage():
    """A Catalogue for a particular component can translate messages for that component into
       the interface_locale on its current ExecutionContext."""


    _ = Catalogue('reahl-component')  # Will find its translations in the compiled messages of reahl-component

    context = LocaleContextStub().install()

    context.test_locale = 'en_gb'
    assert _('test string') == 'test string'
    assert _.gettext('test string') == 'test string'
    assert _.ngettext('thing', 'things', 1) == 'thing'
    assert _.ngettext('thing', 'things', 3) == 'things'

    context.test_locale = 'af'
    assert _('test string') == 'toets string'
    assert _.gettext('test string') == 'toets string'
    assert _.ngettext('thing', 'things', 1) == 'ding'
    assert _.ngettext('thing', 'things', 3) == 'goeters'


def test_formatting():
    """A Catalogue can be used to easily obtain the current locale for use
       by other i18n tools."""

    _ = Catalogue('reahl-component')

    date = datetime.date(2012, 1, 10)

    context = LocaleContextStub().install()

    context.test_locale = 'en_gb'
    assert _.current_locale == 'en_gb'
    actual = babel.dates.format_date(date, format='long', locale=_.current_locale)
    assert actual == '10 January 2012'

    context.test_locale = 'af'
    assert _.current_locale == 'af'
    actual = babel.dates.format_date(date, format='long', locale=_.current_locale)
    assert actual == '10 Januarie 2012'


def test_translator_singleton():
    """Only one SystemWideCatalogue is ever present per process."""

    SystemWideCatalogue.instance = None  # To "reset" the singleton, else its __init__ will NEVER be called in this test

    with InitMonitor(SystemWideCatalogue) as monitor:
        _ = Catalogue('reahl-component')
        _2 = Catalogue('reahl-component')

        context = LocaleContextStub().install()

        _('test string')
        _.ngettext('thing', 'things', 1)
        _.ngettext('thing', 'things', 2)

        _2('test string')

    assert monitor.times_called == 1


def test_translator_singleton_thread_safety():
    """The SystemWideCatalogue.get_instance() is this thread-safe."""
    SystemWideCatalogue.instance = None  # To "reset" the singleton, else its __init__ will NEVER be called in this test
    SystemWideCatalogue.get_instance().map_lock.acquire()
    saved_state = EmptyStub()
    saved_state.lock_released = False
    def release_lock():
        SystemWideCatalogue.get_instance().map_lock.release()
        saved_state.lock_released = True
    timer = Timer(.1, release_lock)
    timer.start()
    context = LocaleContextStub().install()
    _ = Catalogue('reahl-component')
    _.gettext('test string')
    timer.cancel()
    assert saved_state.lock_released


def test_translated_config():
    """Configuration can be translated by adding a duplicate setting for each additional locale."""

    class MyConfig(Configuration):
        setting = ConfigSetting(default='the default')

    config = MyConfig()

    context = LocaleContextStub().install()

    context.test_locale = 'en_gb'
    assert config.setting == 'the default'

    context.test_locale = 'af'
    assert config.setting == 'the default'

    config.setting_af = 'die verstek'
    assert config.setting == 'die verstek'

