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

"""A generic factory that can construct Python classes from XML.

This package provides infrastructure that will read an XML file with
clean, human readable XML and provide you with a bunch of classes that
have been constructed and initialised according to the information in
the XML file.

The XML can look like one of the following:

 1. <mytag>asdasd</mytag>
 1. <mytag type='atype'>asfasfd</mytag>

Classes are registered for a specific XML element name and type
combination.

To be able to register a class, it should have the following class
method:

    @classmethod
    def get_xml_registration_info(cls):
        return ( <tag>, cls, <type> )

Where: cls is the class that will be instantiated when XML element
    <tag> with type attribute <type> is encountered.

    Speficying None for <type> means that cls will be instantiated iff
    an XML element with name <tag> is encountered and it does not have
    a 'type=' attribute.


Registered classes further may have the following methods which will
be called by this package in order to initialise a newly created
instance:

  def inflate_attributes(self, reader, attributes, parent)

    This is the very first call to a newly created instance.  The
    class should be initialised here and all its simple attributes
    set.

      - reader is the XMLReader which is constructing the class.
      - attributes is a dictionary with all the XML attributes
         specified for the XML element that triggered this class
         instantiation
      - parent is the object which was constructed from the parent
         element of the current XML element (it may be None)

  def inflate_child(self, reader, child, tag, parent)

    If an element has children elements, that means the constructed
    class has attributes that are also class instances.  In this case,
    as each child is inflated, this method will be called on its
    parent so that the parent can set its attribute.

      - reader is the XMLReader which is constructing the class.
      - child is the newly instantiated child class instance
      - tag is the XML element name which triggered the instantiation
        of the child
      - parent is the object which was constructed from the parent
         element of the current XML element (it may be None)

  def inflate_text(self, reader, text, parent)

    Sometimes an element will have nothing but text in it.  In such a
    case, this method is called on the constructed class

      - reader is the XMLReader which is constructing the class.
      - text is the text
      - parent is the object which was constructed from the parent
         element of the current XML element (it may be None)

  def perform_post_inflation_checks(self)

    This method is called after all other methods have been called.
    It can be used to check that a class has been properly
    initialised.


"""

from xml.dom.minidom import parse


#--------------------------------------------------[ XMLReaderException ]
class XMLReaderException(Exception):
    """All exceptions of this module are derived from this one."""


#--------------------------------------------------[ DoubleRegistrationException ]
class DoubleRegistrationException(XMLReaderException):
    """Raised when an attempt is made to register the same tag more than once."""


#--------------------------------------------------[ TagNotRegisteredException ]
class TagNotRegisteredException(XMLReaderException):
    """Raised when a tag was encountered during XML parsing for which no class is registered."""


#--------------------------------------------------[ TagTypeTuple ]
class TagTypeTuple(tuple):
    """A tuple of (tag,type) with easy accessors for its elements."""
    def __new__(cls, arg):
        assert len(arg) == 2, 'Programming error: you must supply both tag and type'
        return super().__new__(cls, arg)
    def tag(self):
        return self[0]
    def type(self):
        return self[1]


#--------------------------------------------------[ XMLReader ]
class XMLReader:
    """This class is used to read python objects from an XML file."""
    def __init__(self, xml_classes):
        self.map = {}
        for cls in xml_classes:
            self.register(*cls.get_xml_registration_info())

    def register(self, tag_name, class_to_instantiate, type_name=None):
        tag_type_tuple = TagTypeTuple((tag_name, type_name))

        if tag_type_tuple in self.map:
            message = 'Tag "%s" with type "%s" already registered for class %s' % \
                      (tag_name, type_name, self.map[tag_type_tuple],)
            raise DoubleRegistrationException(message)

        self.map[tag_type_tuple] = class_to_instantiate

    def read_file(self, input_file, parent):
        dom = parse(input_file)
        element = dom.documentElement

        result = self.to_object(element, parent)
        dom.unlink()

        return result

    def to_object(self, dom_element, parent_object):
        type_name = None
        if dom_element.hasAttribute('type'):
            type_name = dom_element.getAttribute('type')

        tag_type_tuple = TagTypeTuple((dom_element.tagName, type_name))

        if tag_type_tuple not in self.map:
            message = 'No class registered for tag "%s", type "%s"' % tag_type_tuple
            raise TagNotRegisteredException(message)

        class_to_instantiate = self.map[tag_type_tuple]
        instance = class_to_instantiate.__new__(class_to_instantiate)

        self.call_if_present(instance, 'inflate_attributes',
                           self, dict(dom_element.attributes.items()), parent_object)

        dom_element.normalize()
        for element in dom_element.childNodes:
            if element.nodeType == element.ELEMENT_NODE:
                child = self.to_object(element, instance)
                self.call_if_present(instance, 'inflate_child',
                                   self, child, element.tagName, parent_object)
            if element.nodeType == element.TEXT_NODE:
                text = element.data
                self.call_if_present(instance, 'inflate_text', self, text, parent_object)

        self.call_if_present(instance, 'perform_post_inflation_checks')

        return instance

    def call_if_present(self, instance, function_name, *args, **kwargs):
        if hasattr(instance, function_name):
            getattr(instance, function_name)(*args, **kwargs)


