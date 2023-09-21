# Copyright 2013-2023 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import subprocess
import sysconfig
import os
import shutil
import glob
import pathlib


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
    return sysconfig.get_config_vars()['exec_prefix']


def clean_egg_info_dirs():
    for current_directory, directories, files in os.walk(os.getcwd()):
        for d in directories:
            if d.endswith('egg-info'):
                shutil.rmtree(os.path.join(current_directory, d))

def install_with_pip(package_list, upgrade=False):
    args = ['-U'] if upgrade else []
    return subprocess.call([sys.executable, '-m', 'pip', 'install'] + args + package_list)

def build_with_pip(package_dir, upgrade=False):
    dist_directory = '%s/.reahlworkspace/dist-egg' % os.environ.get('REAHLWORKSPACE', os.environ['HOME'])
    return subprocess.call([sys.executable, '-m', 'build', '--wheel', '--outdir', dist_directory], cwd=package_dir)

def editable_install(project_dirs, with_tests=False):
    test_extra = '[test]' if with_tests else ''
    subprocess.run(['python', '-m', 'pip', 'install'] + ['-e%s%s' % (i, test_extra) for i in project_dirs], check=True)


def print_final_message():
    debs_needed_to_compile_python = ['python3-venv', 'python3-dev', 'gcc', 'cython3', 'libxml2-dev', 'libxslt-dev', 'libsqlite3-0', 
                                    'sqlite3', 'postgresql-server-dev-all', 'zlib1g-dev', 'libjpeg62-dev', 'libfreetype6-dev', 'liblcms2-dev', 
                                    'mysql-client', 'libmysqlclient-dev']
    general_debs_needed = ['openssh-client', 'dpkg-dev', 'firefox', 'firefox-geckodriver']

    print('')
    print('')
    print('-- ALL DONE --------------------------------------------------------------------------')
    print('Done. All python dependencies satisfied.')
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


clean_virtual_env()
clean_egg_info_dirs()

install_with_pip(['tox>=4.6.3', 'build'])  # Nothing depends on tox, but we use it in .github/worfklows so it forms part of our basic infrastructure
build_with_pip(pathlib.Path('reahl-component-metadata'))
install_with_pip(['reahl-component-metadata'])
project_paths = [str(i) for i in pathlib.Path().glob('reahl-*')]+['.']
editable_install(project_paths, with_tests=False)
editable_install(project_paths, with_tests=True)

print_final_message()

