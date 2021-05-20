# Copyright 2015-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.tofu import expected, NoException
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import WidgetTester

from reahl.component.exceptions import ProgrammerError
from reahl.web.ui import HTMLAttributeValueOption
from reahl.web.bootstrap.ui import Div, P
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container, DeviceClass, Alignment, ContentJustification

from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
def test_containers(web_fixture):
    """There are two types of Bootstrap containers:  a full width container, and a responsive (fluid) container."""


    widget = Div(web_fixture.view).use_layout(Container())
    tester = WidgetTester(widget)

    css_class = tester.xpath('//div')[0].attrib['class']
    assert 'container' == css_class

    widget = Div(web_fixture.view).use_layout(Container(fluid=True))
    tester = WidgetTester(widget)

    css_class = tester.xpath('//div')[0].attrib['class']
    assert 'container-fluid' == css_class


def test_responsive_size():
    """A ResponsiveSize is a way to state what size something should be on each mentioned DeviceClass."""

    responsive_size = ResponsiveSize(xs=1, sm=2, lg=None)

    specified_sizes = responsive_size.device_options

    assert DeviceClass('lg') not in specified_sizes
    assert specified_sizes == {DeviceClass('xs'): 1, DeviceClass('sm'): 2}


@with_fixtures(WebFixture)
def test_column_layout_basics(web_fixture):
    """A ColumnLayout turns its Widget into a sequence of columns, each of which is a Div laid with the given width per device class."""

    layout = ColumnLayout(ColumnOptions('column_a', size=ResponsiveSize(lg=4)),
                          ColumnOptions('column_b', size=ResponsiveSize(lg=8)))
    widget = Div(web_fixture.view)

    assert not widget.has_attribute('class')
    assert not widget.children

    widget.use_layout(layout)

    assert widget.get_attribute('class') == 'row'
    column_a, column_b = widget.children

    assert 'col-lg-4' in column_a.get_attribute('class')
    assert 'col-lg-8' in column_b.get_attribute('class')


@with_fixtures(WebFixture)
def test_column_layout_unspecified_size(web_fixture):
    """Specifying a size of True for a device class means that the size is automatically computed by dividing available
       space equally amongst all the columns so specified."""

    layout = ColumnLayout(ColumnOptions('column_a', size=ResponsiveSize(lg=True)), ColumnOptions('column_b', size=ResponsiveSize(lg=True)))
    widget = Div(web_fixture.view)

    widget.use_layout(layout)

    column_a, column_b = widget.children

    assert 'col-lg' in column_a.get_attribute('class')
    assert 'col-lg' in column_b.get_attribute('class')


@with_fixtures(WebFixture)
def test_column_layout_default_options(web_fixture):
    """You can also pass only column names instead of ColumnOptions objects in which case the column will be configured with default ColumnOptions."""
    widget = Div(web_fixture.view)

    widget.use_layout(ColumnLayout('column_a'))

    [column_a] = widget.children

    assert 'col' in column_a.get_attribute('class')


@with_fixtures(WebFixture)
def test_order_of_columns(web_fixture):
    """Columns are added in the order given to the ColumnLayout constructor, and the Div representing each column
       can be obtained using dictionary access on Layout.columns."""

    fixture = web_fixture

    widget = Div(fixture.view).use_layout(ColumnLayout(ColumnOptions('column_name_a'), ColumnOptions('column_name_b')))

    column_a = widget.layout.columns['column_name_a']
    column_b = widget.layout.columns['column_name_b']

    first_column, second_column = widget.children

    assert first_column is column_a
    assert second_column is column_b


@with_fixtures(WebFixture)
def test_columns_classes(web_fixture):
    """The Div added for each column specified to ColumnLayout is given a CSS class derived from the column name."""

    fixture = web_fixture

    widget = Div(fixture.view).use_layout(ColumnLayout('column_name_a'))
    column_a = widget.layout.columns['column_name_a']
    assert 'column-column_name_a' in column_a.get_attribute('class')


