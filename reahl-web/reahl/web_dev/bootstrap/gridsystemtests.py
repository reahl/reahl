# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
#-*- encoding: utf-8 -*-
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

import six

from reahl.tofu import vassert, scenario, expected, test

from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture

from reahl.web.bootstrap.ui import Div

from reahl.component.exceptions import ProgrammerError
from reahl.web.bootstrap.grid import ColumnLayout, ResponsiveSize, Container, DeviceClass


@test(WebFixture)
def containers(fixture):
    """There are two types of Bootstrap containers:  a full width container, and a responsive (fluid) container."""

    widget = Div(fixture.view).use_layout(Container())
    tester = WidgetTester(widget)
    
    css_class = tester.xpath('//div')[0].attrib['class']
    vassert( 'container' == css_class )

    widget = Div(fixture.view).use_layout(Container(fluid=True))
    tester = WidgetTester(widget)
    
    css_class = tester.xpath('//div')[0].attrib['class']
    vassert( 'container-fluid' == css_class )


@test(WebFixture)
def column_layout_basics(fixture):
    """The bootstrap.ColumnLayout adds the correct classes for Bootstrap to lay out its Widget as a row with columns."""

    layout = ColumnLayout(('column_a', ResponsiveSize(lg=4)), ('column_b', ResponsiveSize(lg=8)))
    widget = Div(fixture.view)
    
    vassert( not widget.has_attribute('class') )
    
    widget.use_layout(layout)

    vassert( widget.get_attribute('class') == 'row' )
    column_a, column_b = widget.children

    vassert( 'col-lg-4' in column_a.get_attribute('class')  )
    vassert( 'col-lg-8' in column_b.get_attribute('class')  )


@test(WebFixture)
def column_layout_sizes(fixture):
    """It is mandatory to specify sizes for all columns."""

    with expected(ProgrammerError):
        ColumnLayout('column_a')


@test(WebFixture)
def adding_columns(fixture):
    """You can add additional columns after construction."""

    widget = Div(fixture.view).use_layout(ColumnLayout())

    vassert( not widget.children )

    widget.layout.add_column(ResponsiveSize(lg=4))

    [added_column] = widget.children
    vassert( added_column.get_attribute('class') == 'col-lg-4' )


@test(WebFixture)
def allowed_sizes(fixture):
    """The device classes for which sizes can be specified."""
    size = ResponsiveSize(xs=1, sm=2, md=3, lg=4, xl=5)

    vassert( size == {'xs':1, 'sm':2, 'md':3, 'lg':4, 'xl':5} )


@test(WebFixture)
def column_offsets(fixture):
    """You can optionally specify space to leave empty (an offset) before a column at specific device sizes."""

    layout = ColumnLayout(('column_a', ResponsiveSize(xl=2).offset(xs=2, sm=4, md=6, lg=3, xl=1)))
    widget = Div(fixture.view).use_layout(layout)

    [column_a] = layout.columns.values()

    vassert( 'col-xl-2' in column_a.get_attribute('class')  )
    vassert( 'col-lg-offset-3' in column_a.get_attribute('class')  )
    vassert( 'col-xs-offset-2' in column_a.get_attribute('class')  )
    vassert( 'col-sm-offset-4' in column_a.get_attribute('class')  )
    vassert( 'col-md-offset-6' in column_a.get_attribute('class')  )
    vassert( 'col-xl-offset-1' in column_a.get_attribute('class')  )


@test(WebFixture)
def column_clearfix(fixture):
    """If a logical row spans more than one visual row for a device size, bootstrap clearfixes are
       automatically inserted to ensure cells in resultant visual rows are neatly arranged.
    """

    # Case: Adding a correct clearfix in the right place
    wrapping_layout = ColumnLayout(('column_a', ResponsiveSize(xs=8).offset(xs=2)),
                                   ('column_b', ResponsiveSize(xs=2).offset(xs=2))
    )
    widget = Div(fixture.view).use_layout(wrapping_layout)

    [column_a, clearfix, column_b] = widget.children           
    vassert( [column_a, column_b] == [i for i in wrapping_layout.columns.values()] )
    vassert( 'clearfix' in clearfix.get_attribute('class')  )
    vassert( 'visible-xs-block' in clearfix.get_attribute('class')  )

    # Case: When clearfix needs to take "implicit" sizes of smaller device classes into account
    wrapping_layout = ColumnLayout(('column_a', ResponsiveSize(xs=8).offset(xs=2)),
                                   ('column_b', ResponsiveSize(lg=2).offset(lg=2))
    )
    widget = Div(fixture.view).use_layout(wrapping_layout)

    [column_a, clearfix, column_b] = widget.children           
    vassert( [column_a, column_b] == [i for i in wrapping_layout.columns.values()] )
    vassert( 'clearfix' in clearfix.get_attribute('class')  )
    vassert( 'visible-lg-block' in clearfix.get_attribute('class')  )

    # Case: When no clearfix must be added
    non_wrapping_layout = ColumnLayout(('column_a', ResponsiveSize(xs=2).offset(xs=2)),
                                       ('column_b', ResponsiveSize(xs=2))
    )
    widget = Div(fixture.view).use_layout(non_wrapping_layout)

    [column_a, column_b] = widget.children
    vassert( [column_a, column_b] == [i for i in non_wrapping_layout.columns.values()] )  




@test(WebFixture)
def all_device_classes(fixture):
    """There is a specific list of supported DeviceClasses, in order of device size."""
    device_classes = [ i.class_label for i in DeviceClass.all_classes()]

    vassert( device_classes == ['xs', 'sm', 'md', 'lg', 'xl'] )


@test(WebFixture)
def device_class_identity(fixture):
    """Each supported DeviceClass is identified by a string; you cannot create one that is not supported."""

    device_class = DeviceClass('lg')

    vassert( device_class.class_label == 'lg' )

    def check_ex(ex):
        vassert( six.text_type(ex).startswith('unsupported is not a supported DeviceClass. Should be one of: xs,sm,md,lg,xl'))

    with expected(AssertionError, test=check_ex):
        DeviceClass('unsupported')



@test(WebFixture)
def previous_device_class(fixture):
    """You can find the supported DeviceClass smaller than a given one."""

    device_class = DeviceClass('sm')
    vassert( device_class.one_smaller.class_label == 'xs' )

    # Case: when there is no class smaller than given

    device_class = DeviceClass('xs')
    vassert( device_class.one_smaller == None )


@test(WebFixture)
def previous_device_classes(fixture):
    """You can find the ordered list of all supported DeviceClasses smaller than a given one."""

    device_class = DeviceClass('md')

    previous_device_classes = [ i.class_label for i in device_class.all_smaller]
    vassert( previous_device_classes == ['xs', 'sm'] )

    # Case: when there is no class smaller than given
    device_class = DeviceClass('xs')

    previous_device_classes = device_class.all_smaller
    vassert( previous_device_classes == [] )
