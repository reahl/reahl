# Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import print_function, unicode_literals, absolute_import, division

import os
import os.path

from reahl.tofu import Fixture, temp_dir, assert_recent

from reahl.bzrsupport import Bzr, Executable


class BzrFixture(Fixture):
    def new_bzr_directory(self, initialised=True):
        bzr_directory = temp_dir()
        if initialised:
            with open(os.devnull, 'w') as DEVNULL:
                Executable('bzr').check_call(['init'], cwd=bzr_directory.name, stdout=DEVNULL, stderr=DEVNULL)
        return bzr_directory


bzr_fixture = BzrFixture.as_pytest_fixture()


def test_is_version_controlled(bzr_fixture):
    non_initialised_directory = bzr_fixture.new_bzr_directory(initialised=False)
    bzr = Bzr(non_initialised_directory.name)
    assert not bzr.is_version_controlled()

    bzr = Bzr(bzr_fixture.bzr_directory.name)
    assert bzr.is_version_controlled()


def test_is_checked_in(bzr_fixture):
    bzr = Bzr(bzr_fixture.bzr_directory.name)
    assert bzr.is_checked_in()

    open(os.path.join(bzr_fixture.bzr_directory.name, 'afile'), 'w').close()
    assert not bzr.is_checked_in()


def test_last_commit_time(bzr_fixture):
    bzr = Bzr(bzr_fixture.bzr_directory.name)
    bzr.commit('testing', unchanged=True)

    assert_recent( bzr.last_commit_time )


def test_tag_related(bzr_fixture):
    bzr = Bzr(bzr_fixture.bzr_directory.name)
    bzr.commit('testing', unchanged=True)

    assert bzr.get_tags() == []
    bzr.tag('mytag')
    assert bzr.get_tags(head_only=True) == ['mytag']
    assert bzr.get_tags() == ['mytag']

    bzr.commit('testing', unchanged=True)
    bzr.tag('lasttag')
    assert bzr.get_tags(head_only=True) == ['lasttag']
    assert bzr.get_tags() == ['lasttag', 'mytag']