@with_fixtures(WebFixture)
def test_column_slots(web_fixture):
    """A ColumnLayout can be made that adds a Slot to each added column, named after the column it is added to."""

    fixture = web_fixture

    widget = Div(fixture.view).use_layout(ColumnLayout('column_name_a', 'column_name_b').with_slots())

    column_a, column_b = widget.layout.columns.values()
    assert 'column_name_a' in column_a.available_slots
    assert 'column_name_b' in column_b.available_slots


@with_fixtures(WebFixture)
def test_column_gutters(web_fixture):
    """A ColumnLayout can be made that does not include gutters in the layout."""

    fixture = web_fixture

    widget = Div(fixture.view).use_layout(ColumnLayout('column_name_a', 'column_name_b').without_gutters())

    assert 'no-gutters' in widget.get_attribute('class').split()


@with_fixtures(WebFixture)
def test_adding_columns_later(web_fixture):
    """You can add additional columns after construction by calling add_column on the ColumnLayout."""

    widget = Div(web_fixture.view).use_layout(ColumnLayout())

    assert not widget.children

    widget.layout.add_column('a_column', size=ResponsiveSize(lg=4))

    [added_column] = widget.children
    assert isinstance(added_column, Div)
    assert added_column.get_attribute('class') == 'col-lg-4 column-a_column'


@with_fixtures(WebFixture)
def test_adding_columns_later_specifying_the_widget_to_use(web_fixture):
    """Specify the widget to use as a wrapper for the column. By default it is a Div"""

    widget = Div(web_fixture.view).use_layout(ColumnLayout())

    column_widget_to_use = P(web_fixture.view)
    widget.layout.add_column('a_column', column_widget=column_widget_to_use)

    [added_column] = widget.children
    assert added_column is column_widget_to_use


def test_allowed_sizes():
    """The device classes for which sizes can be specified."""
    size = ResponsiveSize(xs=1, sm=2, md=3, lg=4, xl=5)

    assert size.device_options == {DeviceClass('xs'):1, DeviceClass('sm'):2, DeviceClass('md'):3, DeviceClass('lg'):4, DeviceClass('xl'):5}


@with_fixtures(WebFixture)
def test_column_offsets(web_fixture):
    """You can optionally specify space to leave empty (an offset) before a column at specific device sizes."""

    layout = ColumnLayout(ColumnOptions('column_a', size=ResponsiveSize(xl=2), offsets=ResponsiveSize(xs=2, sm=4, md=6, lg=3, xl=1)))
    widget = Div(web_fixture.view).use_layout(layout)

    [column_a] = layout.columns.values()

    assert 'col-xl-2' in column_a.get_attribute('class')
    assert 'offset-lg-3' in column_a.get_attribute('class')
    assert 'offset-2' in column_a.get_attribute('class')
    assert 'offset-sm-4' in column_a.get_attribute('class')
    assert 'offset-md-6' in column_a.get_attribute('class')
    assert 'offset-xl-1' in column_a.get_attribute('class')


@with_fixtures(WebFixture)
def test_column_clearfix(web_fixture):
    """If a logical row spans more than one visual row for a device size, bootstrap clearfixes are
       automatically inserted to ensure cells in resultant visual rows are neatly arranged.
    """

    # Case: Adding a correct clearfix in the right place
    wrapping_layout = ColumnLayout(ColumnOptions('column_a', size=ResponsiveSize(md=8), offsets=ResponsiveSize(md=2)),
                                   ColumnOptions('column_b', size=ResponsiveSize(md=2), offsets=ResponsiveSize(md=2))
    )
    widget = Div(web_fixture.view).use_layout(wrapping_layout)

    [column_a, clearfix, column_b] = widget.children
    assert [column_a, column_b] == [i for i in wrapping_layout.columns.values()]
    assert 'clearfix' in clearfix.get_attribute('class')
    assert 'hidden-sm' in clearfix.get_attribute('class')

    # Case: When clearfix needs to take "implicit" sizes of smaller device classes into account
    wrapping_layout = ColumnLayout(ColumnOptions('column_a', size=ResponsiveSize(xs=8), offsets=ResponsiveSize(xs=2)),
                                   ColumnOptions('column_b', size=ResponsiveSize(lg=2), offsets=ResponsiveSize(lg=2))
    )
    widget = Div(web_fixture.view).use_layout(wrapping_layout)

    [column_a, clearfix, column_b] = widget.children
    assert [column_a, column_b] == [i for i in wrapping_layout.columns.values()]
    assert 'clearfix' in clearfix.get_attribute('class')
    assert 'hidden-md' in clearfix.get_attribute('class')

    # Case: When no clearfix must be added
    non_wrapping_layout = ColumnLayout(ColumnOptions('column_a', size=ResponsiveSize(xs=2), offsets=ResponsiveSize(xs=2)),
                                       ColumnOptions('column_b', size=ResponsiveSize(xs=2))
    )
    widget = Div(web_fixture.view).use_layout(non_wrapping_layout)

    [column_a, column_b] = widget.children
    assert [column_a, column_b] == [i for i in non_wrapping_layout.columns.values()]


