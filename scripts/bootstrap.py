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


import sys
import subprocess
import pkg_resources
import distutils.sysconfig
import os
import shutil
import glob
import re
import xml.etree.ElementTree


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


def clean_virtual_env():
    virtual_env = get_venv_basedir()
    for f in glob.iglob(os.path.join(virtual_env, 'lib', 'python*', 'site-packages', '*egg-link')):
        rm_f(f)

    for f in glob.iglob(os.path.join(virtual_env, 'lib', 'python*', 'site-packages', 'easy-install.pth')):
        rm_f(f)


def get_venv_basedir():
    real_prefix = getattr(sys, "real_prefix", None)
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    running_in_virtualenv = (base_prefix or real_prefix) != sys.prefix
    if not running_in_virtualenv:
        raise AssertionError('You must be in a virtual environment')
    return distutils.sysconfig.get_config_vars()['exec_prefix']


def clean_workspace(reahl_workspace):
    rm_f(os.path.join(reahl_workspace, '.reahlworkspace', 'workspace.projects'))
    rm_f(os.path.join(reahl_workspace, '.reahlworkspace', 'current.selection'))

def clean_egg_info_dirs():
    for current_directory, directories, files in os.walk(os.getcwd()):
        for d in directories:
            if (d.endswith('egg-info') or d.endswith('dist-info')) and not d in ['reahl_dev.egg-info','reahl_dev.dist-info']:
                shutil.rmtree(os.path.join(current_directory, d))

def remove_versions_from_requirements(requires_file):
    with open(requires_file, 'r') as input_file:
        lines = input_file.readlines()
    with open(requires_file, 'w') as output_file:
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


def find_all_prerequisits_for(project_dirs):
    prerequisites = {'tox>=3.14,<3.14.999'} # Nothing depends on tox, but we use it in .github/worfklows so it forms part of our basic infrastructure
    for project_dir in project_dirs:
        prerequisites.update(parse_prerequisites_from(os.path.join(os.getcwd(), project_dir, '.reahlproject')))
    return prerequisites


def find_missing_prerequisites(project_dirs):
    missing = set()
    for i in find_all_prerequisits_for(project_dirs):
        try:
            pkg_resources.require(i)
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            missing.add(i.strip())
    return list(missing)


def install_with_pip(package_list, upgrade=False):
    args = ['-U'] if upgrade else []
    return subprocess.call([sys.executable, '-m', 'pip', 'install'] + args + package_list)


def install_prerequisites(missing):
    print('----------------------------------------------------------------------------------')
    print('reahl-dev and its dependencies depend on eggs that are not part of reahl.')
    print('You need these in order to run this script.')
    print('Some of these are not installed on your system.')
    print('The missing eggs are:')
    print('')
    print('  '+(' '.join(missing)))
    print('')
    print('I will now go ahead and "pip install" the eggs listed above')
    print('')
    return install_with_pip(missing, upgrade=True) == 0


def get_common_version():
    def get_debian_changelog_src():
        src_lines = []
        src_line = False
        with open('reahl-dev/reahl/dev/devdomain.py', 'r') as f:
            for line in f:
                if line.startswith('# bootstrap.py-begin'):
                    src_line = True
                if line.startswith('# bootstrap.py-end'):
                    src_line = False
                if src_line:
                    src_lines.append(line)
        return '\n'.join(src_lines)
    tmp_locals = {}
    exec(get_debian_changelog_src(), {'re': re}, tmp_locals)
    DebianChangelog = tmp_locals['DebianChangelog']

    return '.'.join(DebianChangelog('debian/changelog').version.split('.')[:2])


def make_core_projects_importable(core_project_dirs):
    for d in core_project_dirs:
        project_path = os.path.join(os.getcwd(), d)
        pkg_resources.working_set.add_entry(project_path)
        sys.path.append(project_path)
    common_version = get_common_version()
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


def print_final_message(success=True):
    debs_needed_to_compile_python = ['python3-venv', 'python3-dev', 'gcc', 'cython3', 'libxml2-dev', 'libxslt-dev', 'libsqlite3-0', 
                                    'sqlite3', 'postgresql-server-dev-all', 'zlib1g-dev', 'libjpeg62-dev', 'libfreetype6-dev', 'liblcms2-dev', 
                                    'mysql-client', 'libmysqlclient-dev']
    general_debs_needed = ['openssh-client', 'dpkg-dev', 'firefox', 'firefox-geckodriver']

    print('')
    print('')
    if success:
      print('-- ALL DONE --------------------------------------------------------------------------')
      print('Done. All python dependencies satisfied.')
    else:
      print('-- ERROR --------------------------------------------------------------------------')
      print('Something went wrong....please check that all the dependencies listed here are installed:')
    print('')
    print('In order to develop on Reahl, you will need other (non-python) packages as well.')
    print('What these are called may differ depending on your distribution/OS.')
    print('As a hint, on ubuntu systems these are:')
    print('')
    print('  '+' '.join(general_debs_needed)) 
    print('')
    print('NOTE: If you\'re working in a virtualenv and want to pip install dependencies, you will also need:')
    print('')
    print('  '+' '.join(debs_needed_to_compile_python)) 
    print('')

def parse_prerequisites_from(dot_project_file):
    root = xml.etree.ElementTree.parse(dot_project_file).getroot()
    deps_for_common_version = root.findall('.//version[@number="%s"]//thirdpartyegg' % get_common_version())
    for node in deps_for_common_version:
        requirement_string = node.attrib['name']
        min_version = node.attrib.get('minversion', None)
        max_version = node.attrib.get('maxversion', None)
        if min_version:
            requirement_string += '>=%s' % min_version
        if max_version:
            comma = ',' if min_version else ''
            requirement_string += '%s<%s' % (comma, max_version)
        yield requirement_string

    
def ensure_script_dependencies_installed():
    missing = find_missing_prerequisites(core_project_dirs)
    if missing and install_prerequisites(missing):
        return []
    elif missing:
        return missing
    return []

def ensure_reahl_project_dependencies_installed():
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
        if install_with_pip(list(set(missing_dependencies).union(find_all_prerequisits_for(core_project_dirs))), upgrade=False) != 0:
            print("Error trying to install one of: " + ','.join(missing_dependencies))
            return False
        run_setup(workspace, workspace.selection)
    return True


reahl_workspace = read_env_variable('REAHLWORKSPACE',
                    'Please set the environment variable REAHLWORKSPACE to point to a parent directory of %s' \
                          % (os.getcwd()))
reahl_dev_requires_file = os.path.join(os.getcwd(), 'reahl-dev', 'reahl_dev.egg-info', 'requires.txt')
core_project_dirs = ['reahl-component-metadata', 'reahl-component', 'reahl-stubble', 'reahl-tofu', 'reahl-dev']

clean_virtual_env()
clean_workspace(reahl_workspace)
clean_egg_info_dirs()

remove_versions_from_requirements(reahl_dev_requires_file)
fake_distributions_into_existence(core_project_dirs)


if "--script-dependencies" in sys.argv:
   still_missing = ensure_script_dependencies_installed()
   if still_missing:
       print('Failed to install %s - (see pip errors above)' % (' '.join(still_missing)) )
   else:
       print('Successfully installed prerequisites - please re-run with --pip-installs')
       
elif "--pip-installs" in sys.argv:
    success = ensure_reahl_project_dependencies_installed()
    print_final_message(success=success)
else:
    print('Usage: %s [--script-dependencies|--pip-installs]' % sys.argv[0])
    exit(123)
