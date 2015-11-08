# Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from nose.tools import istest
from reahl.tofu import  test, Fixture, vassert
from reahl.stubble import easter_egg

from pkg_resources import EntryPoint

from reahl.component.eggs import ReahlEgg, EntryPointKeyEncodedAttachmentName

@istest
class AttachmentTests(object):
    @test(Fixture)
    def attachment_basics(self, fixture):
        easter_egg.clear()

        # Attachments are discovered from specially encoded entry point keys (that include ordering and path information)
        # from the the reahl.attachments.<label> entry point
        line = '3-Asome+file+path = reahl'
        easter_egg.add_entry_point_from_line('reahl.attachments.js', line)
        line = '0-Bsome+first+path = reahl'
        easter_egg.add_entry_point_from_line('reahl.attachments.js', line)

        # The attachments are found in the correct order and are decoded
        found_attachments = ReahlEgg(easter_egg).find_attachments('js')
        filenames = [i.filename for i in found_attachments]
        vassert( filenames == ['Bsome/first/path', 'Asome/file/path'] )

    @test(Fixture)
    def our_encoding_is_parsable_by_entry_points(self, fixture):
        encoded_key = EntryPointKeyEncodedAttachmentName(path='my/path to-a/file.py', order=42).as_encoded_key()
        entry_point_source = '%s = reahl' % encoded_key

        entry_point = EntryPoint.parse(entry_point_source)

        vassert( entry_point.name == encoded_key )
        vassert( entry_point.module_name == 'reahl' )

    @test(Fixture)
    def encoding_attachment_names(self, fixture):
        entry_point_name = EntryPointKeyEncodedAttachmentName(path='my/path to-a/file.py', order=42)
        encoded_key = entry_point_name.as_encoded_key()

        vassert( encoded_key == '42-my+path to-a+file.py' )

    @test(Fixture)
    def decoding_attachment_names(self, fixture):
        entry_point_name = EntryPointKeyEncodedAttachmentName(encoded_string='42-my+path to-a+file.py')

        vassert( entry_point_name.order == 42 )
        vassert( entry_point_name.decoded_path == 'my/path to-a/file.py')

