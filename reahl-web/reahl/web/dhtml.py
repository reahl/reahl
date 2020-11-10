# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import os.path
import io
import html.parser
import logging

from bs4 import BeautifulSoup, SoupStrainer

from reahl.component.modelinterface import Field
from reahl.component.exceptions import ProgrammerError
from reahl.component.i18n import Catalogue
from reahl.component.context import ExecutionContext
from reahl.web.fw import UrlBoundView, FileOnDisk, UserInterface, FileView, CannotCreate
from reahl.web.ui import LiteralHTML

_ = Catalogue('reahl-web')

class DJHTMLWidget(LiteralHTML):
    def __init__(self, view, html_content):
        super().__init__(view, html_content)

class DHTMLFile:
    def __init__(self, filename, ids):
        self.filename = filename
        self.ids = ids
        self.elements = {}
        self.title = None
        self.orignal_encoding = None
        
    def read(self):
        with io.open(self.filename, 'rb') as dhtml_file:
            def strain(name, attrs):
                if name == 'title':
                    return True
                if name == 'div' and dict(attrs).get('id', None) in self.ids:
                    return True
                return False
            soup = BeautifulSoup(dhtml_file, "lxml", parse_only=SoupStrainer(strain))
            self.title = html.unescape(soup.title.decode_contents()) if soup.title else _('Untitled')
            for an_id in self.ids:
                found_elements = soup.find_all(id=an_id)
                if found_elements:
                    number_of_ids = len(found_elements)
                    if number_of_ids != 1:
                        raise ProgrammerError('Expected to find one element with id "%s", but found %s' % (an_id, number_of_ids))
                    [element] = found_elements
                    self.elements[an_id] = element.decode_contents()
                else:
                    self.elements[an_id] = ''
            self.original_encoding = soup.original_encoding


class DhtmlUI(UserInterface):
    """A UserInterface which serves content from the static directory configured in `web.staticroot`.
       If a given Url maps directly to a file in this directory, that file is normally served
       as-is. If the filename ends on .d.html, however, the file is parsed, and the div inside it
       with id equal to `static_div_name` is read into the `main_slot` of a View. The
       title of the current View is also taken from the <title> of the static page.
       
       :keyword static_div_name: The id of the <div> to insert as `main_slot` of this UserInterface.
    """
    def assemble(self, static_div_name=None):
        self.static_div_name = static_div_name
        self.define_regex_view('(?P<file_path>.*)', '${file_path}', factory_method=self.create_view, file_path=Field())

    def is_dynamic(self, filename):
        return filename.endswith('.d.html') and os.path.exists(filename)

    def is_static(self, filename):
        return os.path.isfile(filename) and not filename.endswith('.d.html')

    def filesystem_path(self, relative_path):
        context = ExecutionContext.get_context()
        static_root = context.config.web.static_root
        if relative_path.endswith('/'):
           relative_path += 'index.d.html'
        return self.i18nise_filename(os.path.join(static_root, *relative_path.split('/')))

    def i18nise_filename(self, for_default_locale):
        current_locale = ExecutionContext.get_context().interface_locale
        head, tail = os.path.splitext(for_default_locale)
        head, d = os.path.splitext(head)
        for_current_locale = head+'.%s' % current_locale+d+tail
        if os.path.isfile(for_current_locale):
            return for_current_locale
        return for_default_locale

    def statics(self, relative_path):
        dhtml_file = DHTMLFile(self.filesystem_path(relative_path), [self.static_div_name])
        dhtml_file.read()
        statics = dict()
        statics['title'] = dhtml_file.title
        statics['div'] = dhtml_file.elements[self.static_div_name]
        return statics
    
    def create_view(self, relative_path, user_interface, file_path=None):
        if not user_interface is self:
            raise ProgrammerError('get_file called on %s with %s as user_interface' % (self, user_interface))
        file_url_path = file_path
        filename = self.filesystem_path(file_url_path)
        logging.debug('Finding a static file on filesystem %s' % filename)
        if self.is_dynamic(filename):
            statics = self.statics(file_url_path)
            view = UrlBoundView(user_interface, file_url_path, statics['title'], cacheable=True)
            view.set_slot('main_slot', DJHTMLWidget.factory(statics['div']))
            return view
        elif self.is_static(filename):
            return FileView(user_interface, FileOnDisk(filename, file_url_path))
        raise CannotCreate()


        

