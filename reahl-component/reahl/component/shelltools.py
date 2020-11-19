# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.

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

import sys
import os.path
import logging
import subprocess
import os
import collections
import argparse 
import shlex
import shutil
import textwrap
import inspect

from reahl.component.config import Configuration, EntryPointClassList
from reahl.component.exceptions import DomainException


class ExecutableNotInstalledException(Exception):
    def __init__(self, executable_name):
        self.executable_name = executable_name
    def __str__(self):
        return 'Executable not found: %s' % self.executable_name


class Executable:
    def __init__(self, name, verbose=False):
        self.name = name
        self.verbose = verbose

    @property
    def executable_file(self):
        return self.which(self.name)
        
    def which(self, program):
        #on windows os, some entrypoints installed in the virtualenv
        #need their full path(with extension) to be able to be used as a spawn command.
        #Python 3 now offers shutil.which() - see also http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
        executable = program
        if program == os.path.basename(program):
            executable = shutil.which(program)
        if executable:
            return executable
        raise ExecutableNotInstalledException(program)

    def execute(self, method, commandline_arguments, *args, **kwargs):
        if self.verbose:
            print(' '.join([self.executable_file]+commandline_arguments))
        return method([self.executable_file]+commandline_arguments, *args, **kwargs)

    def call(self, commandline_arguments, *args, **kwargs):
        return self.execute(subprocess.call, commandline_arguments, *args, **kwargs)
    def check_call(self, commandline_arguments, *args, **kwargs):
        return self.execute(subprocess.check_call, commandline_arguments, *args, **kwargs)
    def Popen(self, commandline_arguments, *args, **kwargs):
        return self.execute(subprocess.Popen, commandline_arguments, *args, **kwargs)
    def check_output(self, commandline_arguments, *args, **kwargs):
        return self.execute(subprocess.check_output, commandline_arguments, *args, **kwargs)

    def run(self, commandline_arguments, *args, **kwargs):
        return self.execute(subprocess.run, commandline_arguments, *args, **kwargs)

class CommandNotFound(Exception):
    pass


class Command:
    """This is the superclass of all Commands executed from the commandline.

    New commands are implemented by subclassing this one and overriding its 
    execute method. Override its `assemble` method to customise its commandline 
    arguments by adding arguments to its `self.parser` :class:`argparse.ArgumentParser`

    """
    keyword = 'not implemented'
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog=self.keyword, description=self.format_description())
        self.assemble()

    @classmethod
    def format_description(cls):
        return cls.__doc__

    def assemble(self):
        pass

    def parse_commandline(self, argv):
        args = self.parser.parse_args(args=argv)
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


class CompositeCommand(Command):
    def __init__(self):
        super().__init__()
        self.parser.epilog = '"%s help-commands" gives a list of available commands' % self.parser.prog

    def assemble(self):
        super().assemble()
        self.parser.add_argument('command', help='a command')
        self.parser.add_argument('command_args', nargs=argparse.REMAINDER)

    @property
    def commands(self):
        return []

    def command_named(self, name):
        for i in self.commands:
            if i.keyword == name:
                if inspect.isclass(i):
                    return i()
                else:
                    return i
        raise CommandNotFound(name)

    def parse_commandline(self, argv):
        args = super().parse_commandline(argv)
        if argv[1:] and argv[1] == '--':
            args.command_args.insert(0, '--')
        return args

    def execute(self, args):
        try:
            command = self.command_named(args.command)
        except CommandNotFound:
            out_stream = sys.stdout
            command_name = args.command
            if command_name != 'help-commands':
                out_stream = sys.stderr
                print('No such command: %s' % command_name, file=out_stream)
            self.print_help(out_stream)
            return 2
            
        return command.do(args.command_args)

    def print_help(self, out_stream):
        print(self.parser.format_help(), file=out_stream)
        print('\nCommands: ( %s <command> --help for usage on a specific command)\n' % os.path.basename(self.keyword), file=out_stream)
        max_len = max([len(command.keyword) for command in self.commands])
        for command in sorted(self.commands, key=lambda x: x.keyword):
            self.print_command(command.keyword, command.format_description(), max_len, out_stream)

    def print_command(self, keyword, description, max_len, out_stream):
        keyword_column = ('{0: <%s}  ' % max_len).format(keyword)
        width = shutil.get_terminal_size().columns or 80
        output = textwrap.fill(description, width=width, initial_indent=keyword_column, subsequent_indent=' '*(max_len+2))
        print(output, file=out_stream)
        
    
class ReahlCommandline(CompositeCommand):
    """Invoke reahl commands on the commandline."""
    keyword = os.path.basename(sys.argv[0])

    def __init__(self, config=None):
        self.config = config or ReahlCommandlineConfig()
        super().__init__()

    def assemble(self):
        super().assemble()
        self.parser.add_argument('-l', '--loglevel', default='WARNING', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], help='set log level to this')

    @property
    def commands(self):
        return self.config.commands[:]
        
    @classmethod
    def execute_one(cls):
        """The entry point for running command from the commandline."""
        try:
            result = cls().do(sys.argv[1:])
        except DomainException as ex:
            print('\nError: %s\n' % ex, file=sys.stderr)
            result = 1
        exit(result)

    @property
    def aliasses(self):
        return dict(collections.ChainMap(AliasFile.get_file(local=True).aliasses, AliasFile.get_file(local=False).aliasses))
        
    def set_log_level(self, log_level):
        log_level = getattr(logging, log_level)
        logging.getLogger('').setLevel(log_level)

    def execute(self, args):
        self.set_log_level(args.loglevel)

        if args.command in self.aliasses:
            return self.do(shlex.split(self.aliasses[args.command]))
        else:
            return super().execute(args)

    def print_help(self, out_stream):
        super().print_help(out_stream)

        if self.aliasses:
            max_len = max([len(alias_name) for alias_name in self.aliasses.keys()])
            print('\nAliasses:\n', file=out_stream)
            for name, value in sorted(self.aliasses.items(), key=lambda x: x[0]):
                self.print_command(name, '"%s"\n' % value, max_len, out_stream)
            print('\n', file=out_stream)
        else:
            print('\nNo Aliasses\n', file=out_stream)



class AddAlias(Command):
    """Adds an alias."""
    keyword = 'alias'
    def assemble(self):
        self.parser.add_argument('-l', '--local', action='store_true', dest='local',
                                 help='store the added alias in the current directory')
        self.parser.add_argument('alias', type=str,  help='what to call this alias')
        self.parser.add_argument('aliassed_command', nargs=argparse.REMAINDER,
                                 help='the command (and arguments) to remember')

    def execute(self, args):
        super().execute(args)
        alias_file = AliasFile.get_file(local=args.local)
        alias_file.add_alias(args.alias, ' '.join(args.aliassed_command))
        alias_file.write()
        return 0

class RemoveAlias(Command):
    """Removes an alias."""
    keyword = 'unalias'
    def assemble(self):
        self.parser.add_argument('-l', '--local', action='store_true', dest='local',
                                 help='store the added alias in the current directory')
        self.parser.add_argument('alias', type=str,  help='which alias to remove')

    def execute(self, args):
        super().execute(args)
        alias_file = AliasFile.get_file(local=args.local)
        if args.alias in alias_file.aliasses:
            alias_file.remove_alias(args.alias)
            alias_file.write()
            return 0
        else:
            print('No such alias: %s' % args.alias)
            return 1


class AliasFile:
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

    def remove_alias(self, name):
        del self.aliasses[name]

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
