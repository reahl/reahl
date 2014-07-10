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
from nose.tools import istest
from reahl.tofu import  test, Fixture, vassert
from reahl.stubble import easter_egg

from reahl.component.eggs import ReahlEgg

@istest
class AttachmentTests(object):
    @test(Fixture)
    def attachment_basics(self, fixture):

        easter_egg.clear()

        # The attachments are published via the reahl.attachments.<label> entry point, with their order specified
        line = '3:Asome/file/path = reahl'
        easter_egg.add_entry_point_from_line('reahl.attachments.js', line)
        line = '0:Bsome/first/path = reahl'
        easter_egg.add_entry_point_from_line('reahl.attachments.js', line)

        # The attachments are found in the correct order
        found_attachments = ReahlEgg(easter_egg).find_attachments('js')
        filenames = [i.filename for i in found_attachments]
        vassert( filenames == ['Bsome/first/path', 'Asome/file/path'] )



