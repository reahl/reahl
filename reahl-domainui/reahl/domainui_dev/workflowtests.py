# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from elixir import using_options, Entity, Boolean, UnicodeText

from nose.tools import istest
from reahl.tofu import Fixture, test, set_up
from reahl.tofu import vassert
from reahl.stubble import easter_egg


from reahl.sqlalchemysupport import Session, metadata
from reahl.web.ui import TwoColumnPage, Panel, P
from reahl.workflowmodel import DeferredAction, Requirement, WorkflowInterface, Queue, Task, Inbox
from reahl.domainui.workflow import InboxUI
from reahl.web.fw import UserInterface, Url
from reahl.domain_dev.workflowtests import TaskQueueZooMixin
from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.webdev.tools import Browser
from reahl.domainui_dev.fixtures import BookmarkStub
from reahl.domainui.accounts import AccountUI

class WorkflowWebFixture(Fixture, WebBasicsMixin, TaskQueueZooMixin):
    def new_queues(self):
        return [self.queue]
    
    def new_account_bookmarks(self):
        class Bookmarks(object):
            terms_bookmark = BookmarkStub(Url(u'/#terms'), u'Terms')
            privacy_bookmark = BookmarkStub(Url(u'/#privacy'), u'Privacy Policy')
            disclaimer_bookmark = BookmarkStub(Url(u'/#disclaimer'), u'Disclaimer')
        return Bookmarks()

    def new_wsgi_app(self, enable_js=False):
        fixture = self
        def get_queues():
            return fixture.queues
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                accounts = self.define_user_interface(u'/accounts', AccountUI, {u'main_slot': u'main'},
                                              name=u'test_ui', bookmarks=fixture.account_bookmarks)
                login_bookmark = accounts.get_bookmark(relative_path='/login')
                self.define_user_interface(u'/inbox',  InboxUI,  {u'main_slot': u'main'}, 
                                   name=u'test_ui', login_bookmark=login_bookmark, get_queues=get_queues)
        return super(WorkflowWebFixture, self).new_wsgi_app(enable_js=enable_js,
                                                         site_root=MainUI)

    def new_system_account(self):
        account = super(WorkflowWebFixture, self).new_system_account()
        account.party = self.party
        return account

class MyTask(Task):
    using_options(metadata=metadata, session=Session, shortnames=True, inheritance=u'single')


class MyTaskWidget(Panel):
    @classmethod
    def displays(cls, task):
        return task.__class__ is MyTask

    def __init__(self, view, task):
        super(MyTaskWidget, self).__init__(view)
        self.add_child(P(view, text=u'my task widget'))


@istest
class Tests(object):
    @test(WorkflowWebFixture)
    def detour_to_login(self, fixture):
        browser = Browser(fixture.wsgi_app)

        browser.open(u'/inbox/')
        vassert( browser.location_path == '/accounts/login' )
        browser.type(u'//input[@name="email"]', fixture.system_account.email)
        browser.type(u'//input[@name="password"]', fixture.system_account.password)
        browser.click(u'//input[@value="Log in"]')
        vassert( browser.location_path == '/inbox/' )
        
        

    @test(WorkflowWebFixture)
    def take_and_release_task(self, fixture):
        browser = Browser(fixture.wsgi_app)
        task = fixture.task

        take_task_button = u'//input[@value="Take"]'
        defer_task_button = u'//input[@value="Defer"]'
        release_task_button = u'//input[@value="Release"]'
        go_to_task_button = u'//input[@value="Go to"]'

        fixture.log_in(browser=browser)
        browser.open(u'/inbox/')
    
        browser.click(take_task_button)
        vassert( browser.location_path == u'/inbox/task/%s' % task.id )

        browser.click(defer_task_button)
        vassert( browser.location_path == u'/inbox/' )
        
        browser.click(go_to_task_button)
        vassert( browser.location_path == u'/inbox/task/%s' % task.id )

        browser.click(release_task_button)
        vassert( browser.location_path == u'/inbox/' )

    @test(WorkflowWebFixture)
    def widgets_for_tasks(self, fixture):
        """The widget to use for displaying a particular type of task can be set via an entry point."""
        pkg_resources.working_set.add(easter_egg)
        line = 'MyTaskWidget = reahl.domainui_dev.workflowtests:MyTaskWidget' 
        easter_egg.add_entry_point_from_line(u'reahl.workflowui.task_widgets', line)

        with fixture.persistent_test_classes(MyTask):
            task = MyTask(queue=fixture.queue, title=u'a task')

            try:
                Task.mapper.polymorphic_on = Task.table.columns['id']
                Session.flush()

                MyTask.mapper.polymorphic_identity = task.id
                MyTask.mapper.polymorphic_map[task.id] = MyTask.mapper

                browser = Browser(fixture.wsgi_app)
                fixture.log_in(browser=browser)
                browser.open(u'/inbox/task/%s' % task.id )
                html = browser.get_html_for(u'//div/p')
                vassert( html == u'<p>my task widget</p>' )
            finally:
                Task.mapper.polymorphic_on = None
                del MyTask.mapper.polymorphic_map[task.id] 
        assert None, 'This is ugly, but the only way I could get this elixir test stub to work'
