# Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import datetime

from nose.tools import istest
from reahl.tofu import Fixture
from reahl.tofu import test
from reahl.tofu import vassert

from sqlalchemy import Column, Integer, Boolean, UnicodeText, ForeignKey

from reahl.dev.tools import EventTester
from reahl.sqlalchemysupport import metadata, Session, Base
from reahl.domain.workflowmodel import DeferredAction, Requirement, WorkflowInterface, Queue, Task, Inbox
from reahl.component.eggs import ReahlEgg
from reahl.domain_dev.fixtures import PartyModelZooMixin, BasicModelZooMixin
from reahl.domain.systemaccountmodel import LoginSession
from reahl.web_dev.fixtures import WebBasicsMixin 
class DeferredActionFixture(Fixture, BasicModelZooMixin):
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
                super(MyDeferredAction, self).__init__(some_object_key=some_object.name, **kwargs)
            def success_action(self):
                Session.query(fixture.SomeObject).filter_by(name=self.some_object_key).one().make_done()
            def deadline_action(self):
                Session.query(fixture.SomeObject).filter_by(name=self.some_object_key).one().deadline_reached()
        return MyDeferredAction

    def new_current_time(self):
        return datetime.datetime.now();
        
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
  
    
@istest
class DeferredActionTests(object):
    @test(DeferredActionFixture)
    def deferred_action_completes(self, fixture):
        """A DeferredAction will execute its primary action once all its Requirements are fulfilled; then, it and its Requirements are deleted."""
        with fixture.persistent_test_classes(fixture.MyDeferredAction, fixture.SomeObject):
            requirements = [Requirement(), Requirement(), Requirement()]
            deferred_action = fixture.MyDeferredAction(fixture.one_object, requirements=requirements, deadline=fixture.future_time)
            Session.add(deferred_action)
            Session.flush()
            for requirement in requirements:
                requirement.set_fulfilled()
            vassert( fixture.one_object.done_flag )
            vassert( not fixture.another_object.done_flag )

            vassert( Session.query(Requirement).count() == 0 )
            vassert( Session.query(DeferredAction).count() == 0 )

    @test(DeferredActionFixture)
    def deferred_action_times_out(self, fixture):
        """If all its Requirements are not fulfilled before its deadline has been reached, a DeferredAction executes its deadline action; then, it and its Requirements are deleted"""
        
        with fixture.persistent_test_classes(fixture.MyDeferredAction, fixture.SomeObject):
            requirements = [Requirement(), Requirement(), Requirement()]
            deferred_action = fixture.MyDeferredAction(fixture.one_object, requirements=requirements, deadline=fixture.future_time)
            Session.add(deferred_action)
            Session.flush()

            vassert( deferred_action.deadline == fixture.future_time )
            ReahlEgg.do_daily_maintenance_for_egg('reahl-domain')
            vassert( not fixture.one_object.deadline_flag )
            vassert( not fixture.another_object.deadline_flag )

            vassert( Session.query(Requirement).count() == 3 )
            vassert( Session.query(DeferredAction).count() == 1 )

            deferred_action.deadline = fixture.past_time
            ReahlEgg.do_daily_maintenance_for_egg('reahl-domain')
            vassert( fixture.one_object.deadline_flag )
            vassert( not fixture.another_object.deadline_flag )

            vassert( Session.query(Requirement).count() == 0 )
            vassert( Session.query(DeferredAction).count() == 0 )

        
    @test(DeferredActionFixture)
    def deferred_action_completes_with_shared_requirements(self, fixture):
        """A requirement could be linked to many DeferredActions, in which case it will notify all on success"""
 
        with fixture.persistent_test_classes(fixture.MyDeferredAction, fixture.SomeObject):
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
                vassert( set(requirement.deferred_actions) == {deferred_action1, deferred_action2} )

            for requirement in requirements1:
                vassert( set(requirement.deferred_actions) == {deferred_action2} )

            # If all of one DeferredAction's Requirements are fulfilled, ones also linked to another DeferrredAction
            # are not deleted just yet
            for requirement in requirements2:
                requirement.set_fulfilled()
            vassert( fixture.one_object.done_flag )
            vassert( not fixture.another_object.done_flag )

            for requirement in requirements1+requirements2:
                vassert( set(requirement.deferred_actions) == {deferred_action2} )
            vassert( Session.query(Requirement).count() == 3 )
            vassert( Session.query(DeferredAction).count() == 1 )

            # But as soon as all Requirements of the last DeferredAction are fulfilled, the last Requirements
            # are deleted as usual
            for requirement in requirements1:
                requirement.set_fulfilled()
            vassert( fixture.one_object.done_flag )
            vassert( fixture.another_object.done_flag )

            vassert( Session.query(Requirement).count() == 0 )
            vassert( Session.query(DeferredAction).count() == 0 )


    @test(DeferredActionFixture)
    def deferred_action_times_out_with_shared_requirements(self, fixture):
        """If a DeferredAction times out, it will not nuke Requirements shared with another DeferredAction."""
 
        with fixture.persistent_test_classes(fixture.MyDeferredAction, fixture.SomeObject):
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
            vassert( fixture.one_object.deadline_flag )
            vassert( not fixture.another_object.deadline_flag )

            vassert( Session.query(Requirement).count() == 3 )
            vassert( Session.query(DeferredAction).count() == 1 )

            for requirement in requirements1+requirements2:
                vassert( set(requirement.deferred_actions) == {deferred_action2} )

            # When no more DeferredActions are held onto by Requirements, those Requirements are deleted
            deferred_action2.deadline=fixture.past_time
            ReahlEgg.do_daily_maintenance_for_egg('reahl-domain')

            vassert( fixture.one_object.deadline_flag )
            vassert( fixture.another_object.deadline_flag )

            vassert( Session.query(Requirement).count() == 0 )
            vassert( Session.query(DeferredAction).count() == 0 )


