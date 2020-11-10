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


import datetime


from reahl.tofu import Fixture, set_up, uses
from reahl.tofu.pytestsupport import with_fixtures

from sqlalchemy import Column, Integer, Boolean, UnicodeText, ForeignKey

from reahl.dev.tools import EventTester
from reahl.sqlalchemysupport import Session, Base
from reahl.domain.workflowmodel import DeferredAction, Requirement, WorkflowInterface, Queue, Task, Inbox
from reahl.component.eggs import ReahlEgg
from reahl.domain.systemaccountmodel import LoginSession

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.domain_dev.fixtures import PartyAccountFixture


@uses(party_account_fixture=PartyAccountFixture)
class DeferredActionFixture(Fixture):

    def new_SomeObject(self):
        class SomeObject(Base):
            __tablename__ = 'someobject'
            id = Column(Integer, primary_key=True)
            done_flag = Column(Boolean, nullable=False, default=False)
            name = Column(UnicodeText, nullable=False)
            deadline_flag = Column(Boolean, nullable=False, default=False)

            def make_done(self):
                self.done_flag = True
            def deadline_reached(self):
                self.deadline_flag = True
        return SomeObject
        
    def new_MyDeferredAction(self):
        fixture = self
        class MyDeferredAction(DeferredAction):
            __tablename__ = 'mydeferredaction'
            __mapper_args__ = {'polymorphic_identity': 'mydeferredaction'}
            id = Column(Integer, ForeignKey(DeferredAction.id), primary_key=True)
            some_object_key = Column(UnicodeText, nullable=False)
        
            def __init__(self, some_object, **kwargs):
                super().__init__(some_object_key=some_object.name, **kwargs)
            def success_action(self):
                Session.query(fixture.SomeObject).filter_by(name=self.some_object_key).one().make_done()
            def deadline_action(self):
                Session.query(fixture.SomeObject).filter_by(name=self.some_object_key).one().deadline_reached()
        return MyDeferredAction

    def new_current_time(self):
        return datetime.datetime.now()
        
    def new_future_time(self):
        return self.current_time + datetime.timedelta(days=1)

    def new_past_time(self):
        return self.current_time - datetime.timedelta(days=1)

    def new_one_object(self):
        one = self.SomeObject(name='one')
        Session.add(one)
        return one

    def new_another_object(self):
        another = self.SomeObject(name='another')
        Session.add(another)
        return another


@with_fixtures(SqlAlchemyFixture, DeferredActionFixture)
def test_deferred_action_completes(sql_alchemy_fixture, deferred_action_fixture):
    """A DeferredAction will execute its primary action once all its Requirements are fulfilled; then, it and its Requirements are deleted."""

    fixture = deferred_action_fixture
    with sql_alchemy_fixture.persistent_test_classes(fixture.MyDeferredAction, fixture.SomeObject):
        requirements = [Requirement(), Requirement(), Requirement()]
        deferred_action = fixture.MyDeferredAction(fixture.one_object, requirements=requirements, deadline=fixture.future_time)
        Session.add(deferred_action)
        Session.flush()
        for requirement in requirements:
            requirement.set_fulfilled()
        assert fixture.one_object.done_flag
        assert not fixture.another_object.done_flag

        assert Session.query(Requirement).count() == 0
        assert Session.query(DeferredAction).count() == 0


@with_fixtures(SqlAlchemyFixture, DeferredActionFixture)
def test_deferred_action_times_out(sql_alchemy_fixture, deferred_action_fixture):
    """If all its Requirements are not fulfilled before its deadline has been reached, a DeferredAction executes its deadline action; then, it and its Requirements are deleted"""

    fixture = deferred_action_fixture
    with sql_alchemy_fixture.persistent_test_classes(fixture.MyDeferredAction, fixture.SomeObject):
        requirements = [Requirement(), Requirement(), Requirement()]
        deferred_action = fixture.MyDeferredAction(fixture.one_object, requirements=requirements, deadline=fixture.future_time)
        Session.add(deferred_action)
        Session.flush()

        assert deferred_action.deadline == fixture.future_time
        ReahlEgg.do_daily_maintenance_for_egg('reahl-domain')
        assert not fixture.one_object.deadline_flag
        assert not fixture.another_object.deadline_flag

        assert Session.query(Requirement).count() == 3
        assert Session.query(DeferredAction).count() == 1

        deferred_action.deadline = fixture.past_time
        ReahlEgg.do_daily_maintenance_for_egg('reahl-domain')
        assert fixture.one_object.deadline_flag
        assert not fixture.another_object.deadline_flag

        assert Session.query(Requirement).count() == 0
        assert Session.query(DeferredAction).count() == 0


