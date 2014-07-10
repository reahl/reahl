# Copyright 2009, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Tools for handling ReStructured Text."""

from __future__ import unicode_literals
from __future__ import print_function
import docutils.io
import docutils.core


class RestructuredText(object):
    """A chunk of ReStructured Text.
    
       :param rst_text: A string containing the actual restructured text represented by this instance.
    """
    def __init__(self, rst_text):
        self.rst_text = rst_text
        
    def as_HTML_fragment(self, header_start=3, report_level=6, halt_level=4):
        """Returns this RestructuredText formatted as an HTML fragment.
        
           :param header_start: The n of the top-level <hn> for top-level heading in this text.
           :param report_level: Reports ReST error messages at or higher than this level.
           :param halt_level:   Error messages above this level result in exceptions.
        """
        settings = {'initial_header_level': header_start,
                    'report_level': report_level,
                    'halt_level': halt_level}

        output, pub = docutils.core.publish_programmatically(
            source_class=docutils.io.StringInput, source=self.rst_text, source_path=None,
            destination_class=docutils.io.StringOutput,
            destination=None, destination_path=None,
            reader=None, reader_name='standalone',
            parser=None, parser_name='restructuredtext',
            writer=None, writer_name='html',
            settings=None, settings_spec=None,
            settings_overrides=settings,
            config_section=None,
            enable_exit_status=None)
        return pub.writer.parts['fragment']


