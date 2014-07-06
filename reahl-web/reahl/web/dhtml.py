# Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""

Static pages that are included on the fly inside Views.
"""
from __future__ import unicode_literals
from __future__ import print_function

import os.path
from six.moves import html_parser
import logging

from BeautifulSoup import BeautifulSoup, SoupStrainer

from reahl.component.modelinterface import Field
from reahl.component.exceptions import ProgrammerError
from reahl.component.i18n import Translator
from reahl.web.fw import WebExecutionContext, Bookmark, UrlBoundView, NoView, \
                         FileOnDisk, UserInterface, FileView, NoMatchingFactoryFound, CannotCreate
from reahl.web.ui import LiteralHTML

_ = Translator('reahl-web')

class DJHTMLWidget(LiteralHTML):
    def __init__(self, view, html_content):
        super(DJHTMLWidget, self).__init__(view, html_content)


class DhtmlUI(UserInterface):
    """A UserInterface which serves content from the static directory configured in `web.staticroot`.
       If a given Url maps directly to a file in this directory, that file is normally served
       as-is. If the filename ends on .d.html, however, the file is parsed, and the div inside it
       with id equal to `static_div_name` is read into the `main_slot` of a View. The
       title of the current View is also taken from the <title> of the static page.
       
       :param static_div_name: The id of the <div> to insert as `main_slot` of this UserInterface.
    """
    def assemble(self, static_div_name=None):
        self.static_div_name = static_div_name
        self.define_regex_view('(?P<file_path>.*)', '${file_path}', factory_method=self.create_view, file_path=Field())

    def is_dynamic(self, filename):
        return filename.endswith('.d.html') and os.path.exists(filename)

    def is_static(self, filename):
        return os.path.isfile(filename) and not filename.endswith('.d.html')

    def filesystem_path(self, relative_path):
        context = WebExecutionContext.get_context()
        static_root = context.config.web.static_root
        if relative_path.endswith('/'):
           relative_path += 'index.d.html'
        return self.i18nise_filename(os.path.join(static_root, *relative_path.split('/')))

    def i18nise_filename(self, for_default_locale):
        current_locale = WebExecutionContext.get_context().interface_locale
        head, tail = os.path.splitext(for_default_locale)
        head, d = os.path.splitext(head)
        for_current_locale = head+'.%s' % current_locale+d+tail
        if os.path.isfile(for_current_locale):
            return for_current_locale
        return for_default_locale

    def statics(self, relative_path):
        statics = {}
        with open(self.filesystem_path(relative_path)) as dhtml_file:
            def strain(name, attrs):
                if name == 'title':
                    return True
                if name == 'div' and dict(attrs).get('id', None) == self.static_div_name:
                    return True
                return False
            soup = BeautifulSoup(dhtml_file, parseOnlyThese=SoupStrainer(strain))
            parser = html_parser.HTMLParser()
            statics['title'] = parser.unescape(soup.title.renderContents()) if soup.title else _('Untitled')
            statics['div'] = soup.div.renderContents() if soup.div else ''
        return statics
    
    def create_view(self, relative_path, user_interface, file_path=None):
        if not user_interface is self:
            raise ProgrammerError('get_file called on %s with %s as user_interface' % (self, user_interface))
        file_url_path = file_path
        filename = self.filesystem_path(file_url_path)
        logging.debug('Finding a static file on filesystem %s' % filename)
        if self.is_dynamic(filename):
            statics = self.statics(file_url_path)
            slot_contents = {'main_slot': DJHTMLWidget.factory(statics['div'])}
            return UrlBoundView(user_interface, file_url_path, statics['title'], slot_contents, cacheable=True)
        elif self.is_static(filename):
            return FileView(user_interface, FileOnDisk(filename, file_url_path))
        raise CannotCreate()


        

