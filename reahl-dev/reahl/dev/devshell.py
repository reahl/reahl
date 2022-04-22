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

"""The module contains code to implement commands that can be issued from a commandline to manipulate Reahl projects."""
import sys
import os
import re
import os.path
import subprocess
import shutil
import argparse
from subprocess import CalledProcessError
from contextlib import contextmanager
import traceback

from reahl.component.shelltools import Command, Executable

from reahl.dev.devdomain import Workspace, Project, ProjectList, ProjectNotFound, LocalAptRepository, SetupCommandFailed
from reahl.dev.exceptions import StatusException, AlreadyUploadedException, \
    NotUploadedException, NotVersionedException, NotCheckedInException, \
    MetaInformationNotAvailableException, AlreadyDebianisedException, \
    MetaInformationNotReadableException, UnchangedException, NeedsNewVersionException, \
    AlreadyMarkedAsReleasedException, NotBuiltAfterLastCommitException, NotBuiltException, \
    NotAValidProjectException
from functools import reduce


class WorkspaceCommand(Command):
    """A specialised form of Command which is used in development. Its operations are assumed to often involve
    the development workspace.
    """

    def __init__(self):
        if 'REAHLWORKSPACE' in os.environ:
            workspace_dir = os.environ['REAHLWORKSPACE']
        else:
            workspace_dir = os.path.expanduser('~')
            print('REAHLWORKSPACE environment variable not set, defaulting to %s' % workspace_dir, file=sys.stderr)

        work_directory = os.path.abspath(os.path.expanduser(workspace_dir))
        self.workspace = Workspace(work_directory)
        self.workspace.read()

        super().__init__()


class Refresh(WorkspaceCommand):
    """Reconstructs the working set of projects by searching through the given directories (by default the entire workspace directory)."""
    keyword = 'refresh'
    usage_args = '[directory...]'

    def assemble(self):
        super().assemble()
        self.parser.add_argument('-A', '--append', action='store_true', dest='append',
                                 help='append to the current working set')
        self.parser.add_argument('directories', nargs='*', help='search for projects specifically in these directories (if not given, search in %s)' % self.workspace.directory)

    def execute(self, args):
        self.workspace.refresh(args.append, args.directories)


class ExplainLegend(WorkspaceCommand):
    """Prints an explanation of project status indicators."""
    keyword = 'explainlegend'
    def execute(self, args):
        for status in StatusException.get_statusses():
            print('%s\t%s' % (status.legend, str(status())))


class Select(WorkspaceCommand):
    """Selects a subset of projects in the workspace based on their state."""
    keyword = 'select'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('-a', '--all', action='store_true', dest='all',
                                 help='operate on all projects in the workspace')
        self.parser.add_argument('-A', '--append', action='store_true', dest='append',
                                 help='append to the current selection')
        self.parser.add_argument('-s', '--state', action='append', dest='states', default=[],
                                 help='operate on projects with given state')
        self.parser.add_argument('-n', '--not', action='store_true', dest='negated',
                                 help='negates a state selection')
        self.parser.add_argument('-t', '--tagged', action='append', dest='tags', default=[],
                                 help='operate on projects tagged as specified')

    def execute(self, args):
        self.workspace.select(states=args.states, tags=args.tags, append=args.append, all_=args.all, negated=args.negated)


class ClearSelection(WorkspaceCommand):
    """Clears the current selection."""
    keyword = 'clearselection'

    def execute(self, args):
        self.workspace.clear_selection()


class ListSelections(WorkspaceCommand):
    """Lists all the named sets of selections that have been saved previously."""
    keyword = 'selections'
    def execute(self, args):
        for i in self.workspace.get_saved_selections():
            print(i)


class List(WorkspaceCommand):
    """Lists all the projects currently selected (or, optionally, all projects in the workspace)"""
    keyword = 'list'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('-s', '--state', action='store_true', dest='with_status',
                                 help='outputs the status too')
        self.parser.add_argument('-a', '--all', action='store_true', dest='all',
                                 help='lists all, not only selection')
        self.parser.add_argument('-d', '--directories', action='store_true', dest='directories',
                                 help='lists relative directory names instead of project names')

    def execute(self, args):
        if args.all:
            project_list = self.workspace.projects
        else:
            project_list = self.workspace.selection

        for i in project_list:
            status_string = ''
            if args.with_status:
                status_string = '%s ' % i.status

            if args.directories:
                ident_string = i.relative_directory
            else:
                ident_string = i.project_name
            print('%s%s' % (status_string, ident_string))


class Save(WorkspaceCommand):
    """Saves the current selection of projects using the given name."""
    keyword = 'save'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('selection_name', help='a name for the saved selection')
        
    def execute(self, args):
        self.workspace.save_selection(args.selection_name)


