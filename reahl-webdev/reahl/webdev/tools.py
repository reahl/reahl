# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import unicode_literals
from __future__ import print_function
import six
import contextlib
from six.moves.urllib import parse as urllib_parse
import logging

from webtest import TestApp
from lxml import html
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from reahl.web.fw import Url


# See: https://bitbucket.org/ianb/webtest/issue/45/html5-form-associated-inputs-break-webtest
from webtest.app import Field, Form
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
    def save_source(self, filename):
        with open(filename, 'w') as output:
            for line in html.tostring(self.lxml_html, pretty_print=True).split('\n'): 
                output.write(line+'\n')

    def view_source(self):
        for line in html.tostring(self.lxml_html, pretty_print=True).split('\n'): 
            print(line)
            
    def save_source(self, filename):
        with open(filename, 'w') as html_file:
            html_file.write(self.raw_html)
            
    def get_html_for(self, locator):
        xpath = six.text_type(locator)
        return html.tostring(self.lxml_html.xpath(xpath)[0])
        
    def is_element_present(self, locator):
        xpath = six.text_type(locator)
        return len(self.lxml_html.xpath(xpath)) == 1 

    @property
    def lxml_html(self):
        if self.raw_html:
            return html.fromstring(self.raw_html)
        return None


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
        self.last_response = self.testapp.post((url_string.encode('utf-8')), form_values, **kwargs)

    def relative(self, url_string):
        url_bits = urllib_parse.urlparse(url_string)
        return urllib_parse.urlunparse(('', '', url_bits.path, url_bits.params, url_bits.query, url_bits.fragment))
            
    def xpath(self, xpath):
        """Returns the `lmxl Element <http://lxml.de/>`_ found by the given `xpath`."""
        return self.lxml_html.xpath(xpath)

    @property
    def raw_html(self):
        """Returns the HTML for the current location unchanged."""
        return self.last_response.unicode_body

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
        form_element = self.xpath('//form[@id=%s/@form]' % xpath)[0]
        patch_Field()
        return self.last_response.forms[form_element.attrib['id']]

    def get_html_for(self, locator):
        """Returns the HTML of the element (including its own tags) targeted by the given `locator`
        
           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        element = self.xpath(xpath)[0]
        return html.tostring(element, encoding='utf-8').decode('utf-8')

    def get_inner_html_for(self, locator):
        """Returns the HTML of the children of the element targeted by the given `locator` (excluding the 
           element's own tags).
        
           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        xpath = six.text_type(locator)
        element = self.xpath(xpath)[0]
        return ''.join(html.tostring(child, encoding='utf-8').decode('utf-8')
                         for child in element.getchildren())

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
            form.action = (self.relative(form.action).encode('utf-8'))
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
        """
        name = cookie_dict['name'].encode('utf-8')
        value = cookie_dict['value'].encode('utf-8')
        self.testapp.cookies[name] = value #'%s;%s' % (value, options)

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
        return cls('//label[text()="%s"]' % text)

    @classmethod
    def heading_with_text(cls, level, text):
        """Returns an XPath to find an HTML <h> of level `level` containing the text in `text`."""
        return cls('//h%s[text()="%s"]' % (level, text))

    @classmethod
    def caption_with_text(cls, text):
        """Returns an XPath to find an HTML <caption> matching the text in `text`."""
        return cls('//caption[text()="%s"]' % (text))

    @classmethod
    def table_with_summary(cls, text):
        """Returns an XPath to find an HTML <table summary='...'> matching the text in `text` in its summary attribute value."""
        return cls('//table[@summary="%s"]' % (text))

    @classmethod
    def table_cell_with_text(cls, text):
        """Returns an XPath to find an HTML <tr> that contains a <td> / cell with text matching the text in `text`"""
        return cls('//tr/td[normalize-space(text())="%s"]' % (text))

    @classmethod
    def checkbox_in_table_row(cls, nth):
        """Returns an XPath to find an HTML <tr> that contains a <td> / cell with text matching the text in `text`"""
        return cls('(//tr/td/input[@type="checkbox"])[%s]' % nth)

    @classmethod
    def link_with_text(cls, text, nth=1):
        """Returns an XPath to find an HTML <a> containing the text in `text`."""
        return cls('(//a[normalize-space(text())=normalize-space("%s")])[%s]' % (text, nth))

    @classmethod
    def link_starting_with_text(cls, text):
        """Returns an XPath to find an HTML <a> containing text that starts with the contents of `text`."""
        return cls('//a[starts-with(text(), "%s")]' % text)

    @classmethod
    def paragraph_containing(cls, text):
        """Returns an XPath to find an HTML <p> that contains the text in `text`."""
        return cls('//p[contains(text(), "%s")]' % text)

    @classmethod
    def input_labelled(cls, label):
        """Returns an XPath to find an HTML <input> referred to by a <label> that contains the text in `label`."""
        return cls('//input[@name=//label[normalize-space(text())=normalize-space("%s")]/@for]' % label)

    @classmethod
    def select_labelled(cls, label):
        """Returns an XPath to find an HTML <select> referred to by a <label> that contains the text in `label`."""
        return cls('//select[@name=//label[normalize-space(text())=normalize-space("%s")]/@for]' % label)

    @classmethod
    def input_of_type(cls, input_type):
        """Returns an XPath to find an HTML <input> with type attribute `input_type`."""
        return '//input[@type="%s"]' % input_type

    @classmethod
    def inputgroup_labelled(cls, label):
        """Returns an XPath to find an InputGroup with label text `label`."""
        return cls('//fieldset[label[normalize-space(text())=normalize-space("%s")]]' % label)

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
        return cls('//input%s%s' % (argument_selector, value_selector))

    @classmethod
    def error_label_containing(cls, text):
        """Returns an XPath to find an ErrorLabel containing the text in `text`."""
        return cls('//label[@class="error" and contains(text(),"%s")]' % text)


class UnexpectedPageLoad(Exception):
    pass


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
        xpath = six.text_type(locator)
        el = self.web_driver.find_element_by_xpath(xpath)
        if el and el.get_attribute('value') == value:
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
            return condition(*args, **kwargs)
        return WebDriverWait(self.web_driver, 2).until(wrapped)

    def wait_for_not(self, condition, *args, **kwargs):
        """Waits until the given `condition` is **not** satisfied. See :meth:`DriverBrowser.wait_for`."""
        def wrapped(driver):
            return not condition(*args, **kwargs)
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
            # Turn all jquery animations off for testing
            self.web_driver.execute_script('if ( "undefined" !== typeof jQuery) { jQuery.fx.off=true; }; return true;')  
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
           :keyword wait: If False, first waits for the element to become interactible (visible and enabled).
        """
        self.wait_for_element_interactable(locator)
        self.find_element(locator).click()
        if wait:
            self.wait_for_page_to_load()

    def type(self, locator, text, wait=True):
        """Types the text in `value` into the input found by the `locator`.
        
           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
           :param text: The text to be typed.
           :keyword wait: If False, first waits for the element to become interactible (visible and enabled).
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

    def execute_script(self, script):
        """Executes JavaScript in the browser.

           :param script: A string containing the JavaScript to be executed.
        """
        return self.web_driver.execute_script(script)
        
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
            self.click(locator)

    def uncheck(self, locator):
        """Ensures the CheckBoxInput element found by `locator` is currently **not** checked.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        if self.is_checked(locator):
            self.click(locator)

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
            logging.warn('PILlow is not available, unable to crop screenshots')

    def press_tab(self, locator):
        """Simulates the user pressing the tab key while the element at `locator` has focus.

           :param locator: An instance of :class:`XPath` or a string containing an XPath expression.
        """
        self.find_element(locator).send_keys(Keys.TAB)

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
        self.web_driver.execute_script('$("html").addClass("page_load_flag")')
        try:
            yield
        finally:
            self.wait_for_page_to_load()
            new_page_loaded = not self.web_driver.execute_script('return $("html").hasClass("page_load_flag")') 
            if new_page_loaded:
                raise UnexpectedPageLoad()
        

