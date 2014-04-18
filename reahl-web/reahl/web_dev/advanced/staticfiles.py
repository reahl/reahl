# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


import StringIO
import datetime
import os.path

import pkg_resources

from nose.tools import istest
from reahl.tofu import Fixture, test, scenario
from reahl.tofu import vassert, expected, temp_dir, temp_file_with
from reahl.stubble import easter_egg, stubclass

from reahl.web.fw import FileOnDisk, FileFromBlob, PackagedFile, ConcatenatedFile, FileDownload, ReahlWSGIApplication, UserInterface
from reahl.web.ui import TwoColumnPage, P
from reahl.webdev.tools import Browser
from reahl.web_dev.fixtures import WebFixture

@istest
class StaticFileTests(object):
    @test(WebFixture)
    def files_from_disk(self, fixture):
        """A directory in the web.static_root configuration setting, can be mounted on a URL
           named after it on the WebApplication.
        """
        static_root = temp_dir()
        files_dir = static_root.sub_dir(u'staticfiles')
        sub_dir = files_dir.sub_dir(u'subdir')
        one_file = files_dir.file_with(u'one_file.xml', u'one')
        nested_file = sub_dir.file_with(u'nested_file', u'other')

        # How the config is set
        fixture.config.web.static_root = static_root.name
        
        # How the subdirectory is mounted
        class MainUI(UserInterface):
            def assemble(self):
                self.define_static_directory(u'/staticfiles')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # How the first file would be accessed
        browser.open('/staticfiles/one_file.xml')
        vassert( browser.raw_html == u'one' )
        
        # The meta-info of the file
        response = browser.last_response
        vassert( response.content_type == u'application/xml' )
        vassert( response.content_encoding is None )
        vassert( response.content_length == 3 )
        expected_mtime = datetime.datetime.fromtimestamp(int(os.path.getmtime(one_file.name)))
        vassert( response.last_modified.replace(tzinfo=None) == expected_mtime )
        expected_tag = u'%s-%s-%s' % (os.path.getmtime(one_file.name), 3, abs(hash(one_file.name)))
        vassert( response.etag == expected_tag )

        # How the file in the subdirectory would be accessed
        browser.open('/staticfiles/subdir/nested_file')
        vassert( browser.raw_html == u'other' )
        
        # When a file does not exist
        browser.open('/staticfiles/one_that_does_not_exist', status=404)

    @test(WebFixture)
    def files_from_list(self, fixture):
        """An explicit list of files can also be added on an URL as if they were in a single
           directory.
        """
        files_dir = temp_dir()
        one_file = files_dir.file_with(u'any_name_will_do_here', u'one')
        
        class MainUI(UserInterface):
            def assemble(self):
                list_of_files = [FileOnDisk(one_file.name, u'one_file')]
                self.define_static_files(u'/morestaticfiles', list_of_files)

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # How the first file would be accessed
        browser.open('/morestaticfiles/one_file')
        vassert( browser.raw_html == u'one' )
        
        # The meta-info of the file
        response = browser.last_response
        vassert( response.content_type == u'application/octet-stream' )
        vassert( response.content_encoding is None )
        vassert( response.content_length == 3 )
        expected_mtime = datetime.datetime.fromtimestamp(int(os.path.getmtime(one_file.name)))
        vassert( response.last_modified.replace(tzinfo=None) == expected_mtime )
        expected_tag = u'%s-%s-%s' % (os.path.getmtime(one_file.name), 3, abs(hash(one_file.name)))
        vassert( response.etag == expected_tag )

        # When a file does not exist
        browser.open('/morestaticfiles/one_that_does_not_exist', status=404)

    @test(WebFixture)
    def files_from_database(self, fixture):
        """Files can also be created on the fly such as from data in a database."""

        class MainUI(UserInterface):
            def assemble(self):
                content_type = u'text/html'
                encoding = u'utf-8'
                size = 10
                mtime = 123
                meta_info = content_type, encoding, size, mtime
                data_blob = StringIO.StringIO(u'x'*size)

                list_of_files = [FileFromBlob(u'database_file', data_blob, *meta_info)]
                self.define_static_files(u'/files', list_of_files)

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # How the file would be accessed
        browser.open('/files/database_file')
        vassert( browser.raw_html == u'xxxxxxxxxx' )
        response = browser.last_response

        # The meta-info of the file
        vassert( response.content_type == u'text/html' )
        vassert( response.content_encoding == u'utf-8' )
        vassert( response.content_length == 10 )
        vassert( response.last_modified.replace(tzinfo=None) == datetime.datetime.fromtimestamp(123) )
        expected_etag = '123-10-%s' % abs(hash(u'database_file'))
        vassert( response.etag == expected_etag )

    @test(WebFixture)
    def packaged_files(self, fixture):
        """Files can also be served straight from a python egg."""

        # Create an egg with package packaged_files, containing the file packaged_file
        egg_dir = temp_dir()
        package_dir = egg_dir.sub_dir(u'packaged_files')
        init_file = package_dir.file_with(u'__init__.py', u'')
        afile = package_dir.file_with(u'packaged_file', u'contents')

        pkg_resources.working_set.add(easter_egg)
        easter_egg.set_module_path(egg_dir.name)
        
        class MainUI(UserInterface):
            def assemble(self):
                list_of_files = [PackagedFile(easter_egg.as_requirement_string(), u'packaged_files', u'packaged_file')]
                self.define_static_files(u'/files', list_of_files)

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # How the file would be accessed
        browser.open('/files/packaged_file')
        vassert( browser.raw_html == u'contents' )

    class ConcatenateScenarios(WebFixture):
        @scenario
        def normal_files(self):
            self.file1_contents = u'contents1'
            self.file2_contents = u'contents2'
            self.filename = u'concatenated'
            self.expected_result = u'contents1contents2'

        @scenario
        def javascript_files(self):
            self.file1_contents = u'acall1(); //some comment'
            self.file2_contents = u'acall2(); //some comment'
            self.filename = u'concatenated.js'
            self.expected_result = u'acall1();acall2();'

        @scenario
        def css_files(self):
            self.file1_contents = u'.cool {}/* a comment */ '
            self.file2_contents = u'a, p { } '
            self.filename = u'concatenated.css'
            self.expected_result = u'.cool{}a,p{}'
            
    @test(ConcatenateScenarios)
    def concatenated_files(self, fixture):
        """Files can also be formed by concatenating other files.  Files ending in .css or .js are appropriately 
           minified in the process."""

        # Make an egg with a package called packaged_files, and two files in there.
        egg_dir = temp_dir()
        package_dir = egg_dir.sub_dir(u'packaged_files')
        init_file = package_dir.file_with(u'__init__.py', u'')
        afile = package_dir.file_with(u'packaged_file', fixture.file1_contents)
        another_file = package_dir.file_with(u'packaged_file2', fixture.file2_contents)

        pkg_resources.working_set.add(easter_egg)
        easter_egg.set_module_path(egg_dir.name)

        class MainUI(UserInterface):
            def assemble(self):
                to_concatenate = [PackagedFile(u'test==1.0', u'packaged_files', u'packaged_file'),
                                  PackagedFile(u'test==1.0', u'packaged_files', u'packaged_file2')]
                list_of_files = [ConcatenatedFile(fixture.filename, to_concatenate)]
                self.define_static_files(u'/files', list_of_files)

        fixture.config.reahlsystem.debug = False  # To enable minification 
        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # How the first file would be accessed
        browser.open('/files/%s' % fixture.filename)
        vassert( browser.raw_html == fixture.expected_result )

    @test(WebFixture)
    def file_download_details(self, fixture):
        """FileDownloadStub (the GET response for a StaticFileResource) works correctly in
          different scenarios of partial GETting too."""
        
        file_content = 'some content'
        server_file = temp_file_with(file_content, 'afile.css')
        @stubclass(FileDownload)
        class FileDownloadStub(FileDownload):
            chunk_size = 1
        response = FileDownloadStub(FileOnDisk(server_file.name, u'/path/for/the/file'))
        
        # Case: The whole content is sent, in chunk_size bits
        read = [i for i in response.app_iter]
        expected = [i for i in file_content]
        vassert( read == expected )

        # Case: Headers are set correctly
        vassert( response.content_type == 'text/css' )
        vassert( not response.content_encoding )
        vassert( response.content_length == len(file_content) )

        mtime = datetime.datetime.fromtimestamp(int(os.path.getmtime(server_file.name)))
        vassert( response.last_modified.replace(tzinfo=None) == mtime )
        tag_mtime, tag_size, tag_hash = response.etag.split('-')
        mtime = str(os.path.getmtime(server_file.name))
        vassert( tag_mtime == mtime )
        vassert( tag_size == str(len(file_content)) )
        vassert( tag_hash == str(abs(hash(server_file.name))) )
        
        # Case: conditional response is supported
        vassert( response.conditional_response )

        # Case: partial response is supported - different cases:
        #      - normal case
        actual = [i for i in response.app_iter.app_iter_range(3,7)]
        expected = [i for i in file_content[3:8]]
        vassert( actual == expected )

        #      - no end specified
        actual = [i for i in response.app_iter.app_iter_range(3)]
        expected = [i for i in file_content[3:]]
        vassert( actual == expected )

        #      - no start specified
        actual = [i for i in response.app_iter.app_iter_range(end=7)]
        expected = [i for i in file_content[:8]]
        vassert( actual == expected )

        #      - where the last chunk read would stretch past end
        response.chunk_size = 2
        actual = ''.join([i for i in response.app_iter.app_iter_range(end=6)])
        expected = file_content[:7]
        vassert( actual == expected )

        #      - where start > end
        response.chunk_size = 1
        actual = [i for i in response.app_iter.app_iter_range(start=7, end=3)]
        expected = ['']
        vassert( actual == expected )

        #      - where start < 0
        actual = [i for i in response.app_iter.app_iter_range(start=-10, end=7)]
        expected = [i for i in file_content[:8]]
        vassert( actual == expected )

        #      - where end > length of file
        actual = [i for i in response.app_iter.app_iter_range(start=3, end=2000)]
        expected = [i for i in file_content[3:]]
        vassert( actual == expected )

        #      - where start > length of file        
        actual = [i for i in response.app_iter.app_iter_range(start=700)]
        expected = ['']
        vassert( actual == expected )

    @test(WebFixture)
    def standard_reahl_files(self, fixture):
        """The framework creates certain static files by default."""
        wsgi_app = ReahlWSGIApplication(fixture.config)
        browser = Browser(wsgi_app)

        browser.open(u'/static/html5shiv-printshiv-3.6.3.js')
        vassert( browser.last_response.content_length > 0 )

        browser.open(u'/static/IE9.js')
        vassert( browser.last_response.content_length > 0 )

        browser.open(u'/static/reahl.js')
        vassert( browser.last_response.content_length > 0 )

        browser.open(u'/static/reahl.css')
        vassert( browser.last_response.content_length > 0 )

        browser.open(u'/static/runningon.png')
        vassert( browser.last_response.content_length > 0 )



