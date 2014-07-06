# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Tests for the bzrsupport module."""

from __future__ import unicode_literals
from __future__ import print_function

import os
import os.path

from nose.tools import istest
from reahl.tofu import test, Fixture
from reahl.tofu import temp_dir, vassert, assert_recent

from reahl.bzrsupport import Bzr, Executable


class BzrFixture(Fixture):
    def new_bzr_directory(self, initialised=True):
        bzr_directory = temp_dir()
        if initialised:
            with file(os.devnull, 'w') as DEVNULL:
                Executable('bzr').check_call(['init'], cwd=bzr_directory.name, stdout=DEVNULL, stderr=DEVNULL)
        return bzr_directory

        
@istest
class BzrTests(object):
    @test(BzrFixture)
    def is_version_controlled(self, fixture):
        non_initialised_directory = fixture.new_bzr_directory(initialised=False)
        bzr = Bzr(non_initialised_directory.name)
        vassert( not bzr.is_version_controlled() )

        bzr = Bzr(fixture.bzr_directory.name)
        vassert( bzr.is_version_controlled() )

    @test(BzrFixture)
    def is_checked_in(self, fixture):
        bzr = Bzr(fixture.bzr_directory.name)
        vassert( bzr.is_checked_in() )

        file(os.path.join(fixture.bzr_directory.name, 'afile'), 'w').close()
        vassert( not bzr.is_checked_in() )
        
    @test(BzrFixture)
    def last_commit_time(self, fixture):
        bzr = Bzr(fixture.bzr_directory.name)
        bzr.commit('testing', unchanged=True)

        assert_recent( bzr.last_commit_time )

    @test(BzrFixture)
    def tag_related(self, fixture):
        bzr = Bzr(fixture.bzr_directory.name)
        bzr.commit('testing', unchanged=True)

        vassert( bzr.get_tags() == [] )
        bzr.tag('mytag')
        vassert( bzr.get_tags(head_only=True) == ['mytag'] )
        vassert( bzr.get_tags() == ['mytag'] )

        bzr.commit('testing', unchanged=True)
        bzr.tag('lasttag')
        vassert( bzr.get_tags(head_only=True) == ['lasttag'] )
        vassert( bzr.get_tags() == ['lasttag', 'mytag'] )