@with_fixtures(WebFixture)
def test_vertical_alignment(web_fixture):
    """You can specify how columns are aligned vertically and override the alignment of a specific column."""

    widget = Div(web_fixture.view).use_layout(ColumnLayout().with_vertical_alignment(Alignment(md='center')))

    defaulted_column = widget.layout.add_column('default_column')
    specifically_overridden_column = widget.layout.add_column('overridden_column', vertical_align=Alignment(md='end'))

    assert 'align-items-md-center' in widget.get_attribute('class').split()
    assert 'align-self-md-end' in specifically_overridden_column.get_attribute('class').split()
    assert 'align' not in defaulted_column.get_attribute('class')


@with_fixtures(WebFixture)
def test_horizontal_alignment(web_fixture):
    """You can specify how columns are aligned horizontally."""

    widget = Div(web_fixture.view).use_layout(ColumnLayout().with_justified_content(ContentJustification(md='around')))

    assert 'justify-content-md-around' in widget.get_attribute('class').split()


def test_allowed_string_options():
    """The value of an HTMLAttributeValueOption is constrained to one of its stated valid options if it is set."""
    with expected(NoException):
        HTMLAttributeValueOption('validoption', True, constrain_value_to=['anoption', 'anotheroption', 'validoption'])

    with expected(NoException):
        HTMLAttributeValueOption('invalidoption', False, constrain_value_to=['anoption', 'anotheroption', 'validoption'])

    with expected(ProgrammerError):
        HTMLAttributeValueOption('invalidoption', True, constrain_value_to=['anoption', 'anotheroption', 'validoption'])


def test_composed_class_string():
    """A HTMLAttributeValueOption be made into as a css class string."""
    style_class = HTMLAttributeValueOption('validoption', True, prefix='pre', constrain_value_to=['validoption'])
    assert style_class.as_html_snippet() == 'pre-validoption'


def test_all_device_classes():
    """There is a specific list of supported DeviceClasses, in order of device size."""
    device_classes = [i.name for i in DeviceClass.all_classes()]

    assert device_classes == ['xs', 'sm', 'md', 'lg', 'xl']


def test_device_class_identity():
    """Each supported DeviceClass is identified by a string; you cannot create one that is not supported."""

    device_class = DeviceClass('lg')

    assert device_class.name == 'lg'

    with expected(ProgrammerError, test='Invalid device class name: unsupported, should be one of xs,sm,md,lg,xl.*'):
        DeviceClass('unsupported')


def test_previous_device_class():
    """You can find the supported DeviceClass smaller than a given one."""

    device_class = DeviceClass('sm')
    assert device_class.one_smaller.name == 'xs'

    # Case: when there is no class smaller than given

    device_class = DeviceClass('xs')
    assert device_class.one_smaller is None


def test_previous_device_classes():
    """You can find the ordered list of all supported DeviceClasses smaller than a given one."""

    device_class = DeviceClass('md')

    previous_device_classes = [ i.name for i in device_class.all_smaller]
    assert previous_device_classes == ['xs', 'sm']

    # Case: when there is no class smaller than given
    device_class = DeviceClass('xs')

    previous_device_classes = device_class.all_smaller
    assert previous_device_classes == []
