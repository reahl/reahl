# Copyright 2009, 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""A basic framework for writing commandline utilities."""

from __future__ import unicode_literals
from __future__ import print_function
import sys
import os.path
import logging
import re
import subprocess
import os
import warnings

from optparse import OptionParser
import shlex


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
        def is_exe(fpath):
            return os.path.exists(fpath) and os.access(fpath, os.X_OK)

        def ext_candidates(fpath):
            for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
                yield fpath + ext
            yield fpath

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                for candidate in ext_candidates(exe_file):
                    if is_exe(candidate):
                        return candidate

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
    """This is the superclass of all Commands that a ReahlCommandline can perform.

    It provides a common place where optparse is invoked. New commands are implemented by subclassing
    this one and overriding its execute method. The class attributes can also be overridden to specify
    how the commandline should be parsed.
    """

    options = []
    keyword = 'not implemented'
    usage_args = ''

    def __init__(self, commandline):
        self.commandline = commandline
        self.parser = OptionParser()
        self.parser.set_usage('%s %s' % (os.path.basename(sys.argv[0]), '%s [options] %s' % (self.keyword, self.usage_args)))
        for (short_version, long_version, kwargs) in self.options:
            self.parser.add_option(short_version, long_version, **kwargs)

    def parse_commandline(self, line):
        options, args = self.parser.parse_args(shlex.split(line))
        self.verify_commandline(options, args)
        return options, args

    def do(self, line):
        try:
            options, args = self.parse_commandline(line)
            return self.execute(options, args)
        except SystemExit as ex:
            return ex.code

    def help(self):
        self.parser.print_help()

    def verify_commandline(self, options, args):
        pass

    def execute(self, options, args):
        pass


class ReahlCommandline(object):
    """A generic class for invoking commands on the commandline."""
    command_entry_point = None
    usage_string = '[options] <command> [command options]'
    args_re = '((-l|--loglevel) +[\w\+\-\'"\>]+)?'
    options = [('-l', '--loglevel', dict(dest='loglevel', default='WARNING',
                                         help='set log level to this'))]

    def __init__(self, options, config):
        self.options = options
        self.commands = config.commands

    @property
    def command_names(self):
        return [i.keyword for i in self.commands]

    def command_named(self, name):
        for i in self.commands:
            if i.keyword == name:
                return i(self)
        raise CommandNotFound(name)

    def print_usage(self, parser):
        print(parser.format_help(), file=sys.stderr)
        print('\nCommands: ( %s <command> --help for usage on a specific command)\n' % os.path.basename(sys.argv[0]), file=sys.stderr)
        max_len = max([len(command.keyword) for command in self.commands])
        format_template = '{0: <%s}\t{1}' % max_len
        for command in self.commands:
            print(format_template.format(command.keyword, command.__doc__), file=sys.stderr)
        print('', file=sys.stderr)

    @classmethod
    def execute_one(cls):
        """The entry point for running command from the commandline."""

        command, line, options, parser = cls.parse_commandline()
        return_code = None

        if command:
            commandline = cls(options)
            if command in ['-h', '--help']:
                commandline.print_usage(parser)
                return_code = -1
            else:
                return_code = commandline.execute_command(command, line, options, parser)
        return return_code

    def set_log_level(self, log_level):
        loglevel = getattr(logging, log_level)
        logging.getLogger('').setLevel(log_level)
        if getattr(logging, log_level, 0) <= logging.WARN:
            warnings.resetwarnings()
        logging.captureWarnings(True)
        
    def execute_command(self, command, line, options, parser):
        self.set_log_level(options.loglevel)
        if command in self.command_names:
            return self.command_named(command).do(line)
        self.print_usage(parser)
        return None

    @classmethod
    def parse_commandline(cls):
        parser = OptionParser(usage='%s %s' % (os.path.basename(sys.argv[0]), cls.usage_string))
        for (short_version, long_version, kwargs) in cls.options:
            parser.add_option(short_version, long_version, **kwargs)

        args_string = ' '.join(sys.argv[1:])
        args_match = re.match(cls.args_re, args_string)
        if args_match:
            initial_args = shlex.split(args_string[:args_match.end()])
            remaining_args = sys.argv[len(initial_args)+1:]
        else:
            parser.error('Could not parse commandline')

        options, args = parser.parse_args(initial_args)

        if not len(remaining_args) >= 1:
            return ('-h', None, options, parser)

        # Note: its necessary to quote parts before we join them, else " chars are nuked (if there were any)
        try:
            command, line = remaining_args[0], ' '.join(['\'%s\'' % i for i in remaining_args[1:]])
        except IndexError:
            parser.error('No commands specified, try %s --help for usage' % os.path.basename(sys.argv[0]))
        return command, line, options, parser


