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


import datetime
import os.path

import pkg_resources

from reahl.tofu import scenario, temp_dir, temp_file_with, Fixture
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import easter_egg, stubclass

from reahl.web.fw import FileOnDisk, FileFromBlob, PackagedFile, ConcatenatedFile, FileDownload, UserInterface
from reahl.browsertools.browsertools import Browser

from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
def test_files_from_disk(web_fixture):
    """A directory in the web.static_root configuration setting, can be mounted on a URL
       named after it on the WebApplication.
    """

    static_root = temp_dir()
    files_dir = static_root.sub_dir('staticfiles')
    sub_dir = files_dir.sub_dir('subdir')
    one_file = files_dir.file_with('one_file.xml', 'one')
    nested_file = sub_dir.file_with('nested_file', 'other')

    # How the config is set
    web_fixture.config.web.static_root = static_root.name

    # How the subdirectory is mounted
    class MainUI(UserInterface):
        def assemble(self):
            self.define_static_directory('/staticfiles')

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # How the first file would be accessed
    browser.open('/staticfiles/one_file.xml')
    assert browser.raw_html == 'one'

    # The meta-info of the file
    response = browser.last_response
    assert response.content_type == 'application/xml'
    assert response.content_encoding is None
    assert response.content_length == 3
    expected_mtime = datetime.datetime.fromtimestamp(int(os.path.getmtime(one_file.name)))
    assert response.last_modified.replace(tzinfo=None) == expected_mtime
    expected_tag = '%s-%s-%s' % (os.path.getmtime(one_file.name), 3, abs(hash(one_file.name)))
    assert response.etag == expected_tag

    # How the file in the subdirectory would be accessed
    browser.open('/staticfiles/subdir/nested_file')
    assert browser.raw_html == 'other'

    # When a file does not exist
    browser.open('/staticfiles/one_that_does_not_exist', status=404)


@with_fixtures(WebFixture)
def test_files_from_list(web_fixture):
    """An explicit list of files can also be added on an URL as if they were in a single
       directory.
    """

    files_dir = temp_dir()
    one_file = files_dir.file_with('any_name_will_do_here', 'one')

    class MainUI(UserInterface):
        def assemble(self):
            list_of_files = [FileOnDisk(one_file.name, 'one_file')]
            self.define_static_files('/morestaticfiles', list_of_files)

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # How the first file would be accessed
    browser.open('/morestaticfiles/one_file')
    assert browser.raw_html == 'one'

    # The meta-info of the file
    response = browser.last_response
    assert response.content_type == 'application/octet-stream'
    assert response.content_encoding is None
    assert response.content_length == 3
    expected_mtime = datetime.datetime.fromtimestamp(int(os.path.getmtime(one_file.name)))
    assert response.last_modified.replace(tzinfo=None) == expected_mtime
    expected_tag = '%s-%s-%s' % (os.path.getmtime(one_file.name), 3, abs(hash(one_file.name)))
    assert response.etag == expected_tag

    # When a file does not exist
    browser.open('/morestaticfiles/one_that_does_not_exist', status=404)


@with_fixtures(WebFixture)
def test_files_from_database(web_fixture):
    """Files can also be created on the fly such as from data in a database."""


    content_bytes = ('hôt stuff').encode('utf-8')

    class MainUI(UserInterface):
        def assemble(self):
            mime_type = 'text/html'
            encoding = 'utf-8'
            mtime = 123
            size = len(content_bytes)

            list_of_files = [FileFromBlob('database_file', content_bytes, mime_type, encoding, size, mtime)]
            self.define_static_files('/files', list_of_files)

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # How the file would be accessed
    browser.open('/files/database_file')
    assert browser.raw_html == 'hôt stuff'
    response = browser.last_response

    # The meta-info of the file
    assert response.content_type == 'text/html'
    assert not response.content_encoding
    assert response.content_length == len(content_bytes)
    assert response.last_modified.replace(tzinfo=None) == datetime.datetime.fromtimestamp(123)
    expected_etag = '123-%s-%s' % (len(content_bytes), abs(hash('database_file')))
    assert response.etag == expected_etag


@with_fixtures(WebFixture)
def test_packaged_files(web_fixture):
    """Files can also be served straight from a python egg."""


    # Create an egg with package packaged_files, containing the file packaged_file
    egg_dir = temp_dir()
    package_dir = egg_dir.sub_dir('packaged_files')
    init_file = package_dir.file_with('__init__.py', '')
    afile = package_dir.file_with('packaged_file', 'contents')

    easter_egg.clear()
    pkg_resources.working_set.add(easter_egg)
    easter_egg.location = egg_dir.name

    with easter_egg.active():
        class MainUI(UserInterface):
            def assemble(self):
                list_of_files = [PackagedFile(easter_egg.as_requirement_string(), 'packaged_files', 'packaged_file')]
                self.define_static_files('/files', list_of_files)

        wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # How the file would be accessed
        browser.open('/files/packaged_file')
        assert browser.raw_html == 'contents'

