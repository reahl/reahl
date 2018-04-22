# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import io
import re
import contextlib
from six.moves.urllib import parse as urllib_parse
import logging
from six.moves.http_cookiejar import Cookie
from six.moves.http_client import CannotSendRequest

from webtest import TestApp
from lxml import html
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from reahl.component.py3compat import ascii_as_bytes_or_str
from reahl.web.fw import Url


# See: https://bitbucket.org/ianb/webtest/issue/45/html5-form-associated-inputs-break-webtest
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


class BasicBrowser(object):

    def view_source(self):
        for line in html.tostring(self.lxml_html, pretty_print=True, encoding='unicode').split('\n'): 
            print(line)
            
    def save_source(self, filename):
        with io.open(filename, 'w') as html_file:
            html_file.write(self.raw_html)

    def is_element_present(self, locator):
        xpath = six.text_type(locator)
        return len(self.lxml_html.xpath(xpath)) == 1 

    @property
    def lxml_html(self):
        if self.raw_html:
            return html.fromstring(self.raw_html)
        return None

    def xpath(self, xpath):
        """Returns the `lmxl Element <http://lxml.de/>`_ found by the given `xpath`."""
        return self.lxml_html.xpath(six.text_type(xpath))

    def get_xpath_count(self, locator):
        """Answers the number of elements matching `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return len(self.xpath(six.text_type(locator)))

    def get_html_for(self, locator):
        """Returns the HTML of the element (including its own tags) targeted by the given `locator`
        
           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        element = self.xpath(xpath)[0]
        return html.tostring(element, encoding='unicode')

    def get_inner_html_for(self, locator):
        """Returns the HTML of the children of the element targeted by the given `locator` (excluding the 
           element's own tags).
        
           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        element = self.xpath(xpath)[0]
        return ''.join(html.tostring(child, encoding='unicode') for child in element.getchildren())

    def get_id_of(self, locator):
        xpath = six.text_type(locator)
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
                                      the method hebaves like a browser would, by opening redirect responses.
           :keyword relative: Set to True to indicate that `url_string` contains a path relative to the current location.
       
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
        self.last_response = self.testapp.post((ascii_as_bytes_or_str(url_string)), form_values, **kwargs)

    def relative(self, url_string):
        url_bits = urllib_parse.urlparse(url_string)
        return urllib_parse.urlunparse(('', '', url_bits.path, url_bits.params, url_bits.query, url_bits.fragment))
            
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
    def location_path(self):
        """Returns the current location url path."""
        return self.last_response.request.path

    @property
    def location_scheme(self):
        """Returns the the last request scheme(HTTP/HTTPS)."""
        return self.last_response.request.scheme

    @property
    def location_query_string(self):
        """Returns the current query string."""
        return self.last_response.request.query_string

    def get_form_for(self, locator):
        """Return the form for the given `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        form_id = self.xpath('%s[@form]' % xpath)[0].attrib['form']
        form_element = self.xpath('//form[@id=\'%s\']' % form_id)[0]
        patch_Field()
        return self.last_response.forms[form_element.attrib['id']]

    def type(self, locator, text):
        """Types the text in `text` into the input found by the `locator`.
        
           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param text: The text to be typed.
        """
        xpath = six.text_type(locator)
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
        xpath = six.text_type(locator)
        buttons = self.xpath(xpath)
        assert len(buttons) == 1, 'Could not find one (and only one) button for %s' % locator
        button = buttons[0]
        if button.tag == 'input' and button.attrib['type'] == 'submit':
            button_name = self.xpath(xpath)[0].name
            form = self.get_form_for(xpath)
            form.action = ascii_as_bytes_or_str(self.relative(form.action))
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
        xpath = six.text_type(locator)
        select = self.xpath(xpath)
        assert len(select) == 1, 'Could not find one (and only one) element for %s' % locator
        select = select[0]
        assert select.tag == 'select', 'Expected %s to find a select tag' % locator

        form = self.get_form_for(xpath)
        
        for option in select.findall('option'):
            if option.text == label_to_choose:
                form[select.attrib['name']] = list(option.values())[0]
                return
        raise AssertionError('Option %s not found' % label_to_choose)

    def select_many(self, locator, labels_to_choose):
        """Finds the select element indicated by `locator` and selects the options labelled as such.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param labels_to_choose: The labels of the options that should be selected.
        """
        xpath = six.text_type(locator)
        select = self.xpath(xpath)
        assert len(select) == 1, 'Could not find one (and only one) element for %s' % locator
        select = select[0]
        assert select.tag == 'select', 'Expected %s to find a select tag' % locator

        form = self.get_form_for(xpath)

        options_to_select = []
        for option in select.findall('option'):
            if option.text in labels_to_choose:
                options_to_select.append(option)
        form[select.attrib['name']] = [option.values()[0] for option in options_to_select]

        if len(options_to_select) != len(options_to_select):
            raise AssertionError('Could only select options labelled[] not all of []' % (','.join([option.text for option in options_to_select]), ','.join(labels_to_choose) ))

    def select_none(self, locator):
        """Finds the select element indicated by `locator` and ensure nothing is selected.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
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
        xpath = six.text_type(locator)
        inputs = self.xpath(xpath)
        assert len(inputs) == 1
        form = self.get_form_for(xpath)
        return form.fields[inputs[0].name][0].value
         
    def get_full_path(self, relative_path):
        return urllib_parse.urljoin(self.location_path, relative_path)

    def is_image_shown(self, locator):
        """Answers whether the located image is available from the server (ie, whether the src attribute 
           of an img element is accessible).

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
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
        name = ascii_as_bytes_or_str(cookie_dict['name'])
        value = ascii_as_bytes_or_str(cookie_dict['value'])
        path = ascii_as_bytes_or_str(cookie_dict.get('path', ''))
        path_set = path != ''
        domain = ascii_as_bytes_or_str(cookie_dict.get('domain', ''))
        domain_set = domain != ''
        secure = cookie_dict.get('secure', False)
        expires = cookie_dict.get('expiry', None)
        cookie = Cookie(0, name, value, None, False, domain, domain_set, None, path, path_set,
                        secure, expires, None, None, None, None)
        self.testapp.cookiejar.set_cookie(cookie)

    def is_element_enabled(self, locator):
        """Answers whether the located element is reactive to user commands or not. For <a> elements,
           this means that they have an href attribute, for inputs it means that they are not disabled.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        [element] = self.xpath(xpath)
        if element.tag == 'a':
            return 'href' in element.attrib
        if element.tag == 'input':
            return 'disabled' not in element.attrib
        assert None, 'Not yet implemented'



class XPath(object):
    """An object representing an XPath expression for locating a particular element on a web page.
       A programmer is not supposed to instantiate an XPath directly. Use one of the descriptive
       class methods to instantiate an XPath instance.

       An XPath expression in a string is returned when an XPath object is cast to six.text_type.
    """
    def __init__(self, xpath):
        self.xpath = xpath
        
    def __str__(self):
        return self.xpath

    @classmethod
    def label_with_text(cls, text):
        """Returns an XPath to find an HTML <label> containing the text in `text`."""
        return cls('//label[normalize-space()=normalize-space("%s")]' % text)

    @classmethod
    def heading_with_text(cls, level, text):
        """Returns an XPath to find an HTML <h> of level `level` containing the text in `text`."""
        return cls('//h%s[node()="%s"]' % (level, text))

    @classmethod
    def caption_with_text(cls, text):
        """Returns an XPath to find an HTML <caption> matching the text in `text`."""
        return cls('//caption[node()="%s"]' % (text))

    @classmethod
    def option_with_text(cls, text):
        """Returns an XPath to find an HTML <option> containing the text in `text`."""
        return cls('//option[node()="%s"]' % (text))

    @classmethod
    def table_with_summary(cls, text):
        """Returns an XPath to find an HTML <table summary='...'> matching the text in `text` in its summary attribute value."""
        return cls('//table[@summary="%s"]' % (text))

    @classmethod
    def table_cell_with_text(cls, text):
        """Returns an XPath to find an HTML <tr> that contains a <td> / cell with text matching the text in `text`"""
        return cls('//tr/td[normalize-space(node())="%s"]' % (text))

    @classmethod
    def checkbox_in_table_row(cls, nth):
        """Returns an XPath to find an HTML <tr> that contains a <td> / cell with text matching the text in `text`"""
        return cls('(//tr/td/input[@type="checkbox"])[%s]' % nth)

    @classmethod
    def link_with_text(cls, text, nth=1):
        """Returns an XPath to find an HTML <a> containing the text in `text`."""
        return cls('(//a[normalize-space(.)=normalize-space("%s")])[%s]' % (text, nth))

    @classmethod
    def link_starting_with_text(cls, text):
        """Returns an XPath to find an HTML <a> containing text that starts with the contents of `text`."""
        return cls('//a[starts-with(node(), "%s")]' % text)

    @classmethod
    def paragraph_containing(cls, text):
        """Returns an XPath to find an HTML <p> that contains the text in `text`."""
        return cls('//p[contains(node(), "%s")]' % text)

    @classmethod
    def input_named(cls, name):
        """Returns an XPath to find an HTML <input> with the given name."""
        return '//input[@name="%s"]' % name

    @classmethod
    def input_labelled(cls, label):
        """Returns an XPath to find an HTML <input> referred to by a <label> that contains the text in `label`."""
        for_based_xpath = '//input[@id=//label[normalize-space(node())=normalize-space("%s")]/@for]' % label
        nested_xpath = '//label[normalize-space()=normalize-space("%s")]//input' % label
        return cls('%s|%s' % (for_based_xpath, nested_xpath))

    @classmethod
    def select_labelled(cls, label):
        """Returns an XPath to find an HTML <select> referred to by a <label> that contains the text in `label`."""
        return cls('//select[@id=//label[normalize-space(node())=normalize-space("%s")]/@for]' % label)

    @classmethod
    def input_of_type(cls, input_type):
        """Returns an XPath to find an HTML <input> with type attribute `input_type`."""
        return '//input[@type="%s"]' % input_type

    @classmethod
    def fieldset_with_legend(cls, legend_text):
        """Returns an XPath to find a FieldSet with the given `legend_text`.

        .. versionadded:: 3.2
        """
        return cls('//fieldset[legend[normalize-space(node())=normalize-space("%s")]]' % legend_text)

    @classmethod
    def button_labelled(cls, label, **arguments):
        """Returns an XPath to find an ButtonInput whose visible label is the text in `label`.

           When extra keyword arguments are sent to this method, each one is interpreted as the name (kwarg name)
           and value (kwarg value) of an Event argument which this ButtonInput instance should match.
        """
        arguments = arguments or {}
        if arguments:
            encoded_arguments = '?'+urllib_parse.urlencode(arguments)
            argument_selector = '[substring(@name, string-length(@name)-string-length("%s")+1) = "%s"]' % (encoded_arguments, encoded_arguments)
        else:
            argument_selector = ''
        value_selector = '[normalize-space(@value)=normalize-space("%s")]'  % label
        inputButtonXPath = '//input%s%s' % (argument_selector, value_selector)
        buttonTagXPath = '//button[normalize-space(node())=normalize-space("%s")]' % label
        return cls('%s | %s' % (inputButtonXPath, buttonTagXPath))

    @classmethod
    def error_label_containing(cls, text):
        """Returns an XPath to find a Label containing the error message in `text`."""
        return cls('//label[@class="error" and contains(node(),"%s")]' % text)

    @classmethod
    def span_containing(cls, text):
        """Returns an XPath to find a Span containing the message in `text`."""
        return cls('//span[contains(node(),"%s")]' % text)

    @classmethod
    def div_containing(cls, text):
        """Returns an XPath to find a Div containing the message in `text`."""
        return cls('//div[contains(text(),"%s")]' % text)


class UnexpectedLoadOf(Exception):
    def __init__(self, jquery_selector):
        super(UnexpectedLoadOf, self).__init__()
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
    def __init__(self, web_driver, host='localhost', port=8000, scheme='http'):
        self.web_driver = web_driver
        self.default_host = host
        self.default_scheme = scheme
        self.default_port = port

    @property
    def raw_html(self):
        """Returns the HTML for the current location unchanged."""
        return self.web_driver.page_source

    def find_element(self, locator):
        """Returns the (WebDriver) element found by `locator`. If not found, the method will keep waiting until 2 seconds
           have passed before it will report not finding an element. This timeout mechanism makes it possible to call find_element
           for elements that will be created via JavaScript, and may need some time before they appear.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        return WebDriverWait(self.web_driver, 2).until(lambda d: d.find_element_by_xpath(xpath), 'waited for %s' % xpath)

    def is_element_enabled(self, locator):
        """Answers whether the element found by `locator` is responsive to user activity or not.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        el = self.web_driver.find_element_by_xpath(xpath)
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
        xpath = six.text_type(locator)
        el = self.web_driver.find_element_by_xpath(xpath)
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
        xpath = six.text_type(locator)
        try:
            el = self.web_driver.find_element_by_xpath(xpath)
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
        xpath = six.text_type(locator)
        el = self.web_driver.find_element_by_xpath(xpath)
        if el and el.get_attribute(attribute) is not None:   # el is present and has attribute
            if (value is not None or el.get_attribute(attribute) == value):  # attribute has specified value if specified
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
        url = Url(url_string)
        if not url.is_network_absolute:
            url.hostname = self.default_host
            url.scheme = self.default_scheme
            url.port = self.default_port
        self.web_driver.get(six.text_type(url))
        self.wait_for_page_to_load()

    def click(self, locator, wait=True):
        """Clicks on the element found by `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :keyword wait: If False, don't wait_for_page_to_load after having clicked the input.
        """
        self.wait_for_element_interactable(locator)
        self.find_element(locator).click()
        if wait:
            self.wait_for_page_to_load()

    def type(self, locator, text, wait=True):
        """Types the text in `value` into the input found by the `locator`.
        
           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param text: The text to be typed.
           :keyword wait: If False, don't wait_for_page_to_load after having typed into the input.
           
        """
        self.wait_for_element_interactable(locator)
        el = self.find_element(locator)
        if el.get_attribute('type') != 'file':
            el.clear()
        el.send_keys(text)
        if wait:
            self.wait_for_page_to_load()

    def mouse_over(self, locator):
        """Moves the mouse pointer over the element found by the `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        el = self.find_element(xpath)
        actions = ActionChains(self.web_driver)
        actions.move_to_element(el)
        actions.perform()

    def focus_on(self, locator):
        """Puts the tab-focus at the element found by the `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.

           ..versionadded:: 3.2

        """
        xpath = six.text_type(locator)
        el = self.find_element(xpath)
        return self.web_driver.execute_script('arguments[0].focus();', el)

    @property
    def current_url(self):
        """Returns the :class:`reahl.web.fw.Url` of the current location."""
        return Url(self.web_driver.current_url)

    def go_back(self):
        """GETs the previous location (like the back button on a browser).
        """
        self.web_driver.back()
        self.wait_for_page_to_load()

    def refresh(self):
        """GETs the current location again (like the refresh button on a browser).
        """
        self.web_driver.refresh()

    def get_attribute(self, locator, attribute_name):
        """Returns the value of the HTML attribute of the element found by `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param attribute_name: The name of the attribute to return.
        """
        return self.find_element(locator).get_attribute(attribute_name)

    def get_value(self, locator): 
        """Returns the value of the input indicated by `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
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
        return self.find_element(locator).text

    def is_image_shown(self, locator):
        """Answers whether the located image is available from the server (ie, whether the src attribute 
           of an img element is accessible).

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        if not self.is_element_present(locator):
            return False
        src = self.get_attribute(locator,'src')
        location = self.current_url
        location.path = urllib_parse.urljoin(location.path, src)
        self.open(six.text_type(location))
        self.go_back()
        return True
        
    def is_editable(self, locator):
        """Answers whether the element found by `locator` can be edited by a user.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.find_element(locator).is_enabled()

    def is_active(self, locator):
        """Answers whether the <a> element found by `locator` is currently clickable.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.get_attribute(locator, 'href') is not None
    
    def is_checked(self, locator):
        """Answers whether the CheckBoxInput element found by `locator` is currently checked.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return self.get_attribute(locator, 'checked') is not None

    def check(self, locator):
        """Ensures the CheckBoxInput element found by `locator` is currently checked.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        if not self.is_checked(locator):
           self.click(self.checkbox_clickable_element(locator))

    def uncheck(self, locator):
        """Ensures the CheckBoxInput element found by `locator` is currently **not** checked.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        if self.is_checked(locator):
            self.click(self.checkbox_clickable_element(locator))

    def checkbox_clickable_element(self, locator):
        if not self.is_visible(locator):
            #it may be that the input type=checkbox may not be visible and represented by another visual element
            #as my be in the case of for example with bootstrap .custom-checkbox.
            #We simply click on the label, which checks the checkbox too.
            label_for_input = XPath('(%s)/following-sibling::label' % locator.xpath)
            return label_for_input
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
        xpath = six.text_type(locator)
        el = self.find_element(xpath)
        return self.web_driver.execute_script('return arguments[0].outerHTML', el)
        
    def get_inner_html_for(self, locator):
        """Returns the HTML of the children of the element targeted by the given `locator` (excluding the 
           element's own tags).
        
           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        el = self.find_element(xpath)
        return self.web_driver.execute_script('return arguments[0].innerHTML', el)

    def get_xpath_count(self, locator):
        """Answers the number of elements matching `locator`.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        return len(self.web_driver.find_elements_by_xpath(six.text_type(locator)))

    def capture_cropped_screenshot(self, output_file, background='White'):
        """Takes a screenshot of the current page, and writes it to `output_file`. The image is cropped
           to contain only the parts containing something other than the background color.

           :param output_file: The name of the file to which to write the screenshot.
           :keyword background: The color to use as background color when cropping.
        """
        self.web_driver.get_screenshot_as_file(output_file)

        try:
            from PIL import Image, ImageChops
            im = Image.open(output_file)
            bg = Image.new(im.mode, im.size, background)
            diff = ImageChops.difference(im, bg)
            bbox = diff.getbbox()

            cropped = im.crop(bbox)
            cropped.save(output_file)
        except ImportError:
            logging.warning('PILlow is not available, unable to crop screenshots')

    def press_tab(self):
        """Simulates the user pressing the tab key on element that is currently focussed.

        .. versionchanged: 4.0
           Changed to operate on the currently focussed element.
        """
        el = self.web_driver.switch_to.active_element
        el.send_keys(Keys.TAB)
        # To ensure the element gets blur event which for some reason does not always happen when pressing TAB:
        self.web_driver.execute_script('if ( "undefined" !== typeof jQuery) {jQuery(arguments[0]).blur();};', el)

    def press_backspace(self, locator):
        """Simulates the user pressing the backspace key while the element at `locator` has focus.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        self.find_element(locator).send_keys(Keys.BACK_SPACE)

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
        self.web_driver.execute_script('$("%s").addClass("load_flag")' % jquery_selector)
        try:
            yield
        finally:
            self.wait_for_page_to_load()
            new_element_loaded = not self.web_driver.execute_script('return $("%s").hasClass("load_flag")' % jquery_selector) 
            if new_element_loaded:
                raise UnexpectedLoadOf(jquery_selector)
        

