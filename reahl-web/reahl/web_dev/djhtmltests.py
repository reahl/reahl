# Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
#-*- encoding: utf-8 -*-
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


from nose.tools import istest
from reahl.tofu import Fixture, test, set_up
from reahl.tofu import vassert, temp_dir
from reahl.stubble import stubclass, replaced

from reahl.web.djhtml import DjhtmlRegion
from reahl.web.fw import WebExecutionContext, Region
from reahl.web.ui import Slot, TwoColumnPage
from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.webdev.tools import Browser

class DjhtmlFixture(Fixture, WebBasicsMixin):
    def new_static_dir(self):
        return temp_dir()
    
    div_internals = u'<p>some stúff</p>'

    def new_djhtml_file(self):
        contents = u'<!DOCTYPE html><meta charset="UTF-8"><html><head><title>â title</title></head>' \
                   u'<body><div id="astatic">%s</div></body></html>' % self.div_internals
        return self.static_dir.file_with(u'correctfile.d.html', contents.encode('utf-8'))

    def new_afrikaans_djhtml_file(self):
        contents = u'<!DOCTYPE html><meta charset="UTF-8"><html><head><title>Afrikaans bo!</title></head><body></body></html>'
        return self.static_dir.file_with(u'correctfile.af.d.html', contents.encode('utf-8'))

    def new_other_file(self):
        return self.static_dir.file_with(u'otherfile.txt', u'other')

    @set_up
    def create_files(self):
        self.djhtml_file
        self.afrikaans_djhtml_file
        self.other_file


@istest
class BasicTests(object):
    @test(DjhtmlFixture)
    def basic_workings(self, fixture):
        """A DjhtmlRegion provides a Region which maps to the filesystem where there may be
           a combination of .d.html and other files. When a d.html file is requested from
           it, the contents of the specified div from inside the d.html file is inserted 
           into the specified Slot. When a normal file is requested, the file is sent verbatim."""
        
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/djhtml_region', DjhtmlRegion, {u'main_slot': u'main'},
                                name=u'test_region', static_div_name=u'astatic')

        # Djhtml files should be located in the web.static_root
        fixture.config.web.static_root = fixture.static_dir.name

        webapp = fixture.new_webapp(site_root=MainRegion, enable_js=True)
        browser = Browser(webapp)

        # A djhtml file: TwoColumnPage's main_slot now contains the insides of the div in the djhtml file
        browser.open(u'/djhtml_region/correctfile.d.html')
        html = browser.get_html_for(u'//div[@id="bd"]/div/div/*')
        vassert( html == fixture.div_internals )

        # A non-djhtml file is returned verbatim
        browser.open(u'/djhtml_region/otherfile.txt')
        contents = browser.raw_html
        vassert( contents == u'other' )

        # Files that do not exist are reported as such
        browser.open(u'/djhtml_region/idonotexist.txt', status=404)
        browser.open(u'/djhtml_region/idonotexist.d.html', status=404)

    @test(DjhtmlFixture)
    def i18n_djhtml(self, fixture):
        """Djhtml files can have i18nsed versions, which would be served up if applicable."""

        @stubclass(WebExecutionContext)
        class AfrikaansContext(WebExecutionContext):
            @property
            def interface_locale(self):
                return u'af'

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/djhtml_region', DjhtmlRegion, {u'main_slot': u'main'},
                                   name=u'test_region', static_div_name=u'astatic')

        # Djhtml files should be located in the web.static_root
        fixture.config.web.static_root = fixture.static_dir.name

        webapp = fixture.new_webapp(site_root=MainRegion)
            
        browser = Browser(webapp)

        # request the file, but get the transalated alternative for the locale
        def stubbed_create_context_for_request():
            return AfrikaansContext()
        with replaced(webapp.create_context_for_request, stubbed_create_context_for_request):
            browser.open(u'/djhtml_region/correctfile.d.html')
            
        vassert( browser.title == u'Afrikaans bo!' )


