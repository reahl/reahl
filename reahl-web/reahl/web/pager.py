# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.component.decorators import deprecated
import reahl.web.attic.paging


@deprecated('Please use reahl.web.attic.paging:PagedPanel instead', '3.2')
class PagedPanel(reahl.web.attic.paging.PagedPanel):
    __doc__ = reahl.web.attic.paging.PagedPanel.__doc__


@deprecated('Please use reahl.web.attic.paging:Page instead', '3.2')
class Page(reahl.web.attic.paging.Page):
    __doc__ = reahl.web.attic.paging.Page.__doc__


@deprecated('Please use reahl.web.attic.paging:PageIndex instead', '3.2')
class PageIndex(reahl.web.attic.paging.PageIndex):
    __doc__ = reahl.web.attic.paging.PageIndex.__doc__


@deprecated('Please use reahl.web.attic.paging:SequentialPageIndex instead', '3.2')
class SequentialPageIndex(reahl.web.attic.paging.SequentialPageIndex):
    __doc__ = reahl.web.attic.paging.SequentialPageIndex.__doc__


@deprecated('Please use reahl.web.attic.paging:PageMenu instead', '3.2')
class PageMenu(reahl.web.attic.paging.PageMenu):
    __doc__ = reahl.web.attic.paging.PageMenu.__doc__


@deprecated('Please use reahl.web.attic.paging:AnnualItemOrganiserProtocol instead', '3.2')
class AnnualItemOrganiserProtocol(reahl.web.attic.paging.AnnualItemOrganiserProtocol):
    __doc__ = reahl.web.attic.paging.AnnualItemOrganiserProtocol.__doc__


@deprecated('Please use reahl.web.attic.paging:AnnualPageIndex instead', '3.2')
class AnnualPageIndex(reahl.web.attic.paging.AnnualPageIndex):
    __doc__ = reahl.web.attic.paging.AnnualPageIndex.__doc__



