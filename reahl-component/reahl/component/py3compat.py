# Copyright 2014, 2016, 2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import six


def ascii_as_bytes_or_str(unicode_str):
    if six.PY2:
        return unicode_str.encode('ascii')
    else:
        return unicode_str


def _html_escape_function():
    if six.PY2:
        import xml.sax.saxutils
        def html_escape(s, quote=True):
            entities = {'"': '&quot;', '\'': '&#x27;'} if quote else {}
            return xml.sax.saxutils.escape(s, entities=entities)
        return html_escape
    else:
        import html
        return html.escape


html_escape = _html_escape_function()
