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

# -*- mode: python; mode: font-lock -*-
# Copyright 2005 Iwan Vosloo

from __future__ import unicode_literals
from __future__ import print_function
import six
import time

from reahl.stubble import easter_egg, stubclass, EmptyStub
from nose.tools import istest
from reahl.tofu import Fixture, test, set_up, tear_down
from reahl.tofu import temp_file_with, check_limitation, vassert, expected

from reahl.dev.xmlreader import XMLReader, DoubleRegistrationException, TagNotRegisteredException


#--------------------------------------------------[ fixtures ]


class BasicObjectSetup(Fixture):
    tag_name = 'anObject'
    string = 'something'
    integer = 234
    def new_file_contents(self):
        return '<%s attr1="%s" attr2="%s"/>' % (self.tag_name, self.string, self.integer)
    def new_file(self):
        return temp_file_with(self.file_contents)
    def new_test_class(self):
        class TestClass(object):
            def inflate_attributes(self, reader, attributes, parent):
                self.attr2 = int(attributes['attr2'])
                self.attr1 = six.text_type(attributes['attr1'])
                self.parent = parent
        return TestClass

    @set_up
    def init_easter_egg(self):
        easter_egg.add_to_working_set()

    def new_reader(self):
        return XMLReader()

    @tear_down
    def close_file(self):
        self.file.close()


class ConfiguredReader(BasicObjectSetup):
    class TestClass1(object):
        @classmethod
        def get_xml_registration_info(cls):
            return ('1', cls, None)

    class TestClass2(object):
        @classmethod
        def get_xml_registration_info(cls):
            return ('2', cls, 'asd')

    def new_reader(self):
        easter_egg.add_entry_point_from_line('reahl.dev.xmlclasses',
                                     'test1 = reahl.dev_dev.xmlreadertests:ConfiguredReader.TestClass1')
        easter_egg.add_entry_point_from_line('reahl.dev.xmlclasses',
                                     'test2 = reahl.dev_dev.xmlreadertests:ConfiguredReader.TestClass2')

        @stubclass(XMLReader)
        class XMLReaderStub(XMLReader):
            registered = {}
            def register(self, tag_name, class_to_instantiate, type_name=None):
                self.registered[class_to_instantiate] = (tag_name, class_to_instantiate, type_name)

        return XMLReaderStub()


class TextObjectSetup(BasicObjectSetup):
    text = 'somet ext'

    def new_test_class(self):
        class TestClass(object):
            def inflate_text(self, reader, text, parent):
                self.text = text
        return TestClass

    def new_file_contents(self):
        return '<%s>%s</%s>' % (self.tag_name, self.text, self.tag_name)


class EmptyTextObjectSetup(TextObjectSetup):
    text = ''


class CompositeObjectSetup(BasicObjectSetup):
    inner_tag_name = 'inner'
    def new_inner_class(self):
        return super(CompositeObjectSetup, self).new_test_class()
    
    def new_test_class(self):
        class OuterClass(object):
            def inflate_attributes(self, reader, attributes, parent):
                self.inner = []
                self.parent = parent
            def inflate_child(self, reader, child, tag, parent):
                self.inner.append((tag, child))

        return OuterClass

    def new_file_contents(self):
        contents = '''
        <%s>
          <%s attr1="%s" attr2="%s"/>
        </%s>
        ''' % (self.tag_name, self.inner_tag_name, self.string, self.integer, self.tag_name)
        return contents


class MultipleClassesForTag(CompositeObjectSetup):
    inner_tag_name = 'sametag'
    innerType1 = 'onetype'
    innerType2 = 'twotype'

    def new_inner_class2(self):
        class Other(object):
            pass
        return Other

    def new_file_contents(self):
        contents = '''
        <%s>
          <%s type="%s" attr1="%s" attr2="%s"/>
          <%s type="%s"/>
        </%s>
        ''' % (self.tag_name,
               self.inner_tag_name, self.innerType1, self.string, self.integer,
               self.inner_tag_name, self.innerType2,
               self.tag_name)
        return contents


class TimeStampedInflationSetup(CompositeObjectSetup):
    def new_test_class(self):
        class OuterClass(super(TimeStampedInflationSetup, self).new_test_class()):
            def inflate_attributes(self, reader, attributes, parent):
                super(OuterClass, self).inflate_attributes(reader, attributes, parent)
                self.attribute_stamp = time.time()
            def inflate_child(self, reader, child, tag, parent):
                super(OuterClass, self).inflate_child(reader, child, tag, parent)
                self.child_stamp = time.time()
            def inflate_text(self, reader, text, parent):
                self.child_stamp = time.time()
            def perform_post_inflation_checks(self):
                self.check_stamp = time.time()

        return OuterClass