class DeleteSelection(WorkspaceCommand):
    """Deletes the saved selection set with the given name."""
    keyword = 'delete'
    usage_args = '<name>'
    def execute(self, args):
        self.workspace.delete_selection(args[0])


class Read(WorkspaceCommand):
    """Changes the current selection to the named, previously saved selection."""
    keyword = 'read'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('selection_name', help='the name of the selection to read')

    def execute(self, args):
        self.workspace.read_selection(args.selection_name)


class ForAllWorkspaceCommand(WorkspaceCommand):
    """Some commands are executed in turn for each project in the selection. This superclass encapsulates some
       common implementation details for such commands."""
    def assemble(self):
        super().assemble()
        self.parser.add_argument('-s', '--selection', action='store_true', dest='selection', default=False,
                                 help='operate on all projects in the current selection')
        self.parser.add_argument('-a', '--all', action='store_true', dest='all',
                                 help='operate on all projects in the workspace') 
        self.parser.add_argument('-S', '--state', action='append', dest='states', default=[],
                                 help='operate on projects with given state')
        self.parser.add_argument('-n', '--not', action='store_true', dest='negated',
                                 help='negates a state selection')
        self.parser.add_argument('-t', '--tagged', action='append', dest='tags', default=[],
                                 help='operate on projects tagged as specified')
        self.parser.add_argument('-p', '--pause', action='store_true', dest='pause',
                                 help='pause between commands')
        self.parser.add_argument('-X', '--summary', action='store_true', dest='summary',
                                 help='prints summary at end')
        self.parser.add_argument('-d', '--delimit-output', action='store_true', dest='delimit_output',
                                 help='prints starting and ending markers around the output of each project')
        

    def function(self, project, args):
        return None

    def verify_commandline(self, args):
        count = reduce(lambda a,b: a+1 if b else a, [args.selection, args.all, args.negated], 0)
        if count > 1:
            self.parser.error('Cannot use -S, -a or -n together')

        if (args.selection or args.all) and (args.states or args.tags or args.negated):
            self.parser.error('Cannot use -s or -a with -n, -S or -t')


    def execute_one(self, project, args):
        with project.paths_set():
            try:
                retcode = self.function(project, args)
            except SystemExit as ex:
                if ex.code:
                    print('\nERROR: Script exited: %s' % ex, file=sys.stderr)
                    retcode = ex.code
                else:
                    retcode = 0
            except OSError as ex:
                print('\nERROR: Execution failed: %s' % ex, file=sys.stderr)
                retcode = ex.errno
            except SetupCommandFailed as ex:
                print('\nERROR: Execution failed: %s' % ex, file=sys.stderr)
                retcode = 1
            except (NotVersionedException, NotCheckedInException, MetaInformationNotAvailableException, AlreadyDebianisedException,
                    MetaInformationNotReadableException, UnchangedException, NeedsNewVersionException,
                    NotUploadedException, AlreadyMarkedAsReleasedException,
                    AlreadyUploadedException, NotBuiltException,
                    NotBuiltAfterLastCommitException, NotBuiltException) as ex:
                print(str(ex), file=sys.stderr)
                retcode = None
            except CalledProcessError as ex:
                print(str(ex), file=sys.stderr)
                retcode = ex.returncode

        if retcode is not None:
            if isinstance(retcode, str):
                print('ERROR: Child was terminated with error message: %s\n' % retcode, file=sys.stderr)
            elif retcode < 0:
                print('ERROR: Child was terminated by signal %s\n' % retcode, file=sys.stderr)
            elif retcode > 0:
                print('ERROR: Child returned %s\n' % retcode, file=sys.stderr)

        return retcode

    def execute(self, args):
        if args.states or args.tags:
            project_list = self.workspace.get_selection_subset(states=args.states, tags=args.tags, append=False, all_=args.all, negated=args.negated)
        elif args.selection:
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

        pause = args.pause
        summary = args.summary
        delimit_output = args.delimit_output

        results = {}
        for i in project_list:
            if delimit_output:
                print(self.format_individual_message(i, args, '\n--- START %s ---'))
            results[i] = self.execute_one(i, args)
            if pause:
                print('--- PAUSED, hit <enter> to continue, ^D to stop ---')
                if not sys.stdin.readline():
                    print('\n^D pressed, halting immediately')
                    break
            if delimit_output:
                print(self.format_individual_message(i, args, '\n--- END %s ---'))

        if summary:
            print('\n--- SUMMARY ---')
            for i in project_list:
                print('%s %s' % (results[i], i.relative_directory), file=sys.stdout)
            print('--- END ---\n')

        success = set(results.values()) == {0}
        if success:
            return 0
        return 1

    def format_individual_message(self, project, args, template):
        return template % project.relative_directory
    


