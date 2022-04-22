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


from reahl.stubble.stub import StubClass as stubclass

from reahl.stubble.stub import Delegate
from reahl.stubble.stub import Impostor

from reahl.stubble.stub import Exempt as exempt
from reahl.stubble.stub import SlotConstrained as slotconstrained
from reahl.stubble.stub import CheckedInstance as checkedinstance

from .easteregg import EasterEgg

easter_egg = EasterEgg()
easter_egg.add_to_working_set()  #TODO: why does this not always work anymore??


class EmptyStub:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


from reahl.stubble.intercept import CallMonitor, InitMonitor, SystemOutStub
from reahl.stubble.intercept import replaced