@with_fixtures(SqlAlchemyFixture, DeferredActionFixture)
def test_deferred_action_completes_with_shared_requirements(sql_alchemy_fixture, deferred_action_fixture):
    """A requirement could be linked to many DeferredActions, in which case it will notify all on success"""

    fixture = deferred_action_fixture
    with sql_alchemy_fixture.persistent_test_classes(fixture.MyDeferredAction, fixture.SomeObject):
        requirements1 = [Requirement()]
        requirements2 = [Requirement(), Requirement()]
        deferred_action1 = fixture.MyDeferredAction(fixture.one_object,
                                                    requirements=requirements2,
                                                    deadline=fixture.future_time)
        Session.add(deferred_action1)
        deferred_action2 = fixture.MyDeferredAction(fixture.another_object,
                                                    requirements=requirements1+requirements2,
                                                    deadline=fixture.future_time)

        Session.add(deferred_action2)
        Session.flush()
        # The requirements are linked back to the correct DeferredActions
        for requirement in requirements2:
            assert set(requirement.deferred_actions) == {deferred_action1, deferred_action2}

        for requirement in requirements1:
            assert set(requirement.deferred_actions) == {deferred_action2}

        # If all of one DeferredAction's Requirements are fulfilled, ones also linked to another DeferrredAction
        # are not deleted just yet
        for requirement in requirements2:
            requirement.set_fulfilled()
        assert fixture.one_object.done_flag
        assert not fixture.another_object.done_flag

        for requirement in requirements1+requirements2:
            assert set(requirement.deferred_actions) == {deferred_action2}
        assert Session.query(Requirement).count() == 3
        assert Session.query(DeferredAction).count() == 1

        # But as soon as all Requirements of the last DeferredAction are fulfilled, the last Requirements
        # are deleted as usual
        for requirement in requirements1:
            requirement.set_fulfilled()
        assert fixture.one_object.done_flag
        assert fixture.another_object.done_flag

        assert Session.query(Requirement).count() == 0
        assert Session.query(DeferredAction).count() == 0


@with_fixtures(SqlAlchemyFixture, DeferredActionFixture)
def test_deferred_action_times_out_with_shared_requirements(sql_alchemy_fixture, deferred_action_fixture):
    """If a DeferredAction times out, it will not nuke Requirements shared with another DeferredAction."""

    fixture = deferred_action_fixture
    with sql_alchemy_fixture.persistent_test_classes(fixture.MyDeferredAction, fixture.SomeObject):
        requirements1 = [Requirement()]
        requirements2 = [Requirement(), Requirement()]
        deferred_action1 = fixture.MyDeferredAction(fixture.one_object,
                                                    requirements=requirements2,
                                                    deadline=fixture.future_time)
        Session.add(deferred_action1)
        deferred_action2 = fixture.MyDeferredAction(fixture.another_object,
                                                    requirements=requirements1+requirements2,
                                                    deadline=fixture.future_time)

        Session.add(deferred_action2)
        Session.flush()

        # If one DeferredAction times out, the remaining one and its Requirements are left intact
        deferred_action1.deadline=fixture.past_time

        ReahlEgg.do_daily_maintenance_for_egg('reahl-domain')
        assert fixture.one_object.deadline_flag
        assert not fixture.another_object.deadline_flag

        assert Session.query(Requirement).count() == 3
        assert Session.query(DeferredAction).count() == 1

        for requirement in requirements1+requirements2:
            assert set(requirement.deferred_actions) == {deferred_action2}

        # When no more DeferredActions are held onto by Requirements, those Requirements are deleted
        deferred_action2.deadline=fixture.past_time
        ReahlEgg.do_daily_maintenance_for_egg('reahl-domain')

        assert fixture.one_object.deadline_flag
        assert fixture.another_object.deadline_flag

        assert Session.query(Requirement).count() == 0
        assert Session.query(DeferredAction).count() == 0


