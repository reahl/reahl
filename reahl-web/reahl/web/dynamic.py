# Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved.
# -*- encoding: utf-8 -*-
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
"""
.. versionadded: 4.1

Classes for creating pages that change on the fly.
"""


from reahl.web.ui import Div
from reahl.component.modelinterface import exposed

class DynamicSection(Div):
    """
    A DynamicSection is a Div that is refreshed when the value of certain 
    inputs (its trigger Inputs) change.
    """
    def __init__(self, view, css_id, trigger_inputs):
        self.trigger_inputs = trigger_inputs
        super(DynamicSection, self).__init__(view, css_id=css_id)
        self.enable_refresh()
        for trigger_input in trigger_inputs:
            trigger_input.enable_notify_change(self, trigger_input.bound_field)

    @exposed
    def query_fields(self, fields):
        for trigger_input in self.trigger_inputs:
            setattr(fields, trigger_input.name, trigger_input.bound_field)
