# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""The module contains code to implement commands that can be issued from a commandline to manipulate Reahl projects."""
from __future__ import unicode_literals
from __future__ import with_statement

from __future__ import print_function
import six
import sys
import os
import os.path
import subprocess
from subprocess import CalledProcessError
import traceback


import shlex

from reahl.component.shelltools import Command, ReahlCommandline, Executable
from reahl.component.config import EntryPointClassList, Configuration

from reahl.dev.devdomain import Workspace, Project, ProjectList, ProjectNotFound, LocalAptRepository
from reahl.dev.exceptions import StatusException, AlreadyUploadedException, NotBuiltException, \
    NotUploadedException, NotVersionedException, NotCheckedInException, \
    MetaInformationNotAvailableException, AlreadyDebianisedException, \
    MetaInformationNotReadableException, UnchangedException, NeedsNewVersionException, \
    AlreadyMarkedAsReleasedException, NotBuiltAfterLastCommitException, NotBuiltException, \
    NotAValidProjectException
from functools import reduce


class DevShellConfig(Configuration):
    commands = EntryPointClassList('reahl.dev.commands', description='All commands (classes) that can be handled by the development shell')

    
class WorkspaceCommand(Command):
    """A specialised form of Command which is used in development. Its operations are assumed to often involve
    the development workspace.
    """

    def __init__(self, commandline):
        super(WorkspaceCommand, self).__init__(commandline)

        if 'REAHLWORKSPACE' in os.environ:
            workspace_dir = os.environ['REAHLWORKSPACE']
        else:
            workspace_dir = os.path.expanduser('~')
            print('REAHLWORKSPACE environment variable not set, defaulting to %s' % workspace_dir, file=sys.stderr)

        work_directory = os.path.abspath(os.path.expanduser(workspace_dir))
        self.workspace = Workspace(workspace_dir)
        self.workspace.read()


class Refresh(WorkspaceCommand):
    """Reconstructs the working set of projects by searching through the given directories (by default the entire workspace directory)."""
    keyword = 'refresh'
    usage_args = '[directory...]'
    options = [('-A', '--append', dict(action='store_true', dest='append', 
                                       help='append to the current working set'))]
    def execute(self, options, args):
        self.workspace.refresh(options.append, args)


class ExplainLegend(WorkspaceCommand):
    """Prints an explanation of project status indicators."""
    keyword = 'explainlegend'
    def execute(self, options, args):
        for status in StatusException.get_statusses():
            print('%s\t%s' % (status.legend, six.text_type(status())))


class Select(WorkspaceCommand):
    """Selects a subset of projects in the workspace based on their state."""
    keyword = 'select'
    options = [('-a', '--all', dict(action='store_true', dest='all', 
                                    help='operate on all projects in the workspace')),
               ('-A', '--append', dict(action='store_true', dest='append', 
                                    help='append to the current selection')),
               ('-s', '--state', dict(action='append', dest='states', default=[],
                                      help='operate on projects with given state')),
               ('-n', '--not', dict(action='store_true', dest='negated', 
                                    help='negates a state selection')),
               ('-t', '--tagged', dict(action='append', dest='tags', default=[],
                                       help='operate on projects tagged as specified'))]

    def execute(self, options, args):
        self.workspace.select(states=options.states, tags=options.tags, append=options.append, all_=options.all, negated=options.negated)


class ClearSelection(WorkspaceCommand):
    """Clears the current selection."""
    keyword = 'clearselection'

    def execute(self, options, args):
        self.workspace.clear_selection()


class ListSelections(WorkspaceCommand):
    """Lists all the named sets of selections that have been saved previously."""
    keyword = 'selections'
    def execute(self, options, args):
        for i in self.workspace.get_saved_selections():
            print(i)


class List(WorkspaceCommand):
    """Lists all the projects currently selected (or, optionally, all projects in the workspace)"""
    keyword = 'list'
    options = [('-s', '--state', dict(action='store_true', dest='with_status',
                                      help='outputs the status too')),
               ('-a', '--all', dict(action='store_true', dest='all',
                                      help='lists all, not only selection')),
               ('-d', '--directories', dict(action='store_true', dest='directories',
                                      help='lists relative directory names instead of project names'))]
    def execute(self, options, args):
        if options.all:
            project_list = self.workspace.projects
        else:
            project_list = self.workspace.selection

        for i in project_list:
            status_string = ''
            if options.with_status:
                status_string = '%s ' % i.status

            if options.directories:
                ident_string = i.relative_directory
            else:
                ident_string = i.project_name
            print('%s%s' % (status_string, ident_string))


