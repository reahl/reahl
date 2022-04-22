# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


class EventTester:
    def __init__(self, event, **arguments):
        self.occurring_event = event.with_arguments(**arguments)
        self.occurring_event.from_input(self.occurring_event.as_input())

    def fire_event(self):
        return self.occurring_event.fire()

    @property
    def can_write_event(self):
        return self.occurring_event.can_write()

    @property
    def can_read_event(self):
        return self.occurring_event.can_read()
