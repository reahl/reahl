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


import io
import re
import contextlib
import itertools
import json
import urllib.parse
import logging
from http.cookiejar import Cookie
from http.client import CannotSendRequest

from webtest import TestApp
from lxml import html
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

# See: https://github.com/Pylons/webtest/issues/8
from webtest.forms import Field, Form
def patch(cls):
    if hasattr(cls, '__orig__init__'):
        return
    cls.__orig__init__ = cls.__init__
    def patched_init(self, form_, *args, **kwargs):
        form = kwargs.pop('form', None)
        cls.__orig__init__(self, form_, *args, **kwargs)
        if form:
            self.attrs['form'] = form
    cls.__init__ = patched_init

def patch_Field():
    patch(Form.FieldClass)
    for k, v in list(Field.classes.items()):
        patch(v)


class BasicBrowser:

    def view_source(self):
        for line in html.tostring(self.lxml_html, pretty_print=True, encoding='unicode').split('\n'): 
            print(line, flush=True)

    def save_source(self, filename):
        with io.open(filename, 'w') as html_file:
            html_file.write(self.raw_html)

    def is_element_present(self, locator):
        xpath = str(locator)
        return len(self.lxml_html.xpath(xpath)) > 0

    @property
    def lxml_html(self):
        if self.raw_html:
            return html.fromstring(self.raw_html)
        return None

    def xpath(self, xpath):
        """Returns the `lmxl Element <http://lxml.de/>`_ found by the given `xpath`."""
        return self.lxml_html.xpath(str(xpath))

    def get_xpath_count(self, locator):
        """Answers the number of elements matching `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return len(self.xpath(str(locator)))

    def get_html_for(self, locator):
        """Returns the HTML of the element (including its own tags) targeted by the given `locator`

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = str(locator)
        element = self.xpath(xpath)[0]
        return html.tostring(element, encoding='unicode')

    def get_inner_html_for(self, locator):
        """Returns the HTML of the children of the element targeted by the given `locator` (excluding the 
           element's own tags).

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = str(locator)
        element = self.xpath(xpath)[0]
        return ''.join(html.tostring(child, encoding='unicode') for child in element.getchildren())

    def get_id_of(self, locator):
        xpath = str(locator)
        element = self.xpath(xpath)[0]
        return element.attrib['id']


class WidgetTester(BasicBrowser):
    """A WidgetTester is used to render the contents of a :class:`reahl.web.fw.Widget` instance.

       :param widget: The Widget instance to be tested.
    """
    def __init__(self, widget):
        self.widget = widget

    @property
    def raw_html(self):
        """The HTML rendered by the Widget."""
        return self.render_html()

    def render_html(self):
        """Returns the HTML rendered by the Widget."""
        return self.widget.render()

    def render_html_tree(self):
        """Returns an `lxml tree <http://lxml.de/>`_ of HTML elements rendered by the Widget."""
        return html.fromstring(self.render_html())

    def render_js(self):
        """Returns the JavaScript that would be rendered for the Widget in the page header."""
        return ' '.join(self.widget.get_js())


class Browser(BasicBrowser):
    """A Browser that can be used to test a WSGI application in the current thread, without the need for a separate
       web server. This class implements methods matching the actions a user would perform using a browser.

       :param wsgi_app: The application instance under test.
    """
    def __init__(self, wsgi_app):
        self.testapp = TestApp(wsgi_app)
        self.last_response = None
        self.history = []

    def open(self, url_string, follow_redirects=True, **kwargs):
        """GETs the URL in `url_string`.

           :param url_string: A string containing the URL to be opened.
           :keyword follow_redirects: If False, this method acts as a simple GET request. If True (the default),
                                      the method behaves like a browser would, by opening redirect responses.

           Other keyword arguments are passed directly on to 
           `WebTest.get <http://webtest.readthedocs.org/en/latest/api.html#webtest.app.TestApp.get>`_.

        """
        if self.last_response:
            self.history.append(self.last_response.request.url)
        relative = not url_string.startswith('/')
        if relative:
            url_string = self.get_full_path(url_string)
        self.last_response = self.testapp.get(url_string, **kwargs)
        if follow_redirects:
            self.follow_response()

    def go_back(self):
        """GETs the previous location (like the back button on a browser).
        """
        previous = self.history.pop()
        self.open(previous)

    def refresh(self):
        """GETs the current location again (like the refresh button on a browser).
        """
        self.open(self.last_request.url)

    def follow_response(self):
        """Assuming the last response received was a redirect, follows that response
          (and other redirect responses that may be received in the process until
          a response is received which is not a redirect.
        """
        counter = 0
        while self.status >= 300 and self.status < 400:
            self.last_response = self.last_response.follow()
            counter += 1
            assert counter <= 10, 'HTTP Redirect loop detected.'

    def post(self, url_string, form_values, **kwargs):
        """POSTs the given form values to the url given.

           :param url_string: A string containing the URL to be posted to.
           :param form_values: A dictionary containing form data in its key/value pairs.

           Other keyword arguments are passed directly on to 
           `WebTest.post <http://webtest.readthedocs.org/en/latest/api.html#webtest.app.TestApp.post>`_.
        """
        self.last_response = self.testapp.post((url_string), form_values, **kwargs)

    def relative(self, url_string):
        url_bits = urllib.parse.urlparse(url_string)
        return urllib.parse.urlunparse(('', '', url_bits.path, url_bits.params, url_bits.query, url_bits.fragment))

    @property
    def raw_html(self):
        """Returns the HTML for the current location unchanged."""
        return self.last_response.body.decode('utf-8')

    @property
    def status(self):
        """Returns the HTTP status code for the last response."""
        return int(self.last_response.status.split(' ')[0])

    @property
    def title(self):
        """Returns the title of the current location."""
        titles = self.xpath('/html/head/title')
        assert len(titles) > 0, 'Error: no title element found'
        return titles[0].text

    @property
    def last_request(self):
        """Returns the last request."""
        return self.last_response.request

    @property
    def current_url(self):
        """Returns the :class:`reahl.web.fw.Url` of the current location.

        .. versionadded:: 5.0
        """
        return urllib.parse.urlparse(self.last_response.request.url, allow_fragments=True)

    def get_form_for(self, locator):
        """Return the form for the given `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = str(locator)
        form_id = self.xpath('%s[@form]' % xpath)[0].attrib['form']
        form_element = self.xpath('//form[@id=\'%s\']' % form_id)[0]
        patch_Field()
        return self.last_response.forms[form_element.attrib['id']]

    def type(self, locator, text):
        """Types the text in `text` into the input found by the `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param text: The text to be typed.
        """
        xpath = str(locator)
        inputs = self.xpath(xpath) 
        assert len(inputs) == 1
        form = self.get_form_for(xpath)
        form.fields[inputs[0].name][0].value = text

    def click(self, locator, **kwargs):
        """Clicks on the element found by `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.

           Other keyword arguments are passed directly on to 
           `Form.submit <http://webtest.readthedocs.org/en/latest/api.html#webtest.forms.Form.submit>`_.
        """
        xpath = str(locator)
        buttons = self.xpath(xpath)
        assert len(buttons) == 1, 'Could not find one (and only one) button for %s' % locator
        button = buttons[0]
        if button.tag == 'input' and button.attrib['type'] == 'submit':
            button_name = self.xpath(xpath)[0].name
            form = self.get_form_for(xpath)
            form.action = self.relative(form.action)
            self.last_response = form.submit(button_name, **kwargs)
            self.follow_response()
        elif button.tag == 'a':
            self.open(button.attrib['href'], **kwargs)
        elif button.tag == 'input' and button.type == 'checkbox':
            form = self.get_form_for(xpath)
            [checkbox] = form.fields[button.name]
            checkbox.value = 'on' if not checkbox.value else None
        else:    
            raise AssertionError('This browser can only click on buttons, a elements, or checkboxes')

    def select(self, locator, label_to_choose):
        """Finds the select element indicated by `locator` and selects one of its options.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param label_to_choose: The label of the option that should be selected.
        """
        xpath = str(locator)
        select = self.xpath(xpath)
        assert len(select) == 1, 'Could not find one (and only one) element for %s' % locator
        select = select[0]
        assert select.tag == 'select', 'Expected %s to find a select tag' % locator

        form = self.get_form_for(xpath)
        for option in select.findall('option'):
            if option.text == label_to_choose:
                form[select.attrib['name']] = option.attrib['value']
                return
        raise AssertionError('Option %s not found' % label_to_choose)

    def select_many(self, locator, labels_to_choose):
        """Finds the select element indicated by `locator` and selects the options labelled as such.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param labels_to_choose: The labels of the options that should be selected.
        """
        xpath = str(locator)
        select = self.xpath(xpath)
        assert len(select) == 1, 'Could not find one (and only one) element for %s' % locator
        select = select[0]
        assert select.tag == 'select', 'Expected %s to find a select tag' % locator

        form = self.get_form_for(xpath)

        options_to_select = []
        for option in select.findall('option'):
            if option.text in labels_to_choose:
                options_to_select.append(option)

        form[select.attrib['name']] = [option.attrib['value'] for option in options_to_select]

        if len(options_to_select) != len(options_to_select):
            raise AssertionError('Could only select options labelled[%s] not all of [%s]' %
                                 (','.join([option.text for option in options_to_select]), ','.join(labels_to_choose)))

    def select_none(self, locator):
        """Finds the select element indicated by `locator` and ensure nothing is selected.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = str(locator)
        select = self.xpath(xpath)
        assert len(select) == 1, 'Could not find one (and only one) element for %s' % locator
        select = select[0]
        assert select.tag == 'select', 'Expected %s to find a select tag' % locator

        form = self.get_form_for(xpath)
        form[select.attrib['name']] = []

    def get_value(self, locator):
        """Returns the value of the input indicated by `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = str(locator)
        inputs = self.xpath(xpath)
        assert len(inputs) == 1
        form = self.get_form_for(xpath)
        return form.fields[inputs[0].name][0].value

    def get_full_path(self, relative_path):
        return urllib.parse.urljoin(self.current_url.path, relative_path)

    def is_image_shown(self, locator):
        """Answers whether the located image is available from the server (ie, whether the src attribute 
           of an img element is accessible).

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = str(locator)
        try:
            img_src = self.lxml_html.xpath(xpath)[0].attrib['src']
            self.open(img_src)
            self.go_back()
        except:
            return False
        return True

    def create_cookie(self, cookie_dict):
        """Creates a cookie from the given `cookie_dict`.

           :param cookie_dict: A dictionary with two keys: 'name' and 'value'. The values of these\
                               keys are the name of the cookie and its value, respectively.
                               The keys  'path', 'domain', 'secure', 'expiry' can also be set to values.\
                               These have the respective meanings as defined in `RFC6265 <http://tools.ietf.org/html/rfc6265#section-5.2>`
        """
        name = cookie_dict['name']
        value = cookie_dict['value']
        path = cookie_dict.get('path', '')
        path_set = path != ''
        domain = cookie_dict.get('domain', '')
        domain_set = domain != ''
        secure = cookie_dict.get('secure', False)
        expires = cookie_dict.get('expiry', None)
        cookie = Cookie(0, name, value, None, False, domain, domain_set, False, path, path_set,
                        secure, expires, False, None, None, {})
        self.testapp.cookiejar.set_cookie(cookie)

    def is_element_enabled(self, locator):
        """Answers whether the located element is reactive to user commands or not. For <a> elements,
           this means that they have an href attribute, for inputs it means that they are not disabled.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = str(locator)
        [element] = self.xpath(xpath)
        if element.tag == 'a':
            return 'href' in element.attrib
        if element.tag == 'input':
            return 'disabled' not in element.attrib
        assert None, 'Not yet implemented'


class XPath:
    """An object to build an XPath expression for locating a particular element on a web page.
       A programmer is not supposed to instantiate an XPath directly. Use one of the descriptive
       class methods to instantiate an XPath instance, then build more complex expressions using the instance methods.

       An XPath expression in a string is returned when an XPath object is cast to str.

       Examples:
           >>> str(XPath.div().including_class('alert'))
           '//div[contains(concat(" ", @class, " "), " alert ")]

           >>> XPath.button_labelled('Save').inside_of(XPath.div().including_class('myclass'))
           XPath('//div[contains(concat(" ", @class, " "), " myclass ")]/.//button[normalize-space()=normalize-space("Save")]|//div[contains(concat(" ", @class, " "), " myclass ")]/.//input[normalize-space(@value)=normalize-space("Save")]')


       .. versionchanged:: 5.0
          Removed .checkbox_in_table_row() method.

       .. versionchanged:: 5.0
          Made XPath instances composable (added .inside_of).

       .. versionchanged:: 5.0
          Added __getitem__ so that something like .table()[5] gives you the 5th table in its parent.

       .. versionchanged:: 5.0
          Removed .error_label_containing()

       .. versionchanged:: 5.0
          Removed .span_containing()

       .. versionchanged:: 5.0
          Removed .div_containing()

       .. versionchanged:: 5.0
          Removed .paragraph_containing()

       .. versionchanged:: 5.0
          Removed .legend_with_text()

       .. versionchanged:: 5.0
          Removed .link_starting_with_text()

       .. versionchanged:: 5.0
          Removed .link_with_text()

       .. versionchanged:: 5.0
          Removed .table_cell_with_text()

       .. versionchanged:: 5.0
          Removed .heading_with_text()

       .. versionchanged:: 5.0
          Removed .label_with_text()

       .. versionchanged:: 5.0
          Removed .caption_with_text()

       .. versionchanged:: 5.0
          Removed .option_with_text()
    """
    def __init__(self, *xpaths):
        self.xpaths = xpaths

    def __str__(self):
        return self.xpath

    def __repr__(self):
        return '%s(\'%s\')' % (self.__class__.__name__, str(self))

    def __getitem__(self, n):
        """Returns an XPath for the nth positioned element matching the current element.
           Can also be used to construct an XPath with an xpath condition (as a string) in the [].

           .. versionadded:: 5.0
        """
        return self.__class__(*['%s[%s]' % (xpath, n) for xpath in self.xpaths])

    @property
    def xpath(self):
        return '|'.join(self.xpaths)

    def inside_of(self, another):
        """Returns an XPath that is positioned inside of another.

           .. versionadded:: 5.0
        """
        return self.__class__(*['%s/%s%s' % (b,'.' if a.startswith('/') else '', a) for a, b in itertools.product(self.xpaths, another.xpaths)])

    def __or__(self, other):
        """Returns an XPath that matches one of self or other.

           .. versionadded:: 5.0
        """
        return self.__class__(*(self.xpaths + other.xpaths))

    def including_class(self, css_class):
        """Returns an XPath that additionally has a given css_class.

           .. versionadded:: 5.0
        """
        return self.__class__(*['%s[contains(concat(" ", @class, " "), " %s ")]' % (xpath, css_class) for xpath in self.xpaths])

    @classmethod
    def delimit_text(cls, text):
        bits = text.split('"')
        if len(bits) > 1:
            return 'concat(%s)' % (',\'"\','.join(['"%s"' % bit for bit in bits]))
        else:
            return '"%s"' % text

    def with_id(self, text):
        """Returns an XPath that additionally has the id.

           .. versionadded:: 5.0
        """
        return self.__class__(*['%s[@id=%s]' % (xpath, self.delimit_text(text)) for xpath in self.xpaths])

    def with_text(self, text):
        """Returns an XPath that additionally matches the given text exactly.

           .. versionadded:: 5.0
        """
        return self.__class__(*['%s[normalize-space()=normalize-space(%s)]' % (xpath, self.delimit_text(text)) for xpath in self.xpaths])

    def including_text(self, text):
        """Returns an XPath that additionally includes text matching the given text.

           .. versionadded:: 5.0
        """
        return self.__class__(*['%s[contains(normalize-space(), normalize-space(%s))]' % (xpath, self.delimit_text(text)) for xpath in self.xpaths])

    def with_text_starting(self, text):
        """Returns an XPath that additionally has text that starts with the given text.

           .. versionadded:: 5.0
        """
        return self.__class__(*['%s[starts-with(normalize-space(), normalize-space(%s))]' % (xpath, self.delimit_text(text)) for xpath in self.xpaths])

    def containing(self, another):
        """Returns an XPath that additionally contains another XPath.

           .. versionadded:: 5.0
        """
        return self.__class__(*[final_xpath for xpath in another.xpaths for final_xpath in self[re.sub(r'^//','',xpath)].xpaths])

    @classmethod
    def any(cls, tag_name):
        """Returns an XPath to find an HTML tag with name=tag_name.

           .. versionadded:: 5.0
        """
        return cls('//%s' % tag_name)

    @classmethod
    def button_labelled(cls, label, **arguments):
        """Returns an XPath to find an ButtonInput whose visible label is the text in `label`.

           When extra keyword arguments are sent to this method, each one is interpreted as the name (kwarg name)
           and value (kwarg value) of an Event argument which this ButtonInput instance should match.
        """
        arguments = arguments or {}

        value_selector = 'normalize-space(@value)=normalize-space(%s)'  % cls.delimit_text(label)
        input_button = cls.any('input')[value_selector]
        if arguments:
            encoded_arguments = '?'+urllib.parse.urlencode(arguments)
            argument_selector = 'substring(@name, string-length(@name)-string-length("%s")+1) = "%s"' % (encoded_arguments, encoded_arguments)
            input_button = input_button[argument_selector]

        button = cls.any('button').with_text(label)
        return button | input_button

    @classmethod
    def caption(cls):
        """Returns an XPath to find an HTML <caption>.

           ..versionadded:: 5.0
        """
        return cls.any('caption')

    @classmethod
    def checkbox(cls):
        """Returns a XPath to a checkbox input.

           .. versionadded:: 5.0
        """
        return cls.any('input')['@type="checkbox"']

    @classmethod
    def div(cls):
        """Returns an XPath to find an HTML <div>.

           .. versionadded:: 5.0
        """
        return cls.any('div')

    @classmethod
    def fieldset_with_legend(cls, legend_text):
        """Returns an XPath to find a FieldSet with the given `legend_text`.

        .. versionadded:: 3.2
        """
        legend = cls.legend().with_text(legend_text)
        return cls.any('fieldset').containing(legend)

    @classmethod
    def heading(cls, level):
        """Returns an XPath to find an HTML <h?> of level `level`.

           .. versionadded:: 5.0
        """
        return cls.any('h%s' % level)

    @classmethod
    def input(cls):
        return cls.any('input')

    @classmethod
    def input_labelled(cls, label_text):
        """Returns an XPath to find an HTML <input> referred to by a <label> that contains the text in `label`."""
        label = cls.any('label').with_text(label_text)
        for_based_xpath = cls.any('input')['@id=%s/@for' % label]
        nested_xpath = cls.any('input').inside_of(label)
        return cls(str(for_based_xpath), str(nested_xpath))

    @classmethod
    def input_named(cls, name):
        """Returns an XPath to find an HTML <input> with the given name."""
        return cls.any('input')['@name="%s"' % name]

    @classmethod
    def input_of_type(cls, input_type):
        """Returns an XPath to find an HTML <input> with type attribute `input_type`."""
        return cls.any('input')['@type="%s"' % input_type]

    @classmethod
    def label(cls):
        """Returns an XPath to find an HTML <label>.

           .. versionadded:: 5.0
        """
        return cls.any('label')

    @classmethod
    def legend(cls):
        """Returns an XPath to find an HTML <legend>.

           .. versionadded:: 5.0
        """
        return cls.any('legend')

    @classmethod
    def link(cls):
        """Returns an XPath to find an HTML <a>.

           .. versionadded:: 5.0
        """
        return cls.any('a')

    @classmethod
    def option(cls):
        """Returns an XPath to find an HTML <option>.

           .. versionadded:: 5.0
        """
        return cls.any('option')

    @classmethod
    def paragraph(cls):
        """Returns an XPath to find an HTML <p>.

           .. versionadded:: 5.0
        """
        return cls.any('p')

    @classmethod
    def select_labelled(cls, label_text):
        """Returns an XPath to find an HTML <select> referred to by a <label> that contains the text in `label`."""
        label = cls.any('label').with_text(label_text)
        return cls.any('select')['@id=%s/@for' % label]

    @classmethod
    def select_named(cls, name):
        """Returns an XPath to find an HTML <select> with the given name."""
        return cls.any('select')['@name="%s"' % name]

    @classmethod
    def span(cls):
        """Returns an XPath to find a Span.

           .. versionadded:: 5.0
        """
        return cls.any('span')

    @classmethod
    def table(cls):
        """Returns a XPath to a table.

           .. versionadded:: 5.0
        """
        return cls.any('table')

    @classmethod
    def table_with_summary(cls, text):
        """Returns an XPath to find an HTML <table summary='...'> matching the text in `text` in its summary attribute value."""
        return cls.any('table')['@summary="%s"' % (text)]

    @classmethod
    def table_header(cls):
        """Returns a XPath to a table header.

           .. versionadded:: 5.0
        """
        return cls.any('thead')

    @classmethod
    def table_body(cls):
        """Returns a XPath to a table body.

           .. versionadded:: 5.0
        """
        return cls.any('tbody')

    @classmethod
    def table_row(cls):
        """Returns a XPath to a table row.

           .. versionadded:: 5.0
        """
        return cls.any('tr')

    @classmethod
    def table_footer(cls):
        """Returns a XPath to a table footer.

           .. versionadded:: 5.0
        """
        return cls.any('tfoot')

    @classmethod
    def table_cell(cls):
        """Returns a XPath to a table cell.

           .. versionadded:: 5.0
        """
        return cls.any('*')['self::td or self::th']

    @classmethod
    def table_cell_aligned_to(cls, column_heading_text, search_column_heading, search_cell_text):
        """Find a cell (td or th) in the column with column_heading_text which is in the same row as 
           where a cell in search_column_heading matches search_cell_text.

            ..versionadded:: 5.0
        """

        target_column_index = 'count(%s/preceding-sibling::th)+1' % cls.table_cell().with_text(column_heading_text).inside_of(cls.table_header())
        search_column_index = 'count(%s/preceding-sibling::th)+1' % cls.table_cell().with_text(search_column_heading).inside_of(cls.table_header())
        found_cell = cls.any('td')[search_column_index].with_text(search_cell_text).xpath
        found_row_index = 'count(%s/parent::tr/preceding-sibling::tr)+1' % found_cell

        return cls.table_cell()[target_column_index].inside_of(XPath.table_row()[found_row_index])

    @classmethod
    def ul(cls):
        """Returns an XPath to find an unordered list.

            ..versionadded:: 5.0
        """
        return cls.any('ul')

    @classmethod
    def li(cls):
        """Returns an XPath to find a list item.

            ..versionadded:: 5.0
        """
        return cls.any('li')


class UnexpectedLoadOf(Exception):
    def __init__(self, jquery_selector):
        super().__init__()
        self.jquery_selector = jquery_selector

    def __str__(self):
        return self.jquery_selector


class DriverBrowser(BasicBrowser):
    """A Browser implemented by a supplied Selenium WebDriver instance, but with interface matching (or similar to)
       :class:`Browser`.

       :param web_driver: The WebDriver instance to be wrapped by this DriverBrowser.
       :keyword host: The hostname of the machine used by default for URLs.
       :keyword port: The port used by default for URLs.
       :keyword scheme: The URL scheme used by default for URLs.
    """
    Keys = Keys
    def __init__(self, web_driver, host='localhost', port=8000, scheme='http'):
        self.web_driver = web_driver
        self.default_host = host
        self.default_scheme = scheme
        self.default_port = port
        self.set_window_size('xl')

    def set_window_size(self, size):
        sizes = {'xs': (576-20, 600),
                 'sm': (768-20, 600),
                 'md': (922-20, 600),
                 'lg': (1200-20, 900),
                 'xl': (1200+300, 900)}
        assert size in sizes.keys(), 'size should be one of: %s' % (', '.join(sizes.keys()))
        self.web_driver.set_window_size(*sizes[size]) # Setting it once requires some sort of delay before it actually happens, twice does that trick.
        self.web_driver.set_window_size(*sizes[size])

    @property
    def raw_html(self):
        """Returns the HTML for the current location unchanged."""
        return self.web_driver.page_source

    def find_element(self, locator, wait=True):
        """Returns the (WebDriver) element found by `locator`. If not found, the method will keep waiting until 2 seconds
           have passed before it will report not finding an element. This timeout mechanism makes it possible to call find_element
           for elements that will be created via JavaScript, and may need some time before they appear.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :keyword wait: If wait=False don't wait for the element to appear (default is True).
        """
        xpath = str(locator)
        if wait:
            return WebDriverWait(self.web_driver, 2).until(lambda d: d.find_element(By.XPATH, xpath), 'waited for %s' % xpath)
        else:
            return self.web_driver.find_element(By.XPATH, xpath)

    def is_element_enabled(self, locator):
        """Answers whether the element found by `locator` is responsive to user activity or not.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        el = self.find_element(locator, wait=False)
        if el and el.is_enabled():
            return el
        return False

    def wait_for_element_enabled(self, locator):
        """Waits until the the element found by `locator` is present and becomes responsive to user activity.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.wait_for(self.is_element_enabled, locator)

    def is_interactable(self, locator):
        """Answers whether the element found by `locator` is actually being displayed by the browser as well as
           responsive to user activity.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        el = self.find_element(locator, wait=False)
        if el and el.is_displayed() and el.is_enabled():
            return el
        return False

    def wait_for_element_interactable(self, locator):
        """Waits until the element found by `locator` is being displayed by the browser as well as
           responsive to user activity.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        self.wait_for(self.is_interactable, locator)

    def is_visible(self, locator):
        """Answers whether the element found by `locator` is being displayed by the browser.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = str(locator)
        try:
            el = self.find_element(locator, wait=False)
        except:
            return False
        if el.is_displayed():
            return el
        return False

    def is_element_value(self, locator, value):
        """Answers whether the element found by `locator` has a value equal to the contents of `value`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param value: The (text) value to match.
        """
        return self.does_element_have_attribute(locator, 'value', value=value)

    def does_element_have_attribute(self, locator, attribute, value=None):
        """Answers whether the element found by `locator` has the given attribute, with the given value

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param attribute: The name of the attribute to check for.
           :keyword value: The value the attribute should have (if any)

           .. versionadded:: 3.2
        """
        el = self.find_element(locator, wait=False)
        if el and el.get_attribute(attribute) is not None:   # el is present and has attribute
            if (value is None) or (el.get_attribute(attribute) == value):  # attribute has specified value if specified
               return el
        return False

    def wait_for(self, condition, *args, **kwargs):
        """Waits until `condition` is satisfied. If `condition` is not satisfied after a timeout period of 2 seconds,
           an exception is raised.

           :param condition: A function, method or other callable which will be called periodically to check\
                             whether a certain condition holds. It should return True if the condition holds,\
                             False otherwise.

           Extra positional and keyword arguments to this method are passed on as-is in the calls
           to `condition`.
        """
        def wrapped(driver):
            try:
                return condition(*args, **kwargs)
            except Exception as ex:
                if isinstance(ex.args[0], CannotSendRequest):
                    return False
                raise
        return WebDriverWait(self.web_driver, 2).until(wrapped)

    def wait_for_not(self, condition, *args, **kwargs):
        """Waits until the given `condition` is **not** satisfied. See :meth:`DriverBrowser.wait_for`."""
        def wrapped(driver):
            try:
                return not condition(*args, **kwargs)
            except Exception as ex:
                if isinstance(ex.args[0], CannotSendRequest):
                    return False
                raise
        return WebDriverWait(self.web_driver, 2).until(wrapped)

    def is_ajax_finished(self):
        return self.web_driver.execute_script('return (("undefined" !== typeof jQuery) && (jQuery.active == 0)) || ("undefined" == typeof jQuery);')

    def wait_for_element_visible(self, locator):
        """Waits for the element found by `locator` to become visible.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.wait_for(self.is_visible, locator)

    def wait_for_element_not_visible(self, locator):
        """Waits until the element found by `locator` is not visible.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.wait_for_not(self.is_visible, locator)

    def is_page_loaded(self):
        """Answers whether the current page has finished loading."""
        readyState = self.web_driver.execute_script('return document.readyState;')
        return readyState == 'complete'

    def wait_for_page_to_load(self):
        """Waits for the current page to load."""
        self.wait_for(self.is_page_loaded)
        try:
#              styleEl.textContent = '*{ transition: none !important; transition-property: none !important; transform: none !important; animation: none !important;  }';
            # Turn all jquery and bootstrap animations off for testing
#            self.web_driver.execute_script('if ( "undefined" !== typeof jQuery) { jQuery.fx.off = true; jQuery.support.transition = false; }; return true;')
            self.web_driver.execute_script('''
              if ( "undefined" !== typeof jQuery) { jQuery.fx.off = true; jQuery.support.transition = false; };
              var styleEl = document.createElement('style');
              styleEl.textContent = '*{ ' +
                 'transition-delay: 0s  !important; ' +
                 '-o-transition-delay: 0s !important; ' +
                 '-moz-transition-delay: 0s !important; ' +
                 '-ms-transition-delay: 0s !important; ' +
                 '-webkit-transition-delay: 0s !important; ' +

                 'transition-duration: 0s !important; ' +
                 '-o-transition-duration: 0s !important; ' +
                 '-moz-transition-duration: 0s !important; ' +
                 '-ms-transition-duration: 0s !important; ' +
                 '-webkit-transition-duration: 0s !important; ' +

                 'animation-delay: 0s !important; ' +
                 '-o-animation-delay: 0s !important; ' +
                 '-moz-animation-delay: 0s !important; ' +
                 '-ms-animation-delay: 0s !important; ' +
                 '-webkit-animation-delay: 0s !important; ' +

                 'animation-duration: 0s !important; ' +
                 '-o-animation-duration: 0s !important; ' +
                 '-moz-animation-duration: 0s !important; ' +
                 '-ms-animation-duration: 0s !important; ' +
                 '-webkit-animation-duration: 0s !important; ' +

                 '}';
              document.head.appendChild(styleEl);
              return true;
            ''')
        except:
            pass # Will only work on HTML pages

    def wait_for_element_present(self, locator):
        """Waits until the element found by `locator` is present on the page (whether visible or not).

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.wait_for(self.is_element_present, locator)

    def wait_for_element_not_present(self, locator):
        """Waits until the element found by `locator` is not present on the page (whether visible or not).

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.wait_for_not(self.is_element_present, locator)

    def open(self, url_string):
        """GETs the URL in `url_string`.

           :param url_string: A string containing the URL to be opened.
        """
        parsed_url = urllib.parse.urlparse(url_string, allow_fragments=True)
        if not (parsed_url.scheme and parsed_url.path and parsed_url.path.startswith('/')):
            parsed_url = parsed_url._replace(scheme=self.default_scheme)
            parsed_url = parsed_url._replace(netloc='{}:{}'.format(self.default_host, self.default_port))

        new_url_string = urllib.parse.urlunparse(parsed_url)
        self.web_driver.get(new_url_string)
        self.wait_for_page_to_load()


    def click(self, locator, wait=True, wait_for_ajax=True):
        """Clicks on the element found by `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :keyword wait: If False, don't wait_for_page_to_load after having clicked the input.
           :keyword wait_for_ajax: If False, don't wait for ajax to finish before continuing (default is to wait).

           .. versionchanged:: 5.0
              Added keyword wait_for_ajax
        """
        self.wait_for_element_interactable(locator)
        self.find_element(locator).click()
        if wait:
            self.wait_for_page_to_load()
        if wait_for_ajax:
            self.wait_for(self.is_ajax_finished)

    def type(self, locator, text, trigger_blur=True, wait_for_ajax=True):
        """Types the text in `value` into the input found by the `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param text: The text to be typed.
           :keyword trigger_blur: If False, don't trigger the blur event on the input after typing (by default blur is triggered).
           :keyword wait_for_ajax: If False, don't wait for ajax to finish before continuing (default is to wait).

           .. versionchanged:: 5.0
              Removed wait kwarg, since we don't ever need to wait_for_page_to_load after typing into an input

           .. versionchanged:: 5.0
              Added trigger_blur to trigger possible onchange events automatically after typing.

           .. versionchanged:: 5.0
              Added keyword wait_for_ajax
        """
        self.wait_for_element_interactable(locator)
        el = self.find_element(locator)
        if el.get_attribute('type') != 'file':
            el.send_keys(Keys.CONTROL+'a') # To clear() the element without triggering extra onchange events
            if not text:
                el.send_keys(Keys.BACKSPACE)
        el.send_keys(text)
        if trigger_blur:
            self.web_driver.execute_script('if ( "undefined" !== typeof jQuery) { jQuery(arguments[0]).blur().focus(); };', el)
        if wait_for_ajax:
            self.wait_for(self.is_ajax_finished)

    def type_focussed(self, keys):
        """Type the keys wherever the focus is.

           :param keys: Keys to send

           ..versionadded:: 5.0
        """

        actions = ActionChains(self.web_driver)
        actions.send_keys(keys)
        actions.perform()

    def select(self, locator, label_to_choose, wait_for_ajax=True):
        """Finds the select element indicated by `locator` and selects one of its options.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param label_to_choose: The label of the option that should be selected.
           :keyword wait_for_ajax: If False, don't wait for ajax to finish before continuing (default is to wait).

            .. versionchanged:: 5.0
               Added keyword wait_for_ajax
        """
        self.select_many(locator, [label_to_choose], wait_for_ajax=wait_for_ajax)

    def select_many(self, locator, labels_to_choose, wait_for_ajax=True):
        """Finds the select element indicated by `locator` and selects some of its options.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param labels_to_choose: A list of the labels of the options that should be selected.
           :keyword wait_for_ajax: If False, don't wait for ajax to finish before continuing (default is to wait).

           .. versionchanged:: 5.0
              Added keyword wait_for_ajax
        """
        self.wait_for_element_interactable(locator)
        el = self.find_element(locator)
        select = Select(el)
        for label_to_choose in labels_to_choose:
            select.select_by_visible_text(label_to_choose)
        if wait_for_ajax:
            self.wait_for(self.is_ajax_finished)

    def select_none(self, locator, wait_for_ajax=True):
        """Finds the select element indicated by `locator` and deselects all options.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :keyword wait_for_ajax: If False, don't wait for ajax to finish before continuing (default is to wait).

           .. versionchanged:: 5.0
              Added keyword wait_for_ajax
        """
        self.wait_for_element_interactable(locator)
        el = self.find_element(locator)
        select = Select(el)
        select.deselect_all()
        if wait_for_ajax:
            self.wait_for(self.is_ajax_finished)

    def mouse_over(self, locator):
        """Moves the mouse pointer over the element found by the `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = str(locator)
        self.wait_for_element_present(locator)
        el = self.find_element(xpath)
        actions = ActionChains(self.web_driver)
        actions.move_to_element(el)
        actions.perform()

    def is_on_top(self, locator):
        """Answers whether the located element is topmost at its location in terms of z-index.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.

           ..versionadded:: 5.0

        """
        el = self.find_element(locator, wait=False)
        return self.web_driver.execute_script('''
            var element = arguments[0];
            var boundingRectangle = element.getBoundingClientRect();
            var center_x = boundingRectangle.left + (boundingRectangle.width / 2);
            var center_y = boundingRectangle.top + (boundingRectangle.height / 2);
            return document.elementFromPoint(center_x, center_y) === element;
        ''', el)

    def focus_on(self, locator):
        """Puts the tab-focus at the element found by the `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.

           ..versionadded:: 3.2

        """
        xpath = str(locator)
        self.wait_for_element_present(locator)
        el = self.find_element(xpath)
        return self.web_driver.execute_script('arguments[0].focus();', el)

    def is_focus_on(self, locator):
        """Answers whether the tab-focus is on the element found by the `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.

           ..versionadded:: 5.0

        """
        el = self.find_element(locator, wait=False)
        active_element = self.web_driver.switch_to.active_element
        #self.web_driver.switch_to.default_content #restore the focus
        return el == active_element

    @property
    def current_url(self):
        """Returns the :class:`reahl.web.fw.Url` of the current location."""
        return urllib.parse.urlparse(self.web_driver.current_url, allow_fragments=True)


    def go_back(self):
        """GETs the previous location (like the back button on a browser).
        """
        self.web_driver.back()
        self.wait_for_page_to_load()

    def refresh(self):
        """GETs the current location again (like the refresh button on a browser).
        """
        self.web_driver.refresh()

    def get_fragment(self):
        """Returns the fragment part (the bit after the #) on the current URL.

        .. versionadded:: 5.0
        """
        return self.execute_script('return window.location.hash')

    def set_fragment(self, fragment):
        """Changes only the fragment part (the bit after the #) on the current URL.

        .. versionadded:: 5.0
        """
        self.execute_script('return (window.location.hash="%s")' % fragment)

    def get_attribute(self, locator, attribute_name):
        """Returns the value of the HTML attribute of the element found by `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param attribute_name: The name of the attribute to return.
        """
        el = self.find_element(locator, wait=False)
        return el.get_attribute(attribute_name)

    def get_value(self, locator):
        """Returns the value of the input indicated by `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        element = self.find_element(locator, wait=False)
        try:
            input_type = element.get_attribute('type')
        except:
            input_type = None
        assert input_type not in ['checkbox', 'radio'], 'You should rather use is_selected method for checkboxes and radio buttons'

        return self.get_attribute(locator, 'value')

    def execute_script(self, script, *arguments):
        """Executes JavaScript in the browser.

           :param script: A string containing the body of a JavaScript function to be executed.
           :param arguments: Variable positional args passed into the function as an array named `arguments`.
        """
        return self.web_driver.execute_script(script, *arguments)

    def switch_styling(self, javascript=True):
        """Switches styling for javascript enabled or javascript disabled.

           .. versionadded:: 3.2
        """
        if javascript:
            script = '''switchJSStyle(document, "js", "no-js"); switchJSStyle(document, "no-js", "js")'''
        else:
            script = '''switchJSStyle(document, "no-js", "js"); switchJSStyle(document, "js", "no-js")'''
        self.execute_script(script)

    def get_text(self, locator):
        """Returns the contents of the element found by `locator`, as plain text.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.find_element(locator, wait=False).text

    def is_image_shown(self, locator):
        """Answers whether the located image is available from the server (ie, whether the src attribute 
           of an img element is accessible).

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        if not self.is_element_present(locator):
            return False
        src = self.get_attribute(locator,'src')
        location = self.current_url
        location.path = urllib.parse.urljoin(location.path, src)
        self.open(str(location))
        self.go_back()
        return True

    def is_editable(self, locator):
        """Answers whether the element found by `locator` can be edited by a user.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.find_element(locator, wait=False).is_enabled()

    def is_active(self, locator):
        """Answers whether the <a> element found by `locator` is currently clickable.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.get_attribute(locator, 'href') is not None

    def is_selected(self, locator):
        """Answers whether the CheckBoxInput or RadionButton element found by `locator` is currently checked.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.

           .. versionchanged:: 5.0
              Renamed from is_checked() to is_selected()
        """
        return self.get_attribute(locator, 'checked') is not None

    def set_selected(self, locator, wait_for_ajax=True):
        """Ensures the CheckBoxInput or RadioButton element found by `locator` is currently checked.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :keyword wait_for_ajax: If False, don't wait for ajax to finish before continuing (default is to wait).

           .. versionchanged:: 5.0
              Changed to break is locator is already checked.

           .. versionchanged:: 5.0
              Added keyword wait_for_ajax.

           .. versionchanged:: 5.0
              Renamed from check() to set_selected()
        """
        self.wait_for_element_enabled(locator) # Cant wait for interactable, since it may be display=none
        assert not self.is_selected(locator)
        self.click(self.checkbox_clickable_element(locator), wait_for_ajax=wait_for_ajax)

    def set_deselected(self, locator, wait_for_ajax=True):
        """Ensures the CheckBoxInput or RadioButton element found by `locator` is currently **not** checked.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :keyword wait_for_ajax: If False, don't wait for ajax to finish before continuing (default is to wait).

           .. versionchanged:: 5.0
              Changed to break is locator is already unchecked.

           .. versionchanged:: 5.0
              Added keyword wait_for_ajax

           .. versionchanged:: 5.0
              Renamed from check() to set_deselected()
        """
        self.wait_for_element_enabled(locator) # Cant wait for interactable, since it may be display=none
        assert self.is_selected(locator)
        self.click(self.checkbox_clickable_element(locator), wait_for_ajax=wait_for_ajax)

    def checkbox_clickable_element(self, locator):
        if not self.is_visible(locator):
            #it may be that the input type=checkbox may not be visible and represented by another visual element
            #as my be in the case of for example with bootstrap .custom-checkbox.
            #We simply click on the label, which checks the checkbox too.

            locators = [XPath.label()['@for=%s/@id' % xpath] for xpath in locator.xpaths]
            locators += [XPath('%s/parent::label' % xpath) for xpath in locator.xpaths]
            return XPath(*[locator.xpath for locator in locators])
        return locator

    def create_cookie(self, cookie_dict):
        """Creates a cookie from the given `cookie_dict`.

           :param cookie_dict: A dictionary with two required keys: 'name' and 'value'. The values of these\
                               keys are the name of the cookie and its value, respectively.\
                               The keys  'path', 'domain', 'secure', 'expiry' can also be set to values.\
                               These have the respective meanings as defined in `RFC6265 <http://tools.ietf.org/html/rfc6265#section-5.2>`_.
        """
        self.web_driver.delete_cookie(cookie_dict['name'])
        self.web_driver.add_cookie(cookie_dict)

    def delete_all_cookies(self):
        """Removes all cookies fomr the browser."""
        self.web_driver.delete_all_cookies()

    def get_html_for(self, locator):
        """Returns the HTML of the element (including its own tags) targeted by the given `locator`

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        el = self.find_element(locator, wait=False)
        return self.web_driver.execute_script('return arguments[0].outerHTML', el)

    def get_inner_html_for(self, locator):
        """Returns the HTML of the children of the element targeted by the given `locator` (excluding the 
           element's own tags).

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        el = self.find_element(locator, wait=False)
        return self.web_driver.execute_script('return arguments[0].innerHTML', el)

    def get_xpath_count(self, locator):
        """Answers the number of elements matching `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return len(self.web_driver.find_elements(By.XPATH, str(locator)))

    def capture_cropped_screenshot(self, output_file):
        """Takes a screenshot of the current page, and writes it to `output_file`. The image is cropped
           to contain only the parts containing something other than the background color.

           :param output_file: The name of the file to which to write the screenshot.
        """
        self.web_driver.get_screenshot_as_file(output_file)
        try:
            from PIL import Image, ImageChops
            im = Image.open(output_file).convert('RGB') #need this mode 1 without alpha, else difference does not work https://stackoverflow.com/questions/61812374/imagechops-difference-not-working-with-simple-png-images
            right_bottom_corner = (im.size[0]-1, im.size[1]-1) #sample of background
            bg = Image.new(im.mode, im.size, im.getpixel(right_bottom_corner))
            diff = ImageChops.difference(im, bg)
            bbox = diff.getbbox()

            cropped = im.crop(bbox)
            cropped.save(output_file)
        except ImportError:
            logging.warning('PILlow is not available, unable to crop screenshots')

    def press_keys(self, keys, locator=None):
        el = self.find_element(locator) if locator else self.web_driver.switch_to.active_element
        el.send_keys(keys)

    def press_tab(self, shift=False):
        """Simulates the user pressing the tab key on element that is currently focussed.

        .. versionchanged:: 4.0
           Changed to operate on the currently focused element.

        .. versionchanged:: 5.0
           Added shift to be able to tab backwards
        """
        self.press_keys((Keys.SHIFT+Keys.TAB) if shift else Keys.TAB)

    def press_arrow(self, direction):
        """Simulates the user pressing arrow key on the element that has focus.

           :param direction: Either 'up', 'down', 'left', 'right'

           .. versionadded:: 5.0

        """
        direction_key = {'up': Keys.ARROW_UP, 'down': Keys.ARROW_DOWN, 'left': Keys.ARROW_LEFT, 'right': Keys.ARROW_RIGHT}
        self.press_keys(direction_key[direction])

    @property
    def title(self):
        """Returns the title of the current location."""
        return self.web_driver.title

    @contextlib.contextmanager
    def no_page_load_expected(self):
        """Returns a context manager that would raise an exception should the current page be reloaded
           while code executes within the context managed by this context manager. Useful for testing
           JavaScript code that should change a page without refreshing it.
        """
        with self.no_load_expected_for('html'):
            yield

    @contextlib.contextmanager
    def no_load_expected_for(self, jquery_selector):
        """Returns a context manager that would raise an exception should the element indicated
           by the given jquery selector be reloaded/replaced during execution of its context.
           Useful for testing JavaScript code that should change an element without replacing it.
        """
        with self.load_expected_for(jquery_selector, False):
            yield

    @contextlib.contextmanager
    def load_expected_for(self, jquery_selector, refresh_expected):
        """Returns a context manager that would raise an exception should the element indicated
           by the given jquery selector be reloaded/replaced or not during execution of its context.
           Useful for testing JavaScript code that should change an element without replacing it.
           If refresh_expected is True, the exception is raised when the element is NOT refreshed.
        """
        escaped_jquery_selector = json.dumps(jquery_selector)[1:-1]
        self.web_driver.execute_script('$("%s").addClass("load_flag")' % escaped_jquery_selector)
        try:
            yield
        finally:
            self.wait_for_page_to_load()
            new_element_loaded = not self.web_driver.execute_script('return $("%s").hasClass("load_flag")' % escaped_jquery_selector)
            if bool(new_element_loaded) is not refresh_expected:
                raise UnexpectedLoadOf(jquery_selector)
            if not new_element_loaded:
                self.web_driver.execute_script('$("%s").removeClass("load_flag")' % escaped_jquery_selector)

    @contextlib.contextmanager
    def refresh_expected_for(self, jquery_selector, refresh_expected):
        """Returns a context manager that would raise an exception should the element indicated
           by the given jquery selector be reloaded/replaced or not during execution of its context.
           Useful for testing JavaScript code that should change an element without replacing it.
           If refresh_expected is True, the exception is raised when the element is NOT refreshed.
        """
        def escaped(javascript):
            return json.dumps(javascript)[1:-1]
        escaped_jquery_selector = escaped(jquery_selector)
        escaped_load_flag_selector = escaped('p[class*="load_flag"]')
        self.web_driver.execute_script('$("%s").append("%s")' % (escaped_jquery_selector, escaped('<p class="load_flag">temporarily added to check refreshing</p>')))
        try:
            yield
        finally:
            self.wait_for_page_to_load()
            new_element_loaded = not self.web_driver.execute_script('''return $('%s').find('%s').length > 0''' % (escaped_jquery_selector, escaped_load_flag_selector)) 
            if bool(new_element_loaded) is not refresh_expected:
                raise UnexpectedLoadOf(jquery_selector)
            if not new_element_loaded:
                self.web_driver.execute_script('''$('%s').find('%s').remove()''' % (escaped_jquery_selector, escaped_load_flag_selector))

    def is_alert_present(self):
        return expected_conditions.alert_is_present()(self.web_driver)

    @contextlib.contextmanager
    def alert_expected(self):
        yield self.wait_for(self.is_alert_present)

    @property
    def current_browser_tab(self):
        return self.web_driver.current_window_handle

    def switch_to_different_tab(self):
        original_tab = self.current_browser_tab
        other_tabs = [h for h in self.web_driver.window_handles if h != original_tab]
        self.web_driver.switch_to.window(other_tabs[0])

    @contextlib.contextmanager
    def new_tab_closed(self):
        """Returns a context manager that ensures, if a new tab is opened in its context, selenium ends up  
           on the original tab while the newly created tab is closed on exit.
        """
        current_tab = self.current_browser_tab
        tabs_before = [w for w in self.web_driver.window_handles if w != current_tab]

        try:
            yield
        finally:
            tabs_after = [w for w in self.web_driver.window_handles if w != current_tab]
            new_tabs = [w for w in tabs_after if w not in tabs_before]
            try:
                assert len(new_tabs) == 1
                new_tab = new_tabs[0]
                self.web_driver.switch_to.window(new_tab)
                self.web_driver.close()
            finally:
                self.web_driver.switch_to.window(current_tab)

