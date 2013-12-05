# Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""A heading for this module
=========================

Copyright (C) 2008 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)

"""

from reahl.component.config import Configuration, EntryPointClassList


class DomainUiConfig(Configuration):
    filename = u'domainui.config.py'
    config_key = u'workflowui'
    task_widgets = EntryPointClassList(u'reahl.workflowui.task_widgets', description=u'All available Widgets for displaying workflow tasks')



