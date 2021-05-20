# Copyright 2013-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import pkg_resources


from reahl.tofu import Fixture, set_up, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import easter_egg

from sqlalchemy import Column, Integer, ForeignKey

from reahl.domain.workflowmodel import Task
from reahl.domainui.bootstrap.workflow import InboxUI, TaskWidget
from reahl.domainui.bootstrap.accounts import AccountUI
from reahl.domainuiegg import DomainUiConfig
from reahl.domainui_dev.fixtures import BookmarkStub

from reahl.browsertools.browsertools import Browser, XPath

from reahl.web.fw import UserInterface, Url
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.grid import ResponsiveSize, ColumnLayout, ColumnOptions, Container

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.domain_dev.fixtures import PartyAccountFixture
from reahl.dev.fixtures import ReahlSystemFixture
from reahl.web_dev.fixtures import WebFixture
from reahl.domain_dev.test_workflow import TaskQueueFixture2


@uses(reahl_system_fixture=ReahlSystemFixture,
      sql_alchemy_fixture=SqlAlchemyFixture,
      party_account_fixture=PartyAccountFixture,
      web_fixture=WebFixture,
      task_queue_fixture=TaskQueueFixture2)
class WorkflowWebFixture(Fixture):

    def new_queues(self):
        return [self.task_queue_fixture.queue]
    
    def new_account_bookmarks(self):
        class Bookmarks:
            terms_bookmark = BookmarkStub(Url('/#terms'), 'Terms')
            privacy_bookmark = BookmarkStub(Url('/#privacy'), 'Privacy Policy')
            disclaimer_bookmark = BookmarkStub(Url('/#disclaimer'), 'Disclaimer')
        return Bookmarks()

    def new_wsgi_app(self, enable_js=False):
        fixture = self

        def get_queues():
            return fixture.queues

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                                  contents_layout=ColumnLayout(ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
                accounts = self.define_user_interface('/accounts', AccountUI, {'main_slot': 'main'},
                                                      name='test_ui', bookmarks=fixture.account_bookmarks)
                login_bookmark = accounts.get_bookmark(relative_path='/login')
                self.define_user_interface('/inbox',  InboxUI,  {'main_slot': 'main'}, 
                                           name='test_ui', login_bookmark=login_bookmark, get_queues=get_queues)
        return self.web_fixture.new_wsgi_app(enable_js=enable_js, site_root=MainUI)

    @set_up
    def add_domain_config(self):
        config = self.reahl_system_fixture.config
        config.workflowui = DomainUiConfig()


class MyTask(Task):
    __tablename__ = 'mytask'
    __mapper_args__ = {'polymorphic_identity': 'mytask'}
    id = Column(Integer, ForeignKey('task.id'), primary_key=True)


class MyTaskWidget(TaskWidget):
    @classmethod
    def displays(cls, task):
        return task.__class__ is MyTask

    def create_contents(self):
        self.add_child(P(self.view, text='my task widget'))


@with_fixtures(WebFixture, PartyAccountFixture, WorkflowWebFixture)
def test_detour_to_login(web_fixture, party_account_fixture, workflow_web_fixture):
    fixture = workflow_web_fixture

    browser = Browser(fixture.wsgi_app)

    browser.open('/inbox/')
    assert browser.current_url.path == '/accounts/login'
    browser.type(XPath.input_labelled('Email'), party_account_fixture.system_account.email)
    browser.type(XPath.input_labelled('Password'), party_account_fixture.system_account.password)
    browser.click(XPath.button_labelled('Log in'))
    assert browser.current_url.path == '/inbox/'


@with_fixtures(WebFixture, TaskQueueFixture2, WorkflowWebFixture)
def test_take_and_release_task(web_fixture, task_queue_fixture, workflow_web_fixture):
    fixture = workflow_web_fixture

    browser = Browser(fixture.wsgi_app)
    task = task_queue_fixture.task

    take_task_button = XPath.button_labelled('Take')
    defer_task_button = XPath.button_labelled('Defer')
    release_task_button = XPath.button_labelled('Release')
    go_to_task_button = XPath.button_labelled('Go to')

    web_fixture.log_in(browser=browser)
    browser.open('/inbox/')

    browser.click(take_task_button)
    assert browser.current_url.path == '/inbox/task/%s' % task.id

    browser.click(defer_task_button)
    assert browser.current_url.path == '/inbox/'

    browser.click(go_to_task_button)
    assert browser.current_url.path == '/inbox/task/%s' % task.id

    browser.click(release_task_button)
    assert browser.current_url.path == '/inbox/'


@with_fixtures(WebFixture, SqlAlchemyFixture, TaskQueueFixture2, WorkflowWebFixture)
def test_widgets_for_tasks(web_fixture, sql_alchemy_fixture, task_queue_fixture, workflow_web_fixture):
    """The widget to use for displaying a particular type of task can be set via an entry point."""
    fixture = workflow_web_fixture

    pkg_resources.working_set.add(easter_egg)
    line = 'MyTaskWidget = reahl.domainui_dev.bootstrap.test_workflow:MyTaskWidget'
    easter_egg.add_entry_point_from_line('reahl.workflowui.task_widgets', line)

    with sql_alchemy_fixture.persistent_test_classes(MyTask):
        task = MyTask(queue=task_queue_fixture.queue, title='a task')

        browser = Browser(fixture.wsgi_app)
        web_fixture.log_in(browser=browser)
        browser.open('/inbox/task/%s' % task.id )
        html = browser.get_html_for('//div/p')
        assert html == '<p>my task widget</p>'
