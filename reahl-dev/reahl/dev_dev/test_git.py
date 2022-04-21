# Copyright 2016-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Tests for dealing with git."""


import os
import os.path

from reahl.tofu import Fixture
from reahl.tofu import temp_dir, assert_recent
from reahl.tofu.pytestsupport import with_fixtures

from reahl.component.shelltools import Executable
from reahl.dev.devdomain import Git


class GitFixture(Fixture):
    def new_git_directory(self, initialised=True):
        git_directory = temp_dir()
        if initialised:
            with open(os.devnull, 'w') as DEVNULL:
                Executable('git').check_call(['init'], cwd=git_directory.name, stdout=DEVNULL, stderr=DEVNULL)
        return git_directory


@with_fixtures(GitFixture)
def test_is_version_controlled(git_fixture):
    fixture = git_fixture
    non_initialised_directory = fixture.new_git_directory(initialised=False)
    git = Git(non_initialised_directory.name)
    assert not git.is_version_controlled()

    git = Git(fixture.git_directory.name)
    assert git.is_version_controlled()


@with_fixtures(GitFixture)
def test_is_checked_in(git_fixture):
    fixture = git_fixture
    git = Git(fixture.git_directory.name)
    assert git.is_checked_in()

    open(os.path.join(fixture.git_directory.name, 'afile'), 'w').close()
    assert not git.is_checked_in()
    

@with_fixtures(GitFixture)
def test_last_commit_time(git_fixture):
    fixture = git_fixture
    git = Git(fixture.git_directory.name)
    git.config('user.name', 'Tester')
    git.config('user.email', 'test@reahl.org')
    git.commit('testing', allow_empty=True)

    assert_recent( git.last_commit_time )


@with_fixtures(GitFixture)
def test_tag_related(git_fixture):
    fixture = git_fixture
    git = Git(fixture.git_directory.name)
    git.config('user.name', 'Tester')
    git.config('user.email', 'test@reahl.org')
    git.commit('testing', allow_empty=True)

    assert git.get_tags() == []
    git.tag('mytag')
    assert git.get_tags(head_only=True) == ['mytag']
    assert git.get_tags() == ['mytag']

    git.commit('testing', allow_empty=True)
    git.tag('lasttag')
    assert git.get_tags(head_only=True) == ['lasttag']
    assert git.get_tags() == ['lasttag', 'mytag']



