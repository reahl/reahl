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
try:
    from six.moves import input
except:
    if 'raw_input' in dir(__builtins__):
        input = raw_input
import sys
import pkg_resources
import os
import shutil
import glob
import re
import io

def ask(prompt):
    answer = None
    while answer is None:
        response = input(prompt)
        if response.lower() in ('y', 'yes'):
            answer = True
        if response.lower() in ('n', 'no'):
            answer = False
    return answer

def rm_f(f):
    if os.path.isfile(f):
        os.remove(f)

def read_env_variable(variable, error_message):
    try:
      return os.environ[variable]
    except KeyError as e:
      raise AssertionError(error_message)

def clean_virtual_env(virtual_env):
    for f in glob.iglob(os.path.join(virtual_env, 'lib', 'python*', 'site-packages', '*egg-link')):
        rm_f(f)

    for f in glob.iglob(os.path.join(virtual_env, 'lib', 'python*', 'site-packages', 'easy-install.pth')):
        rm_f(f)

def clean_workspace(reahl_workspace):
    rm_f(os.path.join(reahl_workspace, '.reahlworkspace', 'workspace.projects'))
    rm_f(os.path.join(reahl_workspace, '.reahlworkspace', 'current.selection'))

def clean_egg_info_dirs():
    for current_directory, directories, files in os.walk(os.getcwd()):
        for d in directories:
            if d.endswith('egg-info') and not d in ['reahl_dev.egg-info','reahl_bzrsupport.egg-info']:
                shutil.rmtree(os.path.join(current_directory, d))

def remove_versions_from_requirements(requires_file):
    with io.open(requires_file, 'r') as input_file:
        lines = input_file.readlines()
    with io.open(requires_file, 'w') as output_file:
        for line in lines:
            version_stripped_line = re.match('([\w-]+)', line).group(0)
            output_file.write(version_stripped_line)
            output_file.write('\n')

def egg_dirs_for(project_dirs):
    for project_dir in project_dirs:
        egg_info = '%s.egg-info' % project_dir.replace('-', '_')
        yield os.path.join(os.getcwd(), project_dir, egg_info)

def fake_distributions_into_existence(project_dirs):
    for egg_dir in egg_dirs_for(project_dirs):
        if not os.path.exists(egg_dir):
            os.mkdir(egg_dir)

def find_missing_prerequisites(requires_file, hard_coded_core_dependencies):
    non_reahl_requirements = hard_coded_core_dependencies[:]
    for line in io.open(requires_file, 'r'):
        if not line.startswith('reahl-'):
            non_reahl_requirements.append(line)
    missing = []
    for i in non_reahl_requirements:
        try:
            pkg_resources.require(i)
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            missing.append(i)
    return missing

def install_prerequisites(missing):
  print('----------------------------------------------------------------------------------')
  print('reahl-dev depends on eggs that are not part of reahl.')
  print('You need these in order to run this script.')
  print('Some of these are not installed on your system.')
  print('The missing eggs are:')
  print('')
  print('  '+(' '.join(missing)))
  print('')
  print('Can I go ahead and "pip install" the eggs listed above?')
  print('  (the alternative is for you to answer "no", which will abort this script and ')
  print('   thus allow you to first install the missing eggs yourself by other means)')
  print('')
  if ask('Enter "yes" or "no"   : '):
      import pip
      pip.main(['install']+missing)
  else:
      print('Not installing %s - please install it by other means before running %s' % ((' '.join(missing), sys.argv[0])))
      exit(1)

def make_core_projects_importable(core_project_dirs):
    for d in core_project_dirs:
        pkg_resources.working_set.add_entry(os.path.join(os.getcwd(), d))
    from reahl.dev.devdomain import DebianChangelog
    common_version = DebianChangelog('debian/changelog').version
 
    for egg_dir in egg_dirs_for(core_project_dirs):
        pkg_filename = os.path.join(egg_dir, 'PKG-INFO')
        if not os.path.exists(pkg_filename):
            with open(pkg_filename, 'w') as pkg_file:
                pkg_file.write('Version: %s\n' % common_version)