class Save(WorkspaceCommand):
    """Saves the current selection of projects using the given name."""
    keyword = 'save'
    usage_args = '<name>'
    def execute(self, options, args):
        self.workspace.save_selection(args[0])


class DeleteSelection(WorkspaceCommand):
    """Deletes the saved selection set with the given name."""
    keyword = 'delete'
    usage_args = '<name>'
    def execute(self, options, args):
        self.workspace.delete_selection(args[0])


class Read(WorkspaceCommand):
    """Changes the current selection to the named, previously saved selection."""
    keyword = 'read'
    usage_args = '<name>'
    def execute(self, options, args):
        self.workspace.read_selection(args[0])


class ForAllWorkspaceCommand(WorkspaceCommand):
    """Some commands are executed in turn for each project in the selection. This superclass encapsulates some
       common implementation details for such commands."""

    options = [('-s', '--selection', dict(action='store_true', dest='selection', default=False,
                                          help='operate on all projects in the current selection')),
               ('-a', '--all', dict(action='store_true', dest='all', 
                                    help='operate on all projects in the workspace')),
               ('-S', '--state', dict(action='append', dest='states', default=[],
                                      help='operate on projects with given state')),
               ('-n', '--not', dict(action='store_true', dest='negated', 
                                    help='negates a state selection')),
               ('-t', '--tagged', dict(action='append', dest='tags', default=[],
                                       help='operate on projects tagged as specified')),
               ('-p', '--pause', dict(action='store_true', dest='pause',
                                      help='pause between commands')),
               ('-X', '--summary', dict(action='store_true', dest='summary',
                                      help='prints summary at end')),
               ('-d', '--delimit-output', dict(action='store_true', dest='delimit_output',
                                      help='prints starting and ending markers around the output of each project'))]
    def function(self, project, options, args):
        return None

    def verify_commandline(self, options, args):
        count = reduce(lambda a,b: a+1 if b else a, [options.selection, options.all, options.negated], 0)
        if count > 1:
            self.parser.error('Cannot use -S, -a or -n together')

        if (options.selection or options.all) and (options.states or options.tags or options.negated):
            self.parser.error('Cannot use -s or -a with -n, -S or -t')


    def execute_one(self, project, options, args):
        with project.paths_set():
            try:
                retcode = self.function(project, options, args)
            except SystemExit as ex:
                print('Script exited: %s' % ex, file=sys.stderr)
                retcode = ex.code
            except OSError as ex:
                print('Execution failed: %s' % ex, file=sys.stderr)
                retcode = ex.errno
            except (NotVersionedException, NotCheckedInException, MetaInformationNotAvailableException, AlreadyDebianisedException,
                    MetaInformationNotReadableException, UnchangedException, NeedsNewVersionException,
                    NotUploadedException, AlreadyMarkedAsReleasedException,
                    AlreadyUploadedException, NotBuiltException, 
                    NotBuiltAfterLastCommitException, NotBuiltException) as ex:
                print(six.text_type(ex), file=sys.stderr)
                retcode = None
            except CalledProcessError as ex:
                print(six.text_type(ex), file=sys.stderr)
                retcode = ex.returncode
          
        if retcode != None:
            if isinstance(retcode, six.string_types):
                print('Child was terminated with error message: %s' % retcode, file=sys.stderr)
            elif retcode < 0:
                print('Child was terminated by signal %s' % -retcode, file=sys.stderr)
            elif retcode > 0:
                print('Child returned %s' % -retcode, file=sys.stderr)

        return retcode

    def execute(self, options, args):
        if options.states or options.tags:
            project_list = self.workspace.get_selection_subset(states=options.states, tags=options.tags, append=False, all_=options.all, negated=options.negated)
        elif options.selection:
            project_list = self.workspace.selection
        else:
            project_list = ProjectList(self.workspace)
            try:
                current_project = self.workspace.project_in(os.getcwd())
            except ProjectNotFound:
                try:
                    current_project = Project.from_file(self.workspace, os.getcwd())
                except NotAValidProjectException:
                    current_project = Project(self.workspace, os.getcwd())
            project_list.append(current_project)

        pause = options.pause
        summary = options.summary
        delimit_output = options.delimit_output

        results = {}
        for i in project_list:
            if delimit_output:
                print('\n--- START %s %s ---' % (i.relative_directory, ' '.join(args)))
            results[i] = self.execute_one(i, options, args)
            if pause:
                print('--- PAUSED, hit <enter> to continue, ^D to stop ---')
                if not sys.stdin.readline():
                    print('\n^D pressed, halting immediately')
                    break
            if delimit_output:
                print('--- END %s %s ---' % (i.relative_directory, ' '.join(args)))

        if summary:
            print('\n--- SUMMARY ---')
            for i in project_list:
                print('%s %s' % (results[i], i.relative_directory), file=sys.stdout)

        self.perform_post_command_duties()

        if set(results.values()) == {0}:
            return 0
        return -1

    def perform_post_command_duties(self):
        pass


