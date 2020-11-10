# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import time

from reahl.stubble import easter_egg, stubclass, EmptyStub
from reahl.tofu import Fixture, set_up, tear_down, scenario, uses, temp_file_with, expected
from reahl.tofu.pytestsupport import with_fixtures

from reahl.dev.xmlreader import XMLReader, DoubleRegistrationException, TagNotRegisteredException


# --------------------------------------------------[ fixtures ]
class BasicObjectSetup(Fixture):
    tag_name = 'anObject'
    string = 'something'
    integer = 234
    def new_file_contents(self):
        return '<%s attr1="%s" attr2="%s"/>' % (self.tag_name, self.string, self.integer)
    def new_file(self):
        return temp_file_with(self.file_contents)
    def new_test_class(self):
        class TestClass:
            def inflate_attributes(self, reader, attributes, parent):
                self.attr2 = int(attributes['attr2'])
                self.attr1 = str(attributes['attr1'])
                self.parent = parent
        return TestClass

    @set_up
    def init_easter_egg(self):
        easter_egg.add_to_working_set()

    @property
    def easter_egg(self):
        return easter_egg

    def new_reader(self):
        return XMLReader([])

    @tear_down
    def close_file(self):
        self.file.close()


@uses(basic_object_setup=BasicObjectSetup)
class ConfiguredReader(Fixture):

    class TestClass1:
        @classmethod
        def get_xml_registration_info(cls):
            return ('1', cls, None)

    class TestClass2:
        @classmethod
        def get_xml_registration_info(cls):
            return ('2', cls, 'asd')

    def new_reader(self):

        @stubclass(XMLReader)
        class XMLReaderStub(XMLReader):
            registered = {}

            def register(self, tag_name, class_to_instantiate, type_name=None):
                self.registered[class_to_instantiate] = (tag_name, class_to_instantiate, type_name)

        return XMLReaderStub([ConfiguredReader.TestClass1, ConfiguredReader.TestClass2])


class TextObjectSetup(BasicObjectSetup):
    def new_test_class(self):
        class TestClass:
            def inflate_text(self, reader, text, parent):
                self.text = text
        return TestClass

    def new_file_contents(self):
        return '<%s>%s</%s>' % (self.tag_name, self.text, self.tag_name)

    @scenario
    def empty_text(self):
        self.text = ''

    @scenario
    def some_text(self):
        self.text = 'some text'


class CompositeObjectSetup(BasicObjectSetup):
    inner_tag_name = 'inner'
    def new_inner_class(self):
        return super().new_test_class()
    
    def new_test_class(self):
        class OuterClass:
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
        class Other:
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
        class OuterClass(super().new_test_class()):
            def inflate_attributes(self, reader, attributes, parent):
                super().inflate_attributes(reader, attributes, parent)
                self.attribute_stamp = time.time()
            def inflate_child(self, reader, child, tag, parent):
                super().inflate_child(reader, child, tag, parent)
                self.child_stamp = time.time()
            def inflate_text(self, reader, text, parent):
                self.child_stamp = time.time()
            def perform_post_inflation_checks(self):
                self.check_stamp = time.time()

        return OuterClass


# --------------------------------------------------[ a basic object ]
@with_fixtures(BasicObjectSetup)
def test_read_basic_object(basic_object_setup):
    fixture = basic_object_setup
    fixture.reader.register(fixture.tag_name, fixture.test_class)
    parent = EmptyStub()
    read_object = fixture.reader.read_file(fixture.file, parent)

    assert isinstance(read_object, fixture.test_class)
    assert read_object.attr1 == fixture.string
    assert read_object.attr2 == fixture.integer
    assert read_object.parent is parent


@with_fixtures(BasicObjectSetup)
def test_exception_on_double_register(basic_object_setup):
    fixture = basic_object_setup
    fixture.reader.register(fixture.tag_name, fixture.test_class)

    with expected(DoubleRegistrationException):
        fixture.reader.register(fixture.tag_name, fixture.test_class)


@with_fixtures(BasicObjectSetup)
def test_exception_on_not_registered(basic_object_setup):
    fixture = basic_object_setup
    with expected(TagNotRegisteredException):
        fixture.reader.read_file(fixture.file, None)


# --------------------------------------------------[ a composite object ]
@with_fixtures(CompositeObjectSetup)
def test_read_composite_object(composite_object_setup):
    fixture = composite_object_setup
    fixture.reader.register(fixture.inner_tag_name, fixture.inner_class)
    fixture.reader.register(fixture.tag_name, fixture.test_class)

    read_object = fixture.reader.read_file(fixture.file, None)

    assert isinstance(read_object, fixture.test_class)
    assert len(read_object.inner) == 1
    child = read_object.inner[0][1]
    child_tag = read_object.inner[0][0]
    assert isinstance(child, fixture.inner_class)
    assert child_tag == fixture.inner_tag_name
    assert child.attr1 == fixture.string
    assert child.attr2 == fixture.integer
    assert child.parent is read_object


@with_fixtures(MultipleClassesForTag)
def test_read_objects_with_same_tag_and_different_type_attribute(multiple_classes_for_tag):
    fixture = multiple_classes_for_tag
    fixture.reader.register(fixture.inner_tag_name, fixture.inner_class, fixture.innerType1)
    fixture.reader.register(fixture.inner_tag_name, fixture.inner_class2, fixture.innerType2)
    fixture.reader.register(fixture.tag_name, fixture.test_class)

    read_object = fixture.reader.read_file(fixture.file, None)

    assert isinstance(read_object, fixture.test_class)
    assert len(read_object.inner) == 2

    assert isinstance(read_object.inner[0][1], fixture.inner_class)
    assert read_object.inner[0][1].attr1 == fixture.string
    assert read_object.inner[0][1].attr2 == fixture.integer

    assert isinstance(read_object.inner[1][1], fixture.inner_class2)


# --------------------------------------------------[ simple object with text content ]
@with_fixtures(TextObjectSetup)
def test_read_text_object(text_object_setup):
    fixture = text_object_setup
    fixture.reader.register(fixture.tag_name, fixture.test_class)
    read_object = fixture.reader.read_file(fixture.file, None)
    if fixture.text:
        assert read_object.text == fixture.text
    else:
        assert not hasattr(read_object, 'text')


# --------------------------------------------------[ order of inflation method calls ]
@with_fixtures(TimeStampedInflationSetup)
def test_order_of_methods_calls_is_correct(time_stamped_inflation_setup):
    fixture = time_stamped_inflation_setup
    fixture.reader.register(fixture.inner_tag_name, fixture.inner_class)
    fixture.reader.register(fixture.tag_name, fixture.test_class)

    read_object = fixture.reader.read_file(fixture.file, None)

    assert read_object.attribute_stamp < read_object.child_stamp < read_object.check_stamp


# --------------------------------------------------[ configuration ]
@with_fixtures(ConfiguredReader)
def test_available_classes_from_plugins_are_registered(configured_reader):
    fixture = configured_reader
    for cls in [fixture.TestClass1, fixture.TestClass2]:
        assert fixture.reader.registered[cls] == cls.get_xml_registration_info()
