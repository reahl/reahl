# Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
# -*- encoding: utf-8 -*-
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

from reahl.web.libraries import Library

class ReahlAttic(Library):
    def __init__(self):
        super(ReahlAttic, self).__init__('reahlattic')
        self.shipped_in_directory = '/reahl/web/attic'
        self.files = ['reahl.labelledinput.css',
                        'reahl.labeloverinput.css',
                        'reahl.menu.css',
                        'reahl.hmenu.css',
                        'reahl.slidingpanel.css',
                        'reahl.cueinput.js',
                        'reahl.labeloverinput.js',
                        'reahl.fileuploadli.js',
                        'reahl.fileuploadpanel.js',
                        'reahl.popupa.js',
                        'reahl.slidingpanel.js',
                      ]