class Debianise(ForAllWorkspaceCommand):
    """Debianises a project."""
    keyword = 'debianise'
    def function(self, project, args):
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

    def function(self, main_project, args):
        projects = [main_project]
        if main_project.has_children:
            projects = main_project.egg_projects

        for project in projects:
            self.print_heading('\tProject directory:\t%s' % project.directory)
            print('\tVersion:\t\t%s' % project.version)
            print('\tName:\t\t\t%s' % project.project_name)
            print('\tIs version controlled?:\t%s' % project.is_version_controlled())
            if project.is_version_controlled():
               print('\tLast commit:\t\t%s' % project.source_control.last_commit_time)
               print('\tUnchanged?:\t\t%s' % project.is_unchanged())
               print('\tNeeds new version?:\t%s' % project.needs_new_version())
               print('\tIs checked in?:\t\t%s' % project.is_checked_in())

        self.print_heading('\tMain project:\t%s' % main_project.directory)
        self.print_heading('\tPackages to distribute:')
        for package in main_project.packages_to_distribute:
            print('\t%s' % str(package))
        print('\n')
        return 0


class MigrateReahlProject(ForAllWorkspaceCommand):
    """Writes a hardcoded setup.cfg file from an existing .reahlproject."""
    keyword = 'migratereahlproject'
    def function(self, project, args):
        project.generate_migrated_setup_cfg()
        return 0

        
class Shell(ForAllWorkspaceCommand):
    """Executes a shell command in each selected project, from each project's own root directory."""
    keyword = 'shell'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('-g', '--generate_setup_py', action='store_true', dest='generate_setup_py', default=False,
                                 help='temporarily generate a setup.py for the duration of the shell command (it is removed afterwards)')
        self.parser.add_argument('shell_commandline', nargs=argparse.REMAINDER, 
                                 help='the shell command (and any arguments) that should be executed')

    def format_individual_message(self, project, args, template):
        return template % ('%s %s' % (project.relative_directory, ' '.join(args.shell_commandline)))
    
    def function(self, project, args):
        @contextmanager
        def nop_context_manager():
            yield

        context_manager = project.generated_setup_py if args.generate_setup_py else nop_context_manager
        with context_manager():
            command = self.do_shell_expansions(project.directory, args.shell_commandline)
            return Executable(command[0]).call(command[1:], cwd=project.directory)

    def do_shell_expansions(self, directory, commandline):
        replaced_command = []
        for i in commandline:
            if i.startswith('$(') and i.endswith(')'):
                shellcommand = i[2]
                shell_args = i[3:-1].split(' ')
                output = Executable(shellcommand).Popen(shell_args, cwd=directory, stdout=subprocess.PIPE).communicate()[0]
                for line in output.splitlines():
                    replaced_command.append(line)
            else:
                replaced_command.append(i)
        return replaced_command


class Setup(ForAllWorkspaceCommand):
    """Runs setup.py <command> for each project in the current selection."""
    keyword = 'setup'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('setup_py_args', nargs=argparse.REMAINDER, help='arguments to setup.py')

    def parse_commandline(self, argv):
        args = super().parse_commandline(argv)
        if args.setup_py_args[0] == '--':
            args.setup_py_args[:] = args.setup_py_args[1:]
        return args

    def function(self, project, args):
        project.setup(args.setup_py_args, script_name='%s %s' % (sys.argv[0], self.keyword))
        return 0


class Build(ForAllWorkspaceCommand):
    """Builds all distributable packages for each project in the current selection."""
    keyword = 'build'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('-ns', '--nosign', action='store_true', dest='nosign', default=False,
                                 help='don\'t sign build artifacts')

    def function(self, project, args):
        self.sign = not args.nosign
        project.build(sign=self.sign)
        return 0

    
class Sign(ForAllWorkspaceCommand):
    """Signs all distributable packages for each project in the current selection."""
    keyword = 'sign'
    def assemble(self):
        super().assemble()

    def function(self, project, args):
        project.sign()
        return 0

    
class ListMissingDependencies(ForAllWorkspaceCommand):
    """Lists all missing thirdparty dependencies for each project in the current selection."""
    keyword = 'missingdeps'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('-D', '--development', action='store_true', dest='for_development', default=False,
                                 help='include development dependencies')

    def function(self, project, args):
        try:
            dependencies = project.list_missing_dependencies(for_development=args.for_development)
            if dependencies:
                print(' '.join(dependencies))
        except:
            traceback.print_exc()
            return -1

        return 0


class DebInstall(ForAllWorkspaceCommand):
    """Runs setup.py install with correct arguments for packaging the result in a deb (for each project in the selection)."""
    keyword = 'debinstall'
    def function(self, project, args):
        project.debinstall(args)
        return 0


class Upload(ForAllWorkspaceCommand):
    """Uploads all built distributable packages for each project in the current selection."""
    keyword = 'upload'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('-k', '--knock', action='append', dest='knocks', default=[],
                                 help='port to knock on before uploading')
        self.parser.add_argument('-r', '--ignore-release-checks', action='store_true', dest='ignore_release_checks', default=False,
                                 help='proceed with uploading despite possible failing release checks')
        self.parser.add_argument('-u', '--ignore-uploaded-check', action='store_true', dest='ignore_upload_check', default=False,
                                 help='upload regardless of possible previous uploads')
        
    def function(self, project, args):
        if args.ignore_release_checks:
            print('WARNING: Ignoring release checks at your request', file=sys.stderr)
        if args.ignore_upload_check:
            print('WARNING: Overwriting possible previous uploads', file=sys.stderr)
        project.upload(knocks=args.knocks, ignore_release_checks=args.ignore_release_checks, ignore_upload_check=args.ignore_upload_check)
        return 0


class MarkReleased(ForAllWorkspaceCommand):
    """Marks each project in the current selection as released."""
    keyword = 'markreleased'
    def function(self, project, args):
        project.mark_as_released()
        return 0


class SubstVars(ForAllWorkspaceCommand):
    """Generates debian substvars."""
    keyword = 'substvars'
    def function(self, project, args):
        assert hasattr(project.metadata, 'generate_deb_substvars'), \
               'This command is only valid on debian-based projects (with <metadata type="debian"/>)'
        project.metadata.generate_deb_substvars()
        return 0

class UpdateAptRepository(WorkspaceCommand):
    """Updates the index files of the given apt repository."""
    keyword = 'updateapt'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('root_directory', help='the root directory of the apt repository')

    def execute(self, args):
        if not os.path.isdir(args.root_directory):
            message = '"%s" is not a valid directory from within %s' % (args.root_directory, os.getcwd())
            raise Exception(message)

        repository = LocalAptRepository(args.root_directory)
        repository.build_index_files()


class ExtractMessages(ForAllWorkspaceCommand):
    """Collects strings marked for translation."""
    keyword = 'extractmessages'
    def function(self, project, args):
        project.extract_messages(args)
        return 0


class MergeTranslations(ForAllWorkspaceCommand):
    """Merges newly discovered strings needing translation with a catalog of existing translations."""
    keyword = 'mergetranslations'
    def function(self, project, args):
        project.merge_translations()
        return 0


class CompileTranslations(ForAllWorkspaceCommand):
    """Compiles all current translations."""
    keyword = 'compiletranslations'
    def function(self, project, args):
        project.compile_translations()
        return 0


class AddLocale(ForAllWorkspaceCommand):
    """Adds a new locale catalog."""
    keyword = 'addlocale'
    def assemble(self):
        super().assemble()
        self.parser.add_argument('locale', help='a locale identifier')
        self.parser.add_argument('source_egg', nargs='?', default=None, help='the egg to which this locale applies (its name is used as the domain of the locale)')

    def function(self, project, args):
        project.add_locale(args.locale, args.source_egg)
        return 0



class UpdateCopyright(Command):
    """Updates the dates found in copyright statements found on the first line of files based on git history."""
    keyword = 'update-copyright'

    def assemble(self):
        super().assemble()
        self.parser.add_argument('copyright_holder_string', nargs='?', default='.*',
                                 help='requires this copyright holder to be present in a copyright line (by default any comment line with Copyright is matched)')

    def execute(self, args):
        super().execute(args)
        self.git = Executable('git')
        for filename in self.get_all_filenames():
            if os.path.splitext(filename)[1] not in ['.mo', '.png', '.jpg']:
                self.process_file(filename, args.copyright_holder_string)
        return 0

    def process_file(self, filename, copyright_holder_string):
        with open(filename, encoding='utf-8') as infile:
            first_line = infile.readline()
            match = re.match('^(?P<start>(#|/[*]|\')\s*Copyright\s*)(?P<years>[0-9, -]+)(?P<end>.*%s.*$)' % copyright_holder_string, first_line)
            if match:
                new_line = '%s%s %s\n' % (match.group('start'), self.get_date_string(filename), match.group('end'))
                out_filename = '%s.t' % filename
                with open(out_filename, 'w', encoding='utf-8') as outfile:
                    outfile.write(new_line)
                    shutil.copyfileobj(infile, outfile)
                shutil.move(out_filename, filename)
        
    def get_all_filenames(self):
        return [filename.decode('utf-8') for filename in self.git.check_output(['ls-files']).split()]

    def get_date_string(self, filename):
        years = sorted({ date[:4].decode('utf-8') for date in self.git.check_output('log --pretty=format:%ad --date=short --follow'.split()+[filename]).split() })
        if len(years) > 3:
            date_string = '%s-%s' % (years[0], years[-1])
        else:
            date_string = ', '.join(years)
        return date_string

        
