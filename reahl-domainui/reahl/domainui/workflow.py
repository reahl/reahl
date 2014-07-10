# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""A User interface that allows a user to monitor tasks allocated to the user's queues and to complete those tasks.
"""

from __future__ import unicode_literals
from __future__ import print_function
from reahl.component.exceptions import ProgrammerError
from reahl.component.i18n import Translator
from reahl.component.decorators import deprecated
from reahl.sqlalchemysupport import PersistedField
from reahl.web.fw import UserInterface, UrlBoundView, WebExecutionContext, Detour, ViewPreCondition
from reahl.web.ui import P, Panel, Ul, Li, H, Form, Button

from reahl.workflowmodel import Inbox, Task, WorkflowInterface


_ = Translator('reahl-domainui')



class TaskBox(Li):
    def __init__(self, view, task):
        super(TaskBox, self).__init__(view)
        self.task = task
        self.add_child(P(view, text=self.task.title))
        form = self.add_child(Form(view, 'task_%s' % task.id))
        form.add_child(Button(form, self.user_interface.workflow_interface.events.take_task.with_arguments(task=self.task)))
        form.add_child(Button(form, self.user_interface.workflow_interface.events.go_to_task.with_arguments(task=self.task)))


class InboxWidget(Panel):
    def __init__(self, view, inbox):
        super(InboxWidget, self).__init__(view)
        self.add_child(H(view, 1, text=_('Inbox')))
        self.list = self.add_child(Ul(view))

        for task in inbox.get_tasks():
            self.list.add_child(TaskBox(view, task))


class TaskWidget(Panel):
    """The Widget used to display a particular :class:`reahl.workflowdomain.Task`.
    
       Programmers need to create a subclass of TaskWidget to display a particular
       Task, also written by the programmer. Such a Widget should display whatever
       a user needs to see to complete the Task, including the relevant Buttons
       for deferring, or releasing the Task.
       
       Register each of your TaskWidget subclasses in your .reahlproject file as a class
       on the entrypoint 'reahl.workflowui.task_widgets'. For example:
       
       .. code-block:: xml

        <export entrypoint="reahl.workflowui.task_widgets" 
                name="TaskWidget" 
                locator="reahl.domainui.workflow:TaskWidget"/>

    """
    @classmethod
    def displays(cls, task):
        """Override this method, and let it return True only if `cls` is the correct
           Widget for displaying the given `task` instance."""
        return task.__class__ is Task

    def __init__(self, view, task):
        super(TaskWidget, self).__init__(view)
        self.task = task
        self.add_child(P(view, text=self.task.title))
        form = self.add_child(Form(view, 'task_form'))
        form.add_child(Button(form, self.user_interface.workflow_interface.events.defer_task))
        form.add_child(Button(form, self.user_interface.workflow_interface.events.release_task.with_arguments(task=self.task)))


class TaskView(UrlBoundView):
    def assemble(self, task=None):
        widget_class = self.get_widget_class_for(task)
        self.set_slot('main_slot', widget_class.factory(task))
        self.title = 'Task %s' % (task.id)

    def get_widget_class_for(self, task):
        config = WebExecutionContext.get_context().config
        for widget_class in config.workflowui.task_widgets:
            if widget_class.displays(task):
                return widget_class
        raise ProgrammerError('no Widget found to display %s' % task)


class InboxUI(UserInterface):
    """A user-facing UserInterface for monitoring an :class:`reahl.systemaccountmodel.Inbox`. It allows
       a user to work on tasks.

       **Slots:**
         - main_slot: All UI elements are put into this Slot for any View in this UserInterface.
         
       **Views**
         Call :meth:`AccountUI.get_bookmark` passing one of these relative URLs as the `relative_url` kwarg
         in order to get a Bookmark for the View listed below:

         `/`
           The inbox itself.
    """
    def assemble(self, login_bookmark=None, get_queues=None):
        self.get_queues = get_queues
        self.web_session = WebExecutionContext.get_context().session 
        self.first_log_in = ViewPreCondition(self.web_session.is_logged_in, exception=Detour(login_bookmark))

        self.workflow_interface = WorkflowInterface()
        self.inbox = Inbox(self.get_queues())
        
        inbox_view_factory = self.define_view('/', title=_('Inbox'))
        inbox_view_factory.set_slot('main_slot', InboxWidget.factory(self.inbox))
        
        task_view_factory = self.define_view('/task', view_class=TaskView, task=PersistedField(Task, required=True))
        task_view_factory.add_precondition(self.first_log_in)
        inbox_view_factory.add_precondition(self.first_log_in)
        
        self.define_transition(self.workflow_interface.events.take_task, inbox_view_factory, task_view_factory)
        self.define_transition(self.workflow_interface.events.go_to_task, inbox_view_factory, task_view_factory)
        self.define_transition(self.workflow_interface.events.defer_task, task_view_factory, inbox_view_factory)
        self.define_transition(self.workflow_interface.events.release_task, task_view_factory, inbox_view_factory)



@deprecated('Please use InboxUI instead.')
class InboxRegion(InboxUI):
    pass











