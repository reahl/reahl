# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import print_function, unicode_literals, absolute_import, division

import os
import os.path

from reahl.tofu import test, Fixture
from reahl.tofu import temp_dir, vassert, assert_recent

from reahl.component.shelltools import Executable
from reahl.dev.devdomain import Git

class GitFixture(Fixture):
    def new_git_directory(self, initialised=True):
        git_directory = temp_dir()
        if initialised:
            with open(os.devnull, 'w') as DEVNULL:
                Executable('git').check_call(['init'], cwd=git_directory.name, stdout=DEVNULL, stderr=DEVNULL)
        return git_directory

        
@test(GitFixture)
def is_version_controlled(fixture):
    non_initialised_directory = fixture.new_git_directory(initialised=False)
    git = Git(non_initialised_directory.name)
    vassert( not git.is_version_controlled() )

    git = Git(fixture.git_directory.name)
    vassert( git.is_version_controlled() )

@test(GitFixture)
def is_checked_in(fixture):
    git = Git(fixture.git_directory.name)
    vassert( git.is_checked_in() )

    open(os.path.join(fixture.git_directory.name, 'afile'), 'w').close()
    vassert( not git.is_checked_in() )
    
@test(GitFixture)
def last_commit_time(fixture):
    git = Git(fixture.git_directory.name)
    git.commit('testing', allow_empty=True)

    assert_recent( git.last_commit_time )

@test(GitFixture)
def tag_related(fixture):
    git = Git(fixture.git_directory.name)
    git.commit('testing', allow_empty=True)

    vassert( git.get_tags() == [] )
    git.tag('mytag')
    vassert( git.get_tags(head_only=True) == ['mytag'] )
    vassert( git.get_tags() == ['mytag'] )

    git.commit('testing', allow_empty=True)
    git.tag('lasttag')
    vassert( git.get_tags(head_only=True) == ['lasttag'] )
    vassert( git.get_tags() == ['lasttag', 'mytag'] )