@uses(sql_alchemy_fixture=SqlAlchemyFixture, party_account_fixture=PartyAccountFixture)
class TaskQueueFixture2(Fixture):

    @set_up
    def log_in_test_user(self):
        session = self.party_account_fixture.session
        system_account = self.party_account_fixture.system_account
        login_session = LoginSession.for_session(session)
        login_session.set_as_logged_in(system_account, True)

    def new_workflow_interface(self):
        return WorkflowInterface()

    def new_queue(self, name=None):
        name = name or 'A queue'
        queue = Queue(name=name)
        Session.add(queue)
        return queue

    def new_task(self, title=None, queue=None):
        title = title or 'A task'
        queue = queue or self.queue
        task = Task(title=title, queue=queue)
        Session.add(task)
        Session.flush()
        return task


@with_fixtures(PartyAccountFixture, TaskQueueFixture2)
def test_reserving_tasks(party_account_fixture, task_queue_fixture):
    """Tasks can be reserved by a party; a reserved task can be released again."""

    fixture = task_queue_fixture

    task = fixture.task

    assert task.is_available()
    assert not task.is_reserved_for(party_account_fixture.party)

    task.reserve_for(party_account_fixture.party)
    assert not task.is_available()
    assert task.is_reserved_for(party_account_fixture.party)

    task.release()
    assert task.is_available()
    assert not task.is_reserved_for(party_account_fixture.party)


@with_fixtures(TaskQueueFixture2)
def test_inbox(task_queue_fixture):
    """An Inbox is a collection of tasks in a collection of queues."""

    fixture = task_queue_fixture

    queue1 = fixture.new_queue(name='q1')
    queue2 = fixture.new_queue(name='q2')
    queue3 = fixture.new_queue(name='q3')
    inbox = Inbox([queue1, queue2])
    task1 = fixture.new_task(queue=queue1)
    task2 = fixture.new_task(queue=queue2)
    task3 = fixture.new_task(queue=queue3)

    tasks = inbox.get_tasks()
    assert tasks == [task1, task2]


@with_fixtures(PartyAccountFixture, TaskQueueFixture2)
def test_take_task_interface(party_account_fixture, task_queue_fixture):
    fixture = task_queue_fixture

    workflow_interface = fixture.workflow_interface
    task = fixture.task

    assert not task.is_reserved_for(party_account_fixture.party)
    take_task = EventTester(workflow_interface.events.take_task, task=task)
    take_task.fire_event()
    assert task.is_reserved_for(party_account_fixture.party)
    assert not take_task.can_write_event

    task.release()
    assert take_task.can_write_event


@with_fixtures(PartyAccountFixture, TaskQueueFixture2)
def test_go_to_task_interface(party_account_fixture, task_queue_fixture):
    fixture = task_queue_fixture

    workflow_interface = fixture.workflow_interface
    task = fixture.task

    assert not task.is_reserved_for(party_account_fixture.party)
    task.reserve_for(party_account_fixture.party)
    go_to_task = EventTester(workflow_interface.events.go_to_task, task=task)
    assert go_to_task.can_read_event

    task.release()
    assert not go_to_task.can_read_event


@with_fixtures(PartyAccountFixture, TaskQueueFixture2)
def test_release_task_interface(party_account_fixture, task_queue_fixture):
    fixture = task_queue_fixture

    workflow_interface = fixture.workflow_interface
    task = fixture.task

    task.reserve_for(party_account_fixture.party)
    release_task = EventTester(workflow_interface.events.release_task, task=task)
    release_task.fire_event()
    assert not task.is_reserved_for(party_account_fixture.party)
    assert not release_task.can_write_event

    task.reserve_for(party_account_fixture.party)
    assert release_task.can_write_event
