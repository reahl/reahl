.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |XPath| replace::  :class:`~reahl.browsertools.browsertools.XPath`
.. |DriverBrowser| replace:: :class:`~reahl.browsertools.browsertools.DriverBrowser`
.. |Browser| replace:: :class:`~reahl.browsertools.browsertools.Browser`
.. |WebDriver| replace:: `Selenium Webdriver <https://www.selenium.dev/>`__
.. |WebTest| replace:: `WebTest <https://docs.pylonsproject.org/projects/webtest>`__

Browser tools (reahl-browsertools)
----------------------------------

Reahl browser tools provides an interface to Selenium WebDriver that simplifies tests that deal with ajax. It also
includes programmatically composable XPaths that are easy to read in code.

.. seealso::

   :doc:`The API documentation <index>`.

Composing XPaths programmatically
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

|XPath| can be used to compose complicated XPath expressions in a readable, consistent way.


Creating an XPath
"""""""""""""""""

To create an |XPath|, call a class method for a simple element::

  >>> from reahl.browsertools.browsertools import XPath
  >>> XPath.div()
  XPath('//div')

To obtain the raw xpath expression, cast an |XPath| to a string::

  >>> str(XPath.div())
  '//div'


Composing expressions
"""""""""""""""""""""

Call methods on an |XPath| instance to compose a larger expression::

  >>> XPath.div().including_class('myclass')
  XPath('//div[contains(concat(" ", @class, " "), " myclass ")]')

These methods can be chained, since each one returns an |XPath|::

  >>> XPath.div().including_class('myclass').including_text('hello')
  XPath('//div[contains(concat(" ", @class, " "), " myclass ")][contains(normalize-space(), normalize-space("hello"))]')

Since methods like :meth:`~reahl.browsertools.browsertools.XPath.including_text` can be called on any |XPath|, you get
standardised behaviour such as that spaces are always normalised: if you pass text with a single space in it, but
the HTML is laid out with more than one space, the resulting expression will still match.

Less simple starting elements
"""""""""""""""""""""""""""""

Some |XPath| class methods can find elements that are not so easily composable, such as
:meth:`~reahl.browsertools.browsertools.XPath.input_labelled`,
:meth:`~reahl.browsertools.browsertools.XPath.button_labelled`,
:meth:`~reahl.browsertools.browsertools.XPath.fieldset_with_legend` or
:meth:`~reahl.browsertools.browsertools.XPath.table_cell_aligned_to`.


|XPath|\s inside other |XPath|\s
""""""""""""""""""""""""""""""""

An |XPath| can also be located inside of another::

    XPath.button_labelled('Save').inside_of(XPath.div().including_class('myclass'))



Smart browser interfaces
^^^^^^^^^^^^^^^^^^^^^^^^

Websites with embedded JavaScript add more fluff to test code: you often have to first wait for an element to
appear before you can click on it, for example.

|DriverBrowser| contains a number of methods to simulate a human interacting with the browser, such
as :meth:`~reahl.browsertools.browsertools.DriverBrowser.click`::

   browser.click(XPath.button_labelled('Save'))

These methods always automatically wait for the operated-on element to appear, so you don't have to write that in
your tests. Where sensible, they also wait for possible ajax action to complete before returning, as in the case
with :meth:`~reahl.browsertools.browsertools.DriverBrowser.type`::

   browser.type(XPath.input_labelled('Percentage'), '99')

Why wait? Because typing a value and tabbing out to the next field might trigger changes to the page. You want to
wait for the page to change before performing another action.

For consistency when not using webdriver, |Browser| provides a similar interface to WebTest. This makes for faster tests
where an actual browser and JavaScript are not required.