def bootstrap_workspace(workspace_dir, core_project_dirs):
    make_core_projects_importable(core_project_dirs)
    from reahl.dev.devdomain import Project, Workspace
    workspace = Workspace(workspace_dir)
    for project_dir in core_project_dirs:
        Project.from_file(workspace, os.path.join(os.getcwd(), project_dir))

    core_projects = [Project.from_file(workspace, os.path.join(os.getcwd(), project_dir)) for project_dir in core_project_dirs]
    return workspace, core_projects

def run_setup(workspace, projects, uninstall=False):
    command = ['develop', '-N']
    if uninstall:
        command.append('--uninstall')

    for project in projects:
        project.setup(command)

def find_missing_dependencies(workspace):
    missing = set()
    for project in workspace.selection:
        missing.update(project.list_missing_dependencies(for_development=True))
    return list(missing)

def print_final_message(missing_dependencies):
    print('')
    print('')
    print('-- ALL DONE --------------------------------------------------------------------------')
    if missing_dependencies:
      print('The following eggs are not available on your system, but are needed ')
      print('to be able to develop and run reahl:')
      print('')
      print('  '+' '.join(missing_dependencies))
      print('')
      print('You have a choice here:')
      print(' 1) You can install packages that provide these eggs via the package manager of your distribution')
      print(' 2) You can install the eggs directly using "pip install" using the following command:')
      print('    pip install ' + (' '.join(['"%s"' % d for d in missing_dependencies])) )
      print('')
      print('NOTE: You are running inside a virtualenv')
      print('      To be able to do (1), your virtualenv should have been created using the ')
      print('      --system-site-packages option to virtualenv.')
      print('')
      print('NOTE: Choosing (2) will require that you have some non-python packages installed')
      print('      on your system. What these are called may differ depending on your distribution/OS,')
      print('      As a hint, on ubuntu these are called:')
      print('')
      print('  python-virtualenv python-dev gcc cython libxml2-dev libxslt-dev libsqlite3-0 sqlite3 postgresql-server-dev-9.1 zlib1g-dev libjpeg62-dev libfreetype6-dev liblcms1-dev')
      print('')
      print('NB:  You will have to run this script again after satisfying these dependencies')
      print('')
    else:
      print('Done. All python dependencies satisfied.')
      print('')
      print('In order to develop on Reahl, you will need other (non-python) packages as well.')
      print('What these are called may differ depending on your distribution/OS.')
      print('As a hint, on ubuntu systems these are:')
      print('')
      print(' equivs openssh-client dpkg-dev ')
      print('')



virtual_env = read_env_variable('VIRTUAL_ENV', 'You should develop on Reahl within a virtualenv.')
reahl_workspace = read_env_variable('REAHLWORKSPACE', 
                    'Please set the environment variable REAHLWORKSPACE to point to a parent directory of %s' \
                          % (os.getcwd()))
reahl_dev_requires_file = os.path.join(os.getcwd(), 'reahl-dev', 'reahl_dev.egg-info', 'requires.txt')
core_project_dirs = ['reahl-bzrsupport', 'reahl-component', 'reahl-stubble', 'reahl-tofu', 'reahl-dev']

clean_virtual_env(virtual_env)
clean_workspace(reahl_workspace)
clean_egg_info_dirs()

remove_versions_from_requirements(reahl_dev_requires_file)
fake_distributions_into_existence(core_project_dirs)
missing = find_missing_prerequisites(reahl_dev_requires_file, ['six','wrapt','setuptools>11'])
if missing:
    install_prerequisites(missing)

workspace, core_projects = bootstrap_workspace(reahl_workspace, core_project_dirs)
run_setup(workspace, core_projects)
workspace.selection = core_projects

# For good measure, we "setup.py develop" all eggs in reahl
workspace.refresh(False, [os.getcwd()])
workspace.select(all_=True)
run_setup(workspace, workspace.selection)

missing_dependencies = find_missing_dependencies(workspace)
if missing_dependencies:
    run_setup(workspace, workspace.selection, uninstall=True)
print_final_message(missing_dependencies)