class TaskQueueZooMixin(PartyModelZooMixin):
    def new_session(self, system_account=None):
        session = super(TaskQueueZooMixin, self).new_session()
        system_account = self.new_system_account(party=self.party)
        login_session = LoginSession.for_session(session)
        login_session.set_as_logged_in(system_account, True)
        return session

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


class TaskQueueFixture(Fixture, TaskQueueZooMixin):
    pass

@istest
class TaskQueueTests(object):
    @test(TaskQueueFixture)
    def reserving_tasks(self, fixture):
        """Tasks can be reserved by a party; a reserved task can be released again."""
        task = fixture.task

        vassert( task.is_available() )
        vassert( not task.is_reserved_for(fixture.party) )

        task.reserve_for(fixture.party)
        vassert( not task.is_available() )
        vassert( task.is_reserved_for(fixture.party) )

        task.release()
        vassert( task.is_available() )
        vassert( not task.is_reserved_for(fixture.party) )

    @test(TaskQueueFixture)
    def inbox(self, fixture):
        """An Inbox is a collection of tasks in a collection of queues."""
        queue1 = fixture.new_queue(name='q1')
        queue2 = fixture.new_queue(name='q2')
        queue3 = fixture.new_queue(name='q3')
        inbox = Inbox([queue1, queue2])
        task1 = fixture.new_task(queue=queue1)
        task2 = fixture.new_task(queue=queue2)
        task3 = fixture.new_task(queue=queue3)

        tasks = inbox.get_tasks()
        vassert( tasks == [task1, task2] )
        
    @test(TaskQueueFixture)
    def take_task_interface(self, fixture):
        workflow_interface = fixture.workflow_interface
        task = fixture.task

        vassert( not task.is_reserved_for(fixture.party) )
        take_task = EventTester(workflow_interface.events.take_task, task=task)
        take_task.fire_event()
        vassert( task.is_reserved_for(fixture.party) )
        vassert( not take_task.can_write_event )

        task.release()
        vassert( take_task.can_write_event )

    @test(TaskQueueFixture)
    def go_to_task_interface(self, fixture):
        workflow_interface = fixture.workflow_interface
        task = fixture.task

        vassert( not task.is_reserved_for(fixture.party) )
        task.reserve_for(fixture.party)
        go_to_task = EventTester(workflow_interface.events.go_to_task, task=task)
        vassert( go_to_task.can_read_event )

        task.release()
        vassert( not go_to_task.can_read_event )


    @test(TaskQueueFixture)
    def release_task_interface(self, fixture):
        workflow_interface = fixture.workflow_interface
        task = fixture.task

        task.reserve_for(fixture.party)
        release_task = EventTester(workflow_interface.events.release_task, task=task)
        release_task.fire_event()
        vassert( not task.is_reserved_for(fixture.party) )
        vassert( not release_task.can_write_event )

        task.reserve_for(fixture.party)
        vassert( release_task.can_write_event )
