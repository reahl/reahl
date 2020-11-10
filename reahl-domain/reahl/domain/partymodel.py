# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from sqlalchemy import Column, Integer

from reahl.sqlalchemysupport import Base
from reahl.component.i18n import Catalogue

_ = Catalogue('reahl-domain')


class Party(Base):
    """A Party is any legal entity which the system may keep track of."""
    __tablename__ = 'party'
    id = Column(Integer, primary_key=True)



