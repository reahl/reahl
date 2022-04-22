# Copyright 2015-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""A commandline utility to display package information installed in your environment."""

import urllib
import argparse

from bs4 import BeautifulSoup

import pip
import pkg_resources


class PypiPackage:
    def __init__(self, package_name):
        self.package_name = package_name

    @property
    def is_installed(self):
        try:
            pkg_resources.get_distribution(package_name)
        except pkg_resources.DistributionNotFound as e:
            return False
        return True

    @property
    def is_exists_in_pypi(self):
        try:
            urllib.request.urlopen(self.get_pypi_org_url())
        except urllib.error.HTTPError as e:
            return False
        return True

    def get_pypi_org_url(self, version=None):
        if version:
            return 'https://pypi.python.org/pypi/%s' % ('%s/%s' % (self.package_name, self.installed_version_string))
        return 'https://pypi.python.org/pypi/%s' % self.package_name

    @property
    def distribution(self):
        return pkg_resources.get_distribution(self.package_name)

    @property
    def installed_version_string(self):
        return self.distribution.version

    @property
    def package_name_version(self):
        if self.is_installed:
            return '%s %s' % (self.package_name, self.installed_version_string)
        return self.package_name

    @property
    def installed_version(self):
        return self.distribution.parsed_version

    @property
    def installed_license(self):
        if self.is_installed:
            metadata_resource_name = self.distribution.PKG_INFO
            if self.distribution.has_metadata(metadata_resource_name):
                license_prefix = 'License: '
                licenses = [l[len(license_prefix):] for l in self.distribution.get_metadata_lines(metadata_resource_name) if l.startswith(license_prefix)]
                return ','.join(licenses)
            return '***No license metadata for installed package***'
        return '***Package not installed***'

    @property
    def pypi_license_for_installed_version(self):
        if self.is_exists_in_pypi:
            url_to_open = self.get_pypi_org_url(version=self.installed_version_string)
            try:
                page = urllib.request.urlopen(url_to_open)
                soup = BeautifulSoup(page)
                soup.prettify()
                for anchor in soup.findAll('a', href=True):
                    if('License' in anchor.contents[0]):
                        license_text = anchor.contents[0]
                        return license_text.split(' :: ')[-1]
                return '***No license metadata on pypi***'
            except urllib.error.HTTPError as e:
                return '***Package version %s not found in pypi (%s)***' % (self.installed_version_string, url_to_open)
        return '***Package not found in pypi***'

    def get_version_from_href(self, href):
        return href.split('/')[-1]

    def other_version_is_newer(self, other_raw_version):
        return pkg_resources.parse_version(other_raw_version) > self.installed_version

    def available_newer_versions(self):
        newer_versions = []
        page = urllib.request.urlopen(self.get_pypi_org_url())
        soup = BeautifulSoup(page)
        soup.prettify()
        for anchor in soup.findAll('a', href=True):
            href = anchor['href']
            if href.startswith('/pypi/%s' % package_name):
                available_raw_version = self.get_version_from_href(href)
                if self.other_version_is_newer(available_raw_version):
                    newer_versions.append(available_raw_version)
        return newer_versions

    def __repr__(self):
        return '%s [%s] InstalledLic[%s] PypiLic[%s] newer versions: %s' % (self.package_name, self.installed_version_string, self.installed_license,
                                                       self.pypi_license_for_installed_version(), str(self.available_newer_versions()))


parser = argparse.ArgumentParser(description='Show meta information about installed packages.')
parser.add_argument('-l', '--installed_license', dest='show_installed_license', action='store_true', default=False,
                   help='show the license info found in the installed package metadata(if package is installed)')
parser.add_argument('-L', '--pypi_license', dest='show_pypi_license', action='store_true', default=False,
                   help='show the license info found in in pypi for the installed package')
parser.add_argument('-V', '--newer_versions', dest='show_newer_versions', action='store_true', default=False,
                   help='list newer versions on pypi than the installed version')
parser.add_argument('-p', '--package_names', dest='package_names', nargs='*', metavar='package_name',
                   help='instead of all installed packages, show the meta information only for a specified list of packages')
args = parser.parse_args()

packages = args.package_names if args.package_names else [dist.project_name for dist in pip.get_installed_distributions()]
for package_name in packages:
    try:
        pypi_package = PypiPackage(package_name)

        list_of_info_to_display = [pypi_package.package_name_version]
        if args.show_installed_license:
            list_of_info_to_display.append('  Licence(Installed): %s' % pypi_package.installed_license)
        if args.show_pypi_license:
            list_of_info_to_display.append('  Licence(Pypi): %s' % pypi_package.pypi_license_for_installed_version)
        if args.show_newer_versions:
            newer_versions = pypi_package.available_newer_versions()
            list_of_info_to_display.append('  Newer versions: %s' % ('-' if not newer_versions else ', '.join(newer_versions)))
        print('\n'.join(list_of_info_to_display))
    except:
        print ('Problem retrieving details for package name: %s' % package_name)