class AliasWorkspaceCommand(ForAllWorkspaceCommand):
    def __init__(self, commandline, keyword):
        super(AliasWorkspaceCommand, self).__init__(commandline)
        self.keyword = keyword
        self.failures = []

    def function(self, project, options, args):
        full_command = project.command_aliases.get(self.keyword, None)
        if not full_command:
            self.failures.append(project)
            return -1
        command = self.commandline.command_named(full_command[0])
        dash_index = full_command.index('--')
        return command.execute_one(project, options, full_command[dash_index+1:]+args) 
        

class Debianise(ForAllWorkspaceCommand):
    """Debianises a project."""
    keyword = 'debianise'
    def function(self, project, options, args):
        assert hasattr(project.metadata, 'debianise'), \
               'This command is only valid on debian-based projects (with <metadata type="debian"/>)'
        project.metadata.debianise()
        return 0


class Info(ForAllWorkspaceCommand):
    """Prints information about a project."""
    keyword = 'info'
    def print_heading(self, heading):
        print('')
        print(heading)
        print('\t'+('-'*(len(heading)+6)))

    def function(self, main_project, options, args):
        projects = [main_project]
        if main_project.has_children:
            projects = main_project.egg_projects

        for project in projects:
            self.print_heading('\tProject:\t%s' % project.directory)
            print('\tIs version controlled?:\t%s' % project.is_version_controlled())
            print('\tLast commit:\t\t%s' % project.source_control.last_commit_time)
            print('\tUnchanged?:\t\t%s' % project.is_unchanged())
            print('\tNeeds new version?:\t%s' % project.needs_new_version())
            print('\tIs checked in?:\t\t%s' % project.is_checked_in())

        self.print_heading('\tProject:\t%s' % main_project.directory)
        self.print_heading('\tPackages to distribute:')
        for package in main_project.packages_to_distribute:
            print('\t%s' % six.text_type(package))


class ForAllParsedWorkspaceCommand(ForAllWorkspaceCommand):
    """Some commands, for example an arbitrary shell command, are not directly implemented here.  Rather, they are
    passed on to some other processing unit, such as the shell.  They are in fact embedded in the command given to the
    reahl commandline processor whose only function is to make sure the same command is executed on each project
    in the selection.

    This superclass contains common implementation details for parsing such commands that are in fact embedded inside
    another commandline.  Optparse cannot directly parse such composite lines.
    """
    def __init__(self, commandline):
        super(ForAllParsedWorkspaceCommand, self).__init__(commandline)
        self.saved_args = None

    def parse_commandline(self, line):
        split_line = shlex.split(line)
        if '--' in split_line:
            separator = split_line.index('--')
            extracted_line = ' '.join(split_line[:separator])
            self.saved_args = split_line[separator+1:] # Saved for use in execute later
        else:
            extracted_line = line
            self.saved_args = []

        return super(ForAllParsedWorkspaceCommand, self).parse_commandline(extracted_line)

    def execute(self, options, args):
        return super(ForAllParsedWorkspaceCommand, self).execute(options, self.saved_args)


class Shell(ForAllParsedWorkspaceCommand):
    """Executes a shell command in each selected project, from each project's own root directory."""
    keyword = 'shell'
    usage_args = '-- <shell_command> [shell_command_options]'
    def function(self, project, options, args):
        if not args:
            print('No shell command specified to run', file=sys.stderr)
            return 1
        replaced_command = []
        for i in args:
            if i.startswith('$(') and i.endswith(')'):
                shellcommand = i[2]
                shell_args = i[3:-1].split(' ')
                output = Executable(shellcommand).Popen(shell_args, cwd=project.directory, stdout=subprocess.PIPE).communicate()[0]
                for line in output.splitlines():
                    replaced_command.append(line)
            else:
                replaced_command.append(i)

        command = replaced_command

        return Executable(command[0]).call(command[1:], cwd=project.directory)



class Setup(ForAllParsedWorkspaceCommand):
    """Runs setup.py <command> for each project in the current selection."""
    keyword = 'setup'
    usage_args = '-- <setup_command> [setup_command_options]'
    def function(self, project, options, args):
        project.setup(args)
        return 0


