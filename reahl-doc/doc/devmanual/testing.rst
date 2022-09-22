.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Browser| replace::  :class:`~reahl.browsertools.browsertools.Browser`
.. |XPath| replace::  :class:`~reahl.browsertools.browsertools.XPath`
.. |Fixture| replace::  :class:`~reahl.tofu.Fixture`
.. |ExecutionContext| replace::  :class:`~reahl.component.context.ExecutionContext`
.. |Configuration| replace::  :class:`~reahl.component.config.Configuration`
.. |SystemControl| replace::  :class:`~reahl.component.dbutils.SystemControl`
.. |WebFixture| replace::  :class:`~reahl.web_dev.fixtures.WebFixture`
.. |WebServerFixture| replace::  :class:`~reahl.web_dev.fixtures.WebServerFixture`
.. |DriverBrowser| replace::  :class:`~reahl.browsertools.browsertools.DriverBrowser`
.. |ReahlSystemFixture| replace:: :class:`~reahl.dev.fixtures.ReahlSystemFixture`
.. |ReahlSystemSessionFixture| replace:: :class:`~reahl.dev.fixtures.ReahlSystemSessionFixture`
.. |SqlAlchemyFixture| replace:: :class:`~reahl.sqlalchemysupport_dev.fixtures.SqlAlchemyFixture`

       
Testing
=======

Tests are central to our development process. We depend on a testing
infrastructure build using |Fixture|\s and some other testing tools.

.. sidebar:: Behind the scenes

   The Reahl testing tools rely on other projects:
   
   - `Pytest <https://docs.pytest.org/>`_ 
   - `WebTest <http://webtest.pythopaste.org>`_
   - `Selenium <https://pypi.python.org/pypi/selenium>`_ 
   - `geckodriver <https://github.com/mozilla/geckodriver>`_

      
Fixtures
--------

A selection of |Fixture|\s are described in :doc:`the reference docs
<../devtools/tools>`. Here is a short summary of what each is used for:

|ReahlSystemFixture| and |ReahlSystemSessionFixture| 
  These are used to set up a database connection and create its schema
  once, at the start of a test run. They give access to the global
  system |Configuration|, the |ExecutionContext| in which tests using
  them are run, and to a |SystemControl| --- an object used to control
  anything related to the database.
 
|SqlAlchemyFixture|
  If a test uses a |SqlAlchemyFixture|, a database transaction is
  started before the test is run, and rolled back after it
  completed. This ensures that the database state stays clean between
  test runs. |SqlAlchemyFixture| can also create tables (and
  associated persisted classes) on the fly for use in tests.

|WebFixture| and |WebServerFixture|
  These Fixtures work together to start up a web server, and a
  selenium-driven web browser for use in tests. The web server runs in
  the same thread and database transaction as your tests. This means
  that if a breakage occurs server-side your test will break
  immediately, with a relevant stack trace. It also means that the
  idea of rolling back transactions after each test still works, even
  when used with Selenium tests.

Web browser interfaces
----------------------

Other important tools introduced are: |Browser| and |XPath|.
|Browser| is not a real browser -- it is our thin wrapper on top of
what is available from WebTest. |Browser| has the interface of a
|Browser| though. It has methods like `.open()` (to open an url),
`.click()` (to click on anything), and `.type()` (to type something
into an element of the web page).

We like this interface, because it makes the tests more readable.

When the browser is instructed to click on something or type into
something, an |XPath| expression is used to specify how to find that
element on the web page. |XPath| has handy methods for constructing
|XPath| expressions while keeping the code readable. Compare, for
example the following two lines to appreciate what |XPath| does. Isn't
the one using |XPath| much more explicit and readable?

.. code-block:: python
   
   browser.click('//a[href="/news"]')

.. code-block:: python

   browser.click(XPath.link().with_text('News'))

Readable tests
--------------

Often in tests, there are small bits of code which would be more
readable if it was extracted into properly named methods (as done with
|XPath| above). If you create a |Fixture| specially for testing the
AddressBookUI (in the example below), such a fixture is an ideal home
for extracted methods.  In the test below, AddressAppFixture contains
the nasty implementation of a couple of things we'd like to assert
about the application, as well as some objects used by the tests.

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2_dev/test_parameterised2_2.py

Testing JavaScript
------------------

.. sidebar:: Running tests with Selenium

   If you installed Reahl[all], as per :ref:`our introductory instructions
   <install-reahl-itself>`, you should have all the necessary testing
   packages installed, including Selenium and WebTest.

   To use Selenium's WebDriver with Firefox also install
   `geckodriver <https://github.com/mozilla/geckodriver>`_ as per the
   instructions for your platform. 

   (:doc:`See our instructions for installing geckodriver in Ubuntu <../tutorial/install-ubuntu>`.)


The |Browser| class used above cannot be used for all tests, since it
cannot execute javascript.  If you want to test something which makes
use of javascript, you'd need the tests (or part of them) to execute
in something like an actual browser. Doing this requires Selenium, and
the use of the web server started by |WebFixture| for exactly this
eventuality.

|DriverBrowser| is a class which provides a thin layer over Selenium's
WebDriver interface. It gives a programmer a similar set of methods
to those provided by the |Browser|, as used above. An instance of it is
available on the |WebFixture| via its `.driver_browser` attribute.

The standard |Fixture|\s that form part of Reahl use Firefox by default
in order to run tests.

You can change which browser is used by creating a new |Fixture| that inherits
from |WebFixture|, and overriding its `.new_driver_browser()` method.  

When the following is executed, a browser will be fired up, and
Selenium used to test that the validation provided by :class:`~reahl.component.modelinterface.EmailField` works
in javascript as expected. Note also how javascript is enabled for the
web application upon creation:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2_dev/test_parameterised2_3.py


