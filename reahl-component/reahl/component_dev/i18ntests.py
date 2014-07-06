# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import unicode_literals
from __future__ import print_function
from threading import Timer
import datetime

import babel.dates 

from nose.tools import istest
from reahl.tofu import  test, Fixture
from reahl.stubble import stubclass, InitMonitor
from reahl.tofu import vassert

from reahl.component.context import ExecutionContext
from reahl.component.i18n import Translator, SystemWideTranslator
from reahl.component.config import Configuration, ConfigSetting

@stubclass(ExecutionContext)
class LocaleContextStub(ExecutionContext):
    test_locale = 'af'
    @property
    def interface_locale(self):
        return self.test_locale

@istest
class I18nTests(object):
    @test(Fixture)
    def basic_usage(self, fixture):
        """A Translator for a particular component can translate messages for that component into
           the interface_locale on its current ExecutionContext."""
        
            
        _ = Translator('reahl-component')  # Will find its translations in the compiled messages of reahl-component

        with LocaleContextStub() as context:
            context.test_locale = 'en_gb'
            vassert( _('test string') == 'test string' )
            vassert( _.gettext('test string') == 'test string' )
            vassert( _.ngettext('thing', 'things', 1) == 'thing' )
            vassert( _.ngettext('thing', 'things', 3) == 'things' )

            context.test_locale = 'af'
            vassert( _('test string') == 'toets string' )
            vassert( _.gettext('test string') == 'toets string' )
            vassert( _.ngettext('thing', 'things', 1) == 'ding' )
            vassert( _.ngettext('thing', 'things', 3) == 'goeters' )

    @test(Fixture)
    def formatting(self, fixture):
        """A Translator can be used to easily obtain the current locale for use
           by other i18n tools."""
            
        _ = Translator('reahl-component') 

        date = datetime.date(2012, 1, 10)

        with LocaleContextStub() as context:
            context.test_locale = 'en_gb'
            vassert( _.current_locale == 'en_gb' )
            actual = babel.dates.format_date(date, format='long', locale=_.current_locale)
            vassert( actual == '10 January 2012' )

            context.test_locale = 'af'
            vassert( _.current_locale == 'af' )
            actual = babel.dates.format_date(date, format='long', locale=_.current_locale)
            vassert( actual == '10 Januarie 2012' )


    @test(Fixture)
    def translator_singleton(self, fixture):
        """Only one SystemwideTranslator is ever present per process."""

        SystemWideTranslator.instance = None  # To "reset" the singleton, else its __init__ will NEVER be called in this test

        with InitMonitor(SystemWideTranslator) as monitor:
            _ = Translator('reahl-component')
            _2 = Translator('reahl-component')
            
            _('test string')
            _.ngettext('thing', 'things', 1) 
            _.ngettext('thing', 'things', 2) 

            _2('test string')
            
        vassert( monitor.times_called == 1 )

    @test(Fixture)
    def translator_singleton_thread_safety(self, fixture):
        """The SystemwideTranslator.get_instance() is this thread-safe."""
        SystemWideTranslator.instance = None  # To "reset" the singleton, else its __init__ will NEVER be called in this test
        SystemWideTranslator.get_instance().map_lock.acquire()
        self.lock_released = False
        def release_lock():
            SystemWideTranslator.get_instance().map_lock.release()
            self.lock_released = True
        timer = Timer(.1, release_lock)
        timer.start()
        _ = Translator('reahl-component')
        _.gettext('test string')
        timer.cancel()
        vassert( self.lock_released )

    @test(Fixture)
    def translated_config(self, fixture):
        """Configuration can be translated by adding a duplicate setting for each additional locale."""

        class MyConfig(Configuration):
            setting = ConfigSetting(default='the default')
            
        config = MyConfig()
        
        with LocaleContextStub() as context:
            context.test_locale = 'en_gb'
            vassert( config.setting == 'the default' )

            context.test_locale = 'af'
            vassert( config.setting == 'the default' )

            config.setting_af = 'die verstek'
            vassert( config.setting == 'die verstek' )
