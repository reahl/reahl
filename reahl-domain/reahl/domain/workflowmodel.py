# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""A simple model for implementing workflow concepts.

   The basics of workflow is the ability for the system to allocate Tasks to users via
   Queues that can be monitored by these users. Via this model a program can also be written
   to schedule a particular task for the system to do some time in the future.
"""

import datetime

from sqlalchemy import Column, Table, Integer, ForeignKey, UnicodeText, String, DateTime, Boolean, Unicode
from sqlalchemy.orm import relationship, backref

from reahl.component.i18n import Catalogue
from reahl.sqlalchemysupport import Session, PersistedField, Base
from reahl.component.modelinterface import Action
from reahl.component.modelinterface import CurrentUser
from reahl.component.modelinterface import Event
from reahl.component.modelinterface import ExposedNames
from reahl.component.modelinterface import secured
from reahl.domain.partymodel import Party

_ = Catalogue('reahl-domain')

class WorkflowInterface:
    """An object that exposes a number of Events that user interface 
       Widgets can use to access the functionality of this module.
       
       Obtain an instance of WorkflowInterface by merely instantiating it.

       **exposed events:**
       
        - take_task = Requests that the given task be reserved for the account currently logged in.
        - defer_task = Indicates that the current user will tend to the given task later.
        - go_to_task = Indicates that the current user is attending to a task previously deferred.
        - release_task = Releases the current task back into the que for other users to tend to.
    """
    events = ExposedNames()
    events.take_task = lambda i: Event(label=_('Take'), 
                                 action=Action(Task.reserve_for, ['task', 'party']),
                                 task=PersistedField(Task, required=True),
                                 party=CurrentUser())
    events.defer_task = lambda i: Event(label=_('Defer'))
    events.go_to_task = lambda i: Event(label=_('Go to'),
                                  task=PersistedField(Task, required=True),
                                  party=CurrentUser(),
                                  readable=Action(Task.is_reserved_for, ['task', 'party']))
    events.release_task = lambda i: Event(label=_('Release'),
                                    action=Action(Task.release, ['task']),
                                    task=PersistedField(Task, required=True),
                                    party=CurrentUser())



class DeferredAction(Base):
    """A DeferredAction implements something the system should do some time in the future. A DeferredAction 
       will be done once a number of Requirements are fulfilled. The `success_action` method of a
       DeferredAction contains the code that needs to be executed when all Requirements are fulfilled. If
       all Requirements are not fulfilled by the given `deadline` (a DateTime), the `deadline_action`
       is executed instead, before the DeferredAction is deleted.
       
       :keyword requirements: A list of :class:`Requirement` instances to be satisfied before `.success_action` can be executed.
       :keyword deadline: The DateTime by which `deadline_action` will be executed if all `requirements` are not fulfulled by that time.
    """
    __tablename__ = 'deferredaction'
    id = Column(Integer, primary_key=True)
    discriminator = Column('row_type', String(40))
    __mapper_args__ = {
        'polymorphic_identity': 'deferredaction',
        'polymorphic_on': discriminator
    }
    requirements = relationship('Requirement', 
                                secondary=Table('deferredaction_requirement', 
                                            Base.metadata,
                                            Column('deferredaction_id', Integer, 
                                               ForeignKey('deferredaction.id'), 
                                               primary_key=True),
                                            Column('requirement_id', Integer, 
                                               ForeignKey('requirement.id'), 
                                               primary_key=True)
                                ),
                                lazy='dynamic',
                                backref=backref('deferred_actions', lazy='dynamic'))

    deadline = Column(DateTime(), nullable=False)

    def success_action(self):
        """Override this method to supply the code that needs to execute upon all instances of :class:`Requirement` are fulfilled."""

    def deadline_action(self):
        """Override this method to supply the code that needs to execute once the DateTime limit has been reached, and 
           not all :class:`Requirement` have been fulfilled"""
        
    def requirement_fulfilled(self):
        unfulfilled_requirements = self.requirements.filter_by(fulfilled=False)
        if unfulfilled_requirements.count() == 0:
            self.success_action()
            self.expire()
    
    @classmethod
    def check_deadline(cls):
        now = datetime.datetime.now()
        for expired_deferred_action in Session.query(cls).filter(cls.deadline < now):
            expired_deferred_action.deadline_expired()
            
    def expire(self):
        for requirement in self.requirements.all():
            requirement.deferred_action_expired(self)
        Session.delete(self)
        
    def deadline_expired(self):
        self.expire()
        self.deadline_action()


class Requirement(Base):
    """Something that needs to be fulfilled before a :class:`DeferrredAction` can be completed. Programmers
       are required to create subclasses of Requirement that call `self.set_fulfulled()` somewhere in a
       method of the subclass in order to indicate that the Requirement is fulfilled.
    """
    __tablename__ = 'requirement'
    id = Column(Integer, primary_key=True)
    discriminator = Column('row_type', String(40))
    __mapper_args__ = {
        'polymorphic_identity': 'requirement',
        'polymorphic_on': discriminator
    }

    #deferred_actions (would like to declare it here)

    fulfilled = Column(Boolean, nullable=False, default=False)
    
    def set_fulfilled(self):
        self.fulfilled = True
        for action in self.deferred_actions:
            action.requirement_fulfilled()
        
    def deferred_action_expired(self, deferred_action):
        self.deferred_actions.remove(deferred_action)
        if self.deferred_actions.count() == 0:
            Session.delete(self)


class Queue(Base):
    """A first-in, first-out queue that is monitored by users for Tasks that the system indicated need to be done."""
    __tablename__ = 'queue'
    id = Column(Integer, primary_key=True)

    tasks = relationship('Task', backref='queue')
    name = Column(Unicode(120), nullable=False, unique=True, index=True)


class Task(Base):
    """A Task that the system needs a user to do. Programmers should create subclasses of Task
       implementing specific Tasks in a given problem domain.
       
       :keyword queue: The :class:`Queue` to which this Task is allocated.
       :keyword title: A title for this task.
    """
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    discriminator = Column('row_type', String(40))
    __mapper_args__ = {
        'polymorphic_identity': 'task',
        'polymorphic_on': discriminator
    }

    queue_id = Column(Integer, ForeignKey(Queue.id), nullable=True, index=True)
    #queue  (would like to declare it here)
    title = Column(UnicodeText, nullable=False)
    reserved_by_party_id = Column(Integer, ForeignKey(Party.id), index=True)
    reserved_by = relationship(Party)

    def is_available(self):
        return self.reserved_by is None

    def is_reserved_for(self, party):
        return party and (self.reserved_by is party)

    def is_reserved_for_current_party(self):
        from reahl.domain.systemaccountmodel import LoginSession    # To prevent circular dependency with systemaccountmodel
        current_account = LoginSession.for_current_session().account
        return current_account and self.is_reserved_for(current_account.owner)
        
    @secured( write_check=is_reserved_for_current_party )
    def release(self):
        self.reserved_by = None

    def may_be_reserved_by(self, party):
        return self.is_available()

    @secured( write_check=may_be_reserved_by )
    def reserve_for(self, party):
        self.reserved_by = party


class Inbox:
    """The inbox of a user monitors several Task Queues."""
    def __init__(self, queues):
        self.queues = queues

    def get_tasks(self):
        return Session.query(Task).join(Queue).filter(Queue.id.in_([q.id for q in self.queues])).all()
        
        