class Build(ForAllWorkspaceCommand):
    """Builds all distributable packages for each project in the current selection."""
    keyword = 'build'
    def function(self, project, options, args):
        try:
            return_code = project.build()
        except:
            print('', file=sys.stderr)
            traceback.print_exc()
            return_code = -1

        return return_code

    def perform_post_command_duties(self):
        self.workspace.update_apt_repository_index()


class ListMissingDependencies(ForAllWorkspaceCommand):
    """Lists all missing thirdparty dependencies for each project in the current selection."""
    keyword = 'missingdeps'
    options = ForAllWorkspaceCommand.options+[('-D', '--development', dict(action='store_true', dest='for_development', default=False,
                                                                           help='include development dependencies'))]
    def function(self, project, options, args):
        return_code = 0
        try:
            dependencies = project.list_missing_dependencies(for_development=options.for_development)
            if dependencies:
                print(' '.join(dependencies))
        except:
            traceback.print_exc()
            return_code = -1

        return return_code


class DebInstall(ForAllParsedWorkspaceCommand):
    """Runs setup.py install with correct arguments for packaging the result in a deb (for each project in the selection)."""
    keyword = 'debinstall'
    def function(self, project, options, args):
        project.debinstall(args)
        return 0


class Upload(ForAllWorkspaceCommand):
    """Uploads all built distributable packages for each project in the current selection."""
    keyword = 'upload'
    options = ForAllWorkspaceCommand.options+[('-k', '--knock', dict(action='append', dest='knocks', default=[],
                                                                     help='port to knock on before uploading'))]
    def function(self, project, options, args):
        return project.upload(knocks=options.knocks)


class MarkReleased(ForAllWorkspaceCommand):
    """Marks each project in the current selection as released."""
    keyword = 'markreleased'
    def function(self, project, options, args):
        return project.mark_as_released()


class SubstVars(ForAllWorkspaceCommand):
    """Generates debian substvars."""
    keyword = 'substvars'
    def function(self, project, options, args):
        assert hasattr(project.metadata, 'generate_deb_substvars'), \
               'This command is only valid on debian-based projects (with <metadata type="debian"/>)'
        project.metadata.generate_deb_substvars()
        return 0


class UpdateAptRepository(WorkspaceCommand):
    """Updates the index files of the given apt repository."""
    keyword = 'updateapt'
    usage_args = '<root_directory>'
    def execute(self, options, args):
        root_directory = None
        if args:
            root_directory = args[0]
        else:
            raise Exception('No root_directory specified')

        if not os.path.isdir( root_directory ):
            message = '"%s" is not a valid directory from within %s' % (root_directory, os.getcwd())
            raise Exception(message)

        repository = LocalAptRepository( root_directory )
        repository.build_index_files()


class ExtractMessages(ForAllWorkspaceCommand):
    """Collects strings marked for translation."""
    keyword = 'extractmessages'
    def function(self, project, options, args):
        project.extract_messages(args)
        return 0


class MergeTranslations(ForAllWorkspaceCommand):
    """Merges newly discovered strings needing translation with a catalog of existing translations."""
    keyword = 'mergetranslations'
    def function(self, project, options, args):
        project.merge_translations()
        return 0


class CompileTranslations(ForAllWorkspaceCommand):
    """Compiles all current translations."""
    keyword = 'compiletranslations'
    def function(self, project, options, args):
        project.compile_translations()
        return 0


class AddLocale(ForAllWorkspaceCommand):
    """Adds a new locale catalog."""
    keyword = 'addlocale'
    usage_args = '<locale_string> [translated_egg]'
    def function(self, project, options, args):
        if len(args) < 1:
            self.parser.error('At least a locale_string should be given')

        locale = args[0]
        translated_egg = locale
        if len(args) >= 2:
            translated_egg = args[1]

        project.add_locale(locale, translated_egg)
        return 0


class WorkspaceCommandline(ReahlCommandline):
    """The main class for invoking commands on the commandline of a development Workspace."""
    usage_string = '[options] <command> [command options] [-- [command_argument...]]'
    def __init__(self, options):
        super(WorkspaceCommandline, self).__init__(options, DevShellConfig())

    def execute_command(self, command, line, options, parser):
        self.set_log_level(options.loglevel)
        if command in self.command_names:
            return self.command_named(command).do(line)

        alias_command = AliasWorkspaceCommand(self, command)
        retcode = alias_command.do(line)
        if alias_command.failures:
            print('\nThere is no command named %s\nAlso, no aliases found for it in project(s):\n' % command, file=sys.stderr)
            print(', '.join([i.project_name for i in alias_command.failures]), file=sys.stderr)
            self.print_usage(parser)
            retcode = -1
        return retcode




