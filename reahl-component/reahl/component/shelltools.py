# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.

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

"""A basic framework for writing commandline utilities."""

from __future__ import print_function, unicode_literals, absolute_import, division
import sys
import os.path
import logging
import re
import subprocess
import os
import distutils
import collections
import argparse 
import shlex

from reahl.component.config import Configuration, EntryPointClassList

class ExecutableNotInstalledException(Exception):
    def __init__(self, executable_name):
        self.executable_name = executable_name
    def __str__(self):
        return 'Executable not found: %s' % self.executable_name


class Executable(object):
    def __init__(self, name):
        self.name = name

    @property
    def executable_file(self):
        return self.which(self.name)
        
    def which(self, program):
        #on windows os, some entrypoints installed in the virtualenv
        #need their full path(with extension) to be able to be used as a spawn command.
        #Python 3 now offers shutil.which() - see also http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
        executable = distutils.spawn.find_executable(program)
        if executable:
            return executable
        raise ExecutableNotInstalledException(program)

    def call(self, commandline_arguments, *args, **kwargs):
        return subprocess.call([self.executable_file]+commandline_arguments, *args, **kwargs)
    def check_call(self, commandline_arguments, *args, **kwargs):
        return subprocess.check_call([self.executable_file]+commandline_arguments, *args, **kwargs)
    def Popen(self, commandline_arguments, *args, **kwargs):
        return subprocess.Popen([self.executable_file]+commandline_arguments, *args, **kwargs)


class CommandNotFound(Exception):
    pass


class Command(object):
    """This is the superclass of all Commands executed from the commandline.

    New commands are implemented by subclassing this one and overriding its 
    execute method. Override its `assemble` method to customise its commandline 
    arguments by adding arguments to its `self.parser` :class:`argparse.ArgumentParser`

    """
    keyword = 'not implemented'
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog=self.keyword, description=self.__doc__)
        self.assemble()

    def assemble(self):
        pass

    def parse_commandline(self, argv):
        args = self.parser.parse_args(argv)
        self.verify_commandline(args)
        return args

    def do(self, argv):
        try:
            args = self.parse_commandline(argv)
            return self.execute(args)
        except SystemExit as ex:
            return ex.code

    def help(self):
        self.parser.print_help()

    def verify_commandline(self, args):
        pass

    def execute(self, args):
        pass

    
class ReahlCommandlineConfig(Configuration):
    commands = EntryPointClassList('reahl.component.commands', description='The commands (classes) available to the commandline shell')


class ReahlCommandline(Command):
    """Invoke reahl commands on the commandline."""
    keyword = 'reahl'

    def __init__(self, prog=sys.argv[0], config=None):
        super(ReahlCommandline, self).__init__()
        config = config or ReahlCommandlineConfig()
        self.commands = config.commands[:]
        self.keyword = prog

    def assemble(self):
        self.parser.add_argument('-l', '--loglevel', default='WARNING', help='set log level to this')
        self.parser.add_argument('command', type=str,  help='a command')
        self.parser.add_argument('command_args', nargs=argparse.REMAINDER)

    @classmethod
    def execute_one(cls):
        """The entry point for running command from the commandline."""
        return cls(sys.argv[0]).do(sys.argv[1:])
        
    @property
    def aliasses(self):
        return dict(collections.ChainMap(AliasFile.get_file(local=True).aliasses, AliasFile.get_file(local=False).aliasses))
        
    @property
    def command_names(self):
        return [i.keyword for i in self.commands]

    def command_named(self, name):
        for i in self.commands:
            if i.keyword == name:
                return i()
        raise CommandNotFound(name)

    def set_log_level(self, log_level):
        log_level = getattr(logging, log_level)
        logging.getLogger('').setLevel(log_level)

    def execute(self, args):
        self.set_log_level(args.loglevel)

        if args.command in self.command_names:
            return self.command_named(args.command).do(args.command_args)
        elif args.command in self.aliasses:
            return self.do(shlex.split(self.aliasses[args.command]))
        else:
            print('No such command: %s' % args.command, file=sys.stderr)
            self.print_help()
            return -1
            
    def print_help(self):
        print(self.parser.format_help(), file=sys.stderr)
        print('\nCommands: ( %s <command> --help for usage on a specific command)\n' % os.path.basename(sys.argv[0]), file=sys.stderr)
        max_len = max([len(command.keyword) for command in self.commands])
        format_template = '{0: <%s}\t{1}' % max_len
        for command in sorted(self.commands, key=lambda x: x.keyword):
            print(format_template.format(command.keyword, command.__doc__), file=sys.stderr)

        print('\nAliasses:\n')
        for name, value in sorted(self.aliasses.items(), key=lambda x: x[0]):
            print(format_template.format(name, '"%s"' % value), file=sys.stderr)
        print('', file=sys.stderr)

        
class AddAlias(Command):
    """Adds an alias."""
    keyword = 'addalias'
    options = [('-l', '--local', dict(action='store_true', dest='local', help='store the added alias in the current directory'))]
    def assemble(self):
        self.parser.add_argument('-l', '--local', action='store_true', dest='local', help='store the added alias in the current directory')
        self.parser.add_argument('alias', type=str,  help='what to call this alias')
        self.parser.add_argument('aliassed_command', nargs=argparse.REMAINDER, help='the command (and arguments) to remember')

    def execute(self, args):
        super(AddAlias, self).execute(args)
        alias_file = AliasFile.get_file(local=args.local)
        alias_file.add_alias(args.alias, ' '.join(args.aliassed_command))
        alias_file.write()
        return 0

    
class AliasFile(object):
    @classmethod
    def get_file(cls, local=False):
        filename = '.reahlalias' if local else os.path.expanduser('~/.reahlalias')
        alias_file = cls(filename)
        if alias_file.exists:
            alias_file.read()
        return alias_file
    
    def __init__(self, filename):
        self.filename = filename
        self.aliasses = {}

    def add_alias(self, name, value):
        self.aliasses[name] = value

    @property
    def exists(self):
        return os.path.isfile(self.filename)
    
    def read(self):
        for line in open(self.filename, 'r'):
            line = line.strip()
            if line:
                alias_name = line.split(' ')[0]
                alias_value = ' '.join(line.split(' ')[1:])
                self.aliasses[alias_name] = alias_value

    def write(self):
        with open(self.filename, 'w', encoding='utf-8') as open_file:
            for alias_name, alias_value in self.aliasses.items():
                open_file.write('%s %s\n' % (alias_name, alias_value))