class ConcatenateScenarios(Fixture):
    @scenario
    def normal_files(self):
        self.file1_contents = 'contents1'
        self.file2_contents = 'contents2'
        self.filename = 'concatenated'
        self.expected_result = 'contents1contents2'

    @scenario
    def javascript_files(self):
        self.file1_contents = 'acall1(); //some comment'
        self.file2_contents = 'acall2(); //some comment'
        self.filename = 'concatenated.js'
        self.expected_result = 'acall1();acall2();'

    @scenario
    def css_files(self):
        self.file1_contents = '.cool {  text:bold;   }/* a comment */ '
        self.file2_contents = 'a, p { text:white;     } '
        self.filename = 'concatenated.css'
        self.expected_result = '.cool{text:bold}a,p{text:white}'


@with_fixtures(WebFixture, ConcatenateScenarios)
def test_concatenated_files(web_fixture, concatenate_scenarios):
    """Files can also be formed by concatenating other files.  Files ending in .css or .js are appropriately
       minified in the process."""

    fixture = concatenate_scenarios

    # Make an egg with a package called packaged_files, and two files in there.
    egg_dir = temp_dir()
    package_dir = egg_dir.sub_dir('packaged_files')
    init_file = package_dir.file_with('__init__.py', '')
    afile = package_dir.file_with('packaged_file', fixture.file1_contents)
    another_file = package_dir.file_with('packaged_file2', fixture.file2_contents)

    pkg_resources.working_set.add(easter_egg)
    easter_egg.location = egg_dir.name

    class MainUI(UserInterface):
        def assemble(self):
            to_concatenate = [PackagedFile('test==1.0', 'packaged_files', 'packaged_file'),
                              PackagedFile('test==1.0', 'packaged_files', 'packaged_file2')]
            list_of_files = [ConcatenatedFile(fixture.filename, to_concatenate)]
            self.define_static_files('/files', list_of_files)

    with easter_egg.active():
        web_fixture.config.reahlsystem.debug = False  # To enable minification
        wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # How the first file would be accessed
        browser.open('/files/%s' % fixture.filename)
        assert browser.raw_html == fixture.expected_result


@with_fixtures(WebFixture)
def test_file_download_details(web_fixture):
    """FileDownloadStub (the GET response for a StaticFileResource) works correctly in
      different scenarios of partial GETting too."""


    file_content = b'some content'
    server_file = temp_file_with(file_content, 'afile.css', mode='w+b')
    @stubclass(FileDownload)
    class FileDownloadStub(FileDownload):
        chunk_size = 1
    response = FileDownloadStub(FileOnDisk(server_file.name, '/path/for/the/file'))

    # Case: The whole content is sent, in chunk_size bits
    read = [i for i in response.app_iter]
    expected = [bytes((i,)) for i in file_content]
    assert read == expected

    # Case: Headers are set correctly
    assert response.content_type == 'text/css'
    assert not response.content_encoding
    assert response.content_length == len(file_content)

    mtime = datetime.datetime.fromtimestamp(int(os.path.getmtime(server_file.name)))
    assert response.last_modified.replace(tzinfo=None) == mtime
    tag_mtime, tag_size, tag_hash = response.etag.split('-')
    mtime = str(os.path.getmtime(server_file.name))
    assert tag_mtime == mtime
    assert tag_size == str(len(file_content))
    assert tag_hash == str(abs(hash(server_file.name)))

    # Case: conditional response is supported
    assert response.conditional_response

    # Case: partial response is supported - different cases:
    #      - normal case
    actual = [i for i in response.app_iter.app_iter_range(3,7)]
    expected = [bytes((i,)) for i in file_content[3:8]]
    assert actual == expected

    #      - no end specified
    actual = [i for i in response.app_iter.app_iter_range(3)]
    expected = [bytes((i,)) for i in file_content[3:]]
    assert actual == expected

    #      - no start specified
    actual = [i for i in response.app_iter.app_iter_range(end=7)]
    expected = [bytes((i,)) for i in file_content[:8]]
    assert actual == expected

    #      - where the last chunk read would stretch past end
    response.chunk_size = 2
    actual = b''.join([i for i in response.app_iter.app_iter_range(end=6)])
    expected = file_content[:7]
    assert actual == expected

    #      - where start > end
    response.chunk_size = 1
    actual = [i for i in response.app_iter.app_iter_range(start=7, end=3)]
    expected = [b'']
    assert actual == expected

    #      - where start < 0
    actual = [i for i in response.app_iter.app_iter_range(start=-10, end=7)]
    expected = [bytes((i,)) for i in file_content[:8]]
    assert actual == expected

    #      - where end > length of file
    actual = [i for i in response.app_iter.app_iter_range(start=3, end=2000)]
    expected = [bytes((i,)) for i in file_content[3:]]
    assert actual == expected

    #      - where start > length of file
    actual = [i for i in response.app_iter.app_iter_range(start=700)]
    expected = [b'']
    assert actual == expected
