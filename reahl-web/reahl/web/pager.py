# Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import print_function, unicode_literals, absolute_import, division

import six
from abc import ABCMeta, abstractproperty

from reahl.component.i18n import Translator

_ = Translator('reahl-web')


@six.add_metaclass(ABCMeta)
class PageIndexProtocol(object):
    @abstractproperty
    def pages_in_range(self): pass
    @abstractproperty
    def current_page(self): pass
    @abstractproperty
    def start_page(self): pass
    @abstractproperty
    def end_page(self): pass
    @abstractproperty
    def previous_page(self): pass
    @abstractproperty
    def next_page(self): pass
    @abstractproperty
    def last_page(self): pass
    @abstractproperty
    def has_next_page(self): pass
    @abstractproperty
    def has_previous_page(self): pass