#--------------------------------------------------[ tests ]
@istest
class XMLReaderTests(object):

    @test(Fixture)
    def usage_of_dom_implementation(self, fixture):
        dom_msg = 'DOM Level 3 adds a Load/Store specification, which defines an interface to the reader, but this is not yet available in the Python standard library.'
        check_limitation('2.7', 'More standardised DOM stuff may be available - this implementation uses minidom (from current docs: "%s")' % dom_msg)


    #--------------------------------------------------[ a basic object ]
    @test(BasicObjectSetup)
    def read_basic_object(self, fixture):
        fixture.reader.register(fixture.tag_name, fixture.test_class)
        parent = EmptyStub()
        read_object = fixture.reader.read_file(fixture.file, parent)

        vassert( isinstance(read_object, fixture.test_class) )
        vassert( read_object.attr1 == fixture.string )
        vassert( read_object.attr2 == fixture.integer )
        vassert( read_object.parent is parent )

    @test(BasicObjectSetup)
    def exception_on_double_register(self, fixture):
        fixture.reader.register(fixture.tag_name, fixture.test_class)

        with expected(DoubleRegistrationException):
            fixture.reader.register(fixture.tag_name, fixture.test_class)

    @test(BasicObjectSetup)
    def exception_on_not_registered(self, fixture):
        with expected(TagNotRegisteredException):
            fixture.reader.read_file(fixture.file, None)

    #--------------------------------------------------[ a composite object ]
    @test(CompositeObjectSetup)
    def read_composite_object(self, fixture):
        fixture.reader.register(fixture.inner_tag_name, fixture.inner_class)
        fixture.reader.register(fixture.tag_name, fixture.test_class)

        read_object = fixture.reader.read_file(fixture.file, None)

        vassert(isinstance(read_object, fixture.test_class))
        vassert(len(read_object.inner) == 1)
        child = read_object.inner[0][1]
        child_tag = read_object.inner[0][0]
        vassert(isinstance(child, fixture.inner_class))
        vassert(child_tag == fixture.inner_tag_name)
        vassert(child.attr1 == fixture.string)
        vassert(child.attr2 == fixture.integer)
        vassert(child.parent is read_object)

    @test(MultipleClassesForTag)
    def read_objects_with_same_tag_and_different_type_attribute(self, fixture):
        fixture.reader.register(fixture.inner_tag_name, fixture.inner_class, fixture.innerType1)
        fixture.reader.register(fixture.inner_tag_name, fixture.inner_class2, fixture.innerType2)
        fixture.reader.register(fixture.tag_name, fixture.test_class)

        read_object = fixture.reader.read_file(fixture.file, None)

        vassert(isinstance(read_object, fixture.test_class))
        vassert(len(read_object.inner) == 2)

        vassert(isinstance(read_object.inner[0][1], fixture.inner_class))
        vassert(read_object.inner[0][1].attr1 == fixture.string)
        vassert(read_object.inner[0][1].attr2 == fixture.integer)

        vassert(isinstance(read_object.inner[1][1], fixture.inner_class2))

    #--------------------------------------------------[ simple object with text content ]
    def read_text_object(self, fixture):
        fixture.reader.register(fixture.tag_name, fixture.test_class)
        read_object = fixture.reader.read_file(fixture.file, None)
        if fixture.text:
            vassert(read_object.text == fixture.text)
        else:
            vassert(not hasattr(read_object, 'text'))

    @test(TextObjectSetup)
    def read_non_empty_text_object(self, fixture):
        self.read_text_object(fixture)

    @test(EmptyTextObjectSetup)
    def read_empty_text_object(self, fixture):
        self.read_text_object(fixture)


    #--------------------------------------------------[ order of inflation method calls ]
    @test(TimeStampedInflationSetup)
    def order_of_methods_calls_is_correct(self, fixture):
        fixture.reader.register(fixture.inner_tag_name, fixture.inner_class)
        fixture.reader.register(fixture.tag_name, fixture.test_class)

        read_object = fixture.reader.read_file(fixture.file, None)

        vassert(read_object.attribute_stamp < read_object.child_stamp < read_object.check_stamp)


    #--------------------------------------------------[ configuration ]
    @test(ConfiguredReader)
    def available_classes_from_plugins_are_registered(self, fixture):
        for cls in [fixture.TestClass1, fixture.TestClass2]:
            vassert( fixture.reader.registered[cls] == cls.get_xml_registration_info() )
