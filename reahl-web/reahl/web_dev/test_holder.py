# Copyright 2016-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.tofu import expected
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import WidgetTester
from reahl.component.exceptions import ProgrammerError

from reahl.web.holder.holder import PlaceholderImage, PredefinedTheme, CustomTheme

from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
def test_placeholder_basics(web_fixture):
    """
       hint: Ensure the Holder(Library) is added to the  web.frontend_libraries config setting in the file:web.config.py
    """
    placeholder = PlaceholderImage(web_fixture.view, 20, 30)

    tester = WidgetTester(placeholder)

    expected_html = '<img data-src="holder.js/20x30">'
    actual = tester.render_html()
    assert actual == expected_html


@with_fixtures(WebFixture)
def test_placeholder_with_text(web_fixture):

    placeholder = PlaceholderImage(web_fixture.view, 20, 30, text='My banner')

    expected_value = 'holder.js/20x30?text=My banner'
    actual_value = placeholder.get_attribute('data-src')
    assert actual_value == expected_value


@with_fixtures(WebFixture)
def test_placeholder_with_predefine_theme(web_fixture):

    my_theme = PredefinedTheme('lava')
    placeholder = PlaceholderImage(web_fixture.view, 20, 30, theme=my_theme)

    expected_value = 'holder.js/20x30?theme=lava'
    actual_value = placeholder.get_attribute('data-src')
    assert actual_value == expected_value


@with_fixtures(WebFixture)
def test_text_and_theme_options_are_encoded(web_fixture):

    my_theme = CustomTheme(bg='white', fg='red')
    placeholder = PlaceholderImage(web_fixture.view, 20, 30, text='My sê goed', theme=my_theme)

    expected_value = 'holder.js/20x30?bg=white&fg=red&text=My sê goed'
    actual_value = placeholder.get_attribute('data-src')
    assert actual_value == expected_value


def test_custom_theme_options_become_text():

    my_theme = CustomTheme(bg='yellow', fg='blue',
                           text_size=12, text_font='arial', text_align='left',
                           outline='yes', line_wrap=0.5)

    options_dict = my_theme

    assert options_dict.get('bg') == 'yellow'
    assert options_dict.get('fg') == 'blue'
    assert options_dict.get('size') == '12'
    assert options_dict.get('font') == 'arial'
    assert options_dict.get('align') == 'left'
    assert options_dict.get('outline') == 'yes'
    assert options_dict.get('lineWrap') == '0.5'


def test_custom_theme_text_align_valid_values():

    #valid options
    CustomTheme(text_align='left')
    CustomTheme(text_align='right')
    CustomTheme(text_align=None)

    #invalid
    with expected(ProgrammerError):
        invalid_value = 'somewhere'
        CustomTheme(text_align=invalid_value)
