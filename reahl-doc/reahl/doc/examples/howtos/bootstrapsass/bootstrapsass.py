# Copyright 2018, 2019, 2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.component.modelinterface import exposed, Field, Event, Action, Choice, ChoiceField, IntegerField, BooleanField
from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface, Widget
from reahl.web.ui import StaticColumn, DynamicColumn
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import FieldSet, Div, P, Alert
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import Form, FormLayout, TextInput, SelectInput, RadioButtonSelectInput, CheckboxInput, Button
from reahl.web.bootstrap.tables import Table
from reahl.web.libraries import Library

from sqlalchemy import Column, Integer, UnicodeText, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from reahl.sqlalchemysupport import Base, Session, session_scoped



class ThemedUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=ColumnLayout(
                                                              ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        home = self.define_view('/', title='Themed example')
        home.set_slot('main', SomeWidget.factory())


class SomeWidget(Widget):
    def __init__(self, view):
        super().__init__(view)

        self.add_child(Alert(view, 'This is an alert in danger color', severity='danger'))

        self.add_child(Alert(view, 'This is an alert in primary color', severity='primary'))




class CompiledBootstrap(Library):
    def __init__(self):
        super().__init__('custom')
        self.egg_name = 'bootstrapsass'
        self.shipped_in_directory = 'dist'
        self.files = [
                      'theme.css',
                      'main.js'
                      ]
