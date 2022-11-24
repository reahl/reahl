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


import inspect
from reahl.component.decorators import  deprecated, memoized


try:
    import contextvars
    execution_context_var = contextvars.ContextVar('reahl.component.context.ExecutionContext')
except:
    execution_context_var = None


class NoContextFound(Exception):
    pass




class ExecutionContext:
    """Most code execute "in the scope of" some ExecutionContext. Such code can obtain
       the current ExecutionContext by calling ExecutionContext.get_context. The ExecutionContext
       of code comprises of: the current Configuration for all components, the current UserSession,
       and a SystemControl.
    
       .. attribute:: config
       
       .. attribute:: session
       
       .. attribute:: system_control
    """
    use_context_var = False
    
    @classmethod
    def for_config_directory(cls, config_directory):
        from reahl.component.config import StoredConfiguration # Here, to avoid circular dependency
        
        config = StoredConfiguration(config_directory)
        config.configure()
        new_context = cls()
        new_context.config = config
        return new_context

    @classmethod
    def get_context_id(cls):
        """Returns a unique, hashable identifier identifying the current call context."""
        return cls.get_context().id


    @classmethod
    def get_context(cls):
        """Returns the current call context, or raises :class:`NoContextFound` if there is none."""
        if not cls.use_context_var:
            return cls.get_context_using_frames()
        try:
            context = execution_context_var.get()
        except LookupError:
            context = None
        if not context:
            raise NoContextFound('No %s is active in the call stack' % cls)

        return context

    @classmethod
    def get_context_using_frames(cls):
        """Returns the current call context, or raises :class:`NoContextFound` if there is none."""
        context = None
        f = inspect.currentframe()
        while (not context) and f:
            context = f.f_locals.get('__reahl_context__', None)
            to_delete = f
            f = f.f_back
            del to_delete
        if not context:
            raise NoContextFound('No %s is active in the call stack' % cls)
        return context

    def __init__(self, name=None, parent_context=None):
        self.name = name
        try:
            self.parent_context = parent_context or self.get_context()
        except NoContextFound:
            self.parent_context = None
        self.id = (self.parent_context.id if isinstance(self.parent_context, ExecutionContext) else id(self))

    def copy(self):
        context = self.__class__(name='ExecutionContext.copy()', parent_context=self)
        for name in self.__dict__:
            if name not in ['id', 'name','parent_context']:
                context.__setattr__(name, self.__dict__[name])
        return context

    def __enter__(self):
        self.install_with_context_vars_or_frames()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.uninstall()

    def install_with_context_vars_or_frames(self, stop=None):
        if not self.use_context_var:
            return self.install_using_frames(stop=stop)
        try:
            if execution_context_var.get() == self:
                raise Exception('Context already installed')
        except LookupError:
            pass
        self.ctx_token = execution_context_var.set(self)
        return self


    @deprecated('Use `with ExecutionContext(): ...` instead, in order to exit the context explicitly as well.', '6.1')
    def install(self, stop=None):
        """Installs the ExecutionContext in the current scope so that it will be found by code called after it is installed.

           .. versionchanged:: 6.1
              Deprecated install. Use ExecutionContext as ContextManager instead.

        """
        return self.install_with_context_vars_or_frames(stop=stop)

    def uninstall(self):
        if not self.use_context_var:
            return
        execution_context_var.reset(self.ctx_token)

    def install_using_frames(self, stop=None):
        f = inspect.currentframe()
        if not stop:
            def stop(ff):
                return not isinstance(ff.f_locals.get('self', None), ExecutionContext)
        while not stop(f):
            calling_frame = f.f_back
            del f
            f = calling_frame
        calling_frame.f_locals['__reahl_context__'] = self
        del calling_frame
        return self

    @property
    @memoized
    def interface_locale(self):
        """Returns a string identifying the current locale."""
        session = getattr(self, 'session', None)
        if not session:
            return 'en_gb'
        return self.session.get_interface_locale()

    def __getattr__(self, name):
        raise AttributeError('%s has no attribute \'%s\'' % (self, name))

    def __str__(self):
        if self.name:
            return '%s named \'%s\'' % (self.__class__.__name__, self.name)
        return super().__str__()

        
