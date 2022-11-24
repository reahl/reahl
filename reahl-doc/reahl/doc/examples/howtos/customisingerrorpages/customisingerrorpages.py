# Copyright 2020, 2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.component.modelinterface import ExposedNames, Event, Action
from reahl.web.fw import UserInterface, ErrorWidget, Url
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.navbar import Navbar, NavbarLayout
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import Form, Button, FormLayout
from reahl.web.bootstrap.ui import H, P, A


# NOTE: For the error page to display, this app should not be run in DEBUG mode. See etc/reahl.config.py

class MySitePage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.use_layout(PageLayout(document_layout=Container(),
                                    contents_layout=ColumnLayout(
                                                        ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        navbar = Navbar(view).use_layout(NavbarLayout())
        navbar.layout.set_brand_text('My Site')
        self.layout.header.add_child(navbar)


class CustomErrorPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        error_widget = self.body.insert_child(0, ErrorWidget(view))
        error_widget.add_child(H(view, 1, text='Oops, something broke'))
        error_widget.add_child(P(view, text=error_widget.error_message))
        error_widget.add_child(A(view, Url(error_widget.error_source_href), description='Click here to try again'))

    @classmethod
    def get_widget_bookmark_for_error(cls, error_message, error_source_bookmark):
        return ErrorWidget.get_widget_bookmark_for_error(error_message, error_source_bookmark)


class BreakingUI(UserInterface):
    def assemble(self):
        self.define_page(MySitePage)
        home = self.define_view('/', title='Error Page demo')
        home.set_slot('main', SimpleForm.factory())


# Note: See etc/web.config.py to set which root UI you want to run
class BreakingUIWithBuiltInErrorPage(BreakingUI):
    pass


# Note: See etc/web.config.py to set which root UI you want to run
class BreakingUIWithCustomErrorPage(BreakingUI):
    def assemble(self):
        super().assemble()
        self.define_error_view(CustomErrorPage.factory())


class SimpleForm(Form):
    def __init__(self, view):
        super().__init__(view, 'simple_form')
        self.use_layout(FormLayout())
        if self.exception:
            self.layout.add_alert_for_domain_exception(self.exception)

        self.add_child(P(view, text='Press Submit to cause an error'))

        self.domain_object = SimpleDomainObject()

        self.define_event_handler(self.domain_object.events.submit)
        self.add_child(Button(self, self.domain_object.events.submit))


class SimpleDomainObject(Base):
    __tablename__ = 'customising_error_pages_simple_object'

    id = Column(Integer, primary_key=True)

    events = ExposedNames()
    events.submit = lambda i: Event(label='Submit', action=Action(i.submit))

    def submit(self):
        raise Exception('This error is thrown intentionally')
