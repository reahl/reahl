.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Testing
=======

TODO: explain all the new fixture stuff

Tests are central to our development process., :ref:'as alluded to
before<making_sense>'. We depend on a testing infrastructure build
using :class:`~reahl.tofu.Fixture`\s.


.. sidebar:: Behind the scenes

   The Reahl testing tools are mostly wrappers and extensions of other
   testing tools out there. `Pytest
   <https://docs.pytest.org/>`_ has already been
   mentioned. The other important tools are: `WebTest
   <http://webtest.pythopaste.org>`_ and `Selenium
   <https://pypi.python.org/pypi/selenium>`_ (the latter is used with
   `chromedriver
   <http://code.google.com/p/selenium/wiki/ChromeDriver>`_).


Foundational fixtures
---------------------

 ReahlSystemSessionFixture and RealSystemFixture

 database connection, schema creation(?), config, copying of config
 

Keeping the database clean
--------------------------

 SqlAlchemyFixture

 explain transactions


Testing web stuff
-----------------

 WebSessionFixture, WebFixture

 Browser, DriverBrowser etc

 Process in one thread, transactions and exception stacks in this context

 JavaScript

 in_background?
 

Testing without a real browser
------------------------------

Enough talk. Its time for a first test.

In the :doc:`previous section <parameterised>` an application was
developed which lets one add, view and edit Addresses on different
:class:`~reahl.web.fw.View`\ s. The second version of it used :class:`~reahl.web.ui.Button`\ s to navigate to the edit
:class:`~reahl.web.fw.View`\ s  of individual Addresses. This application is starting to get
cumbersome to test by hand each time a change is made to it. It needs
a test. A Test for it will also make it possible to set breakpoints
and investigate its internals while running.

Here is a first stab at a test for it. Sometimes it is useful to write
a test per explained fact; other times it is useful to write a test
for a little scenario illustrating a "user story". This test is an
example of the latter:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2_dev/test_parameterised2_1.py

The test should be run with pytest.

There are a number of :class:`~reahl.tofu.Fixture`\s available as part of Reahl to help you
test applications. Explaining all of them is outside of the scope of
this introductory section. For this test, it is useful to know some of
the things that happen behind the scenes.

The test is run with a :class:`~reahl.web_dev.fixtures.WebFixture`. :class:`~reahl.web_dev.fixtures.WebFixture` in turn depends on
a number of other :class:`~reahl.tofu.Fixture`\s, each responsible for something useful behind the scenes:

 :class:`~reahl.dev.fixtures.ReahlSystemSessionFixture`
    A session-scoped :class:`~reahl.tofu.Fixture` responsible for a number of basic concerns:
        
    It creates an empty database before any tests run, with the
    correct database schema of your application. The Elixir/Sqlalchemy
    classes used by your application are also initialised properly (no
    need to create_all/setup_all, etc).

    It also sets up an initial configuration for the system.

 :class:`~reahl.dev.fixtures.ReahlSystemFixture`
    A function-scoped copy of
    :class:`~reahl.dev.fixtures.ReahlSystemSessionFixture` which can
    be used and changed in tests. It ensures that changes you make to
    things like the system configuration are torn down before the next
    test
        
 :class:`~reahl.sqlalchemysupport_dev.fixtures.SqlAlchemyFixture`
    This one ensures a transaction is started before each test run,
    and rolled back after each test so as to leave the database
    unchanged between tests. It also contains a handy method
    :method:`~reahl.sqlalchemysupport_dev.fixtures.SqlAlchemyFixture.persistent_test_classes`
    that can be used to add persistent classes to your database schema
    just for purposes of the current test.
        
 :class:`~reahl.webdev.fixtures.WebServerFixture`
    A session-scoped :class:`~reahl.tofu.Fixture` that ensures a
    webserver is started before your tests run. It also maintains an
    instance of a selenium WebDriver that you can use to programatically
    surf to the currently served web application via a real web
    browser.

The only obvious feature of :class:`~reahl.web_dev.fixtures.WebFixture` used in this little test is the
creation of a WSGI application. `WebFixture.new_wsgi_app()` can create a
WSGI application in various different ways. This example shows how to
create a ReahlWSGIApplication from a supplied :class:`~reahl.web.fw.UserInterface`. By default javascript
is not turned on (although, as you will see later, this can be
specified as well).

Two other important tools introduced in this test are: :class:`~reahl.webdev.tools.Browser` and
:class:`~reahl.webdev.tools.XPath`.  :class:`~reahl.webdev.tools.Browser` is not a real browser -- it is our thin wrapper on top
of what is available from WebTest. :class:`~reahl.webdev.tools.Browser` has the interface of a
:class:`~reahl.webdev.tools.Browser` though. It has methods like `.open()` (to open an url),
`.click()` (to click on anything), and `.type()` (to type something
into an element of the web page).

We like this interface, because it makes the tests more readable to a
non-programmer.

When the browser is instructed to click on something or type into
something, an :class:`~reahl.webdev.tools.XPath` expression is used to specify how to find that
element on the web page. :class:`~reahl.webdev.tools.XPath` has handy methods for constructing
:class:`~reahl.webdev.tools.XPath` expressions while keeping the code readable. Compare, for
example the following two lines to appreciate what :class:`~reahl.webdev.tools.XPath` does. Isn't
the one using :class:`~reahl.webdev.tools.XPath` much more explicit and readable?

.. code-block:: python
   
   browser.click('//a[href="/news"]')

   browser.click(XPath.link_labelled('News'))

Readable tests
--------------

Often in tests, there are small bits of code which would be more
readable if it was extracted into properly named methods (as done with
:class:`~reahl.webdev.tools.XPath` above). If you create a :class:`~reahl.tofu.Fixture` specially for testing the
AddressBookUI, such a fixture is an ideal home for such methods.  In
the expanded version of our test below, AddressAppFixture was
added. AddressAppFixture now contains the nasty implementation of a
couple of things we'd like to assert about the application, as well as
some objects used by the tests.  (Compare this implementation of
`.adding_an_address()` to the previous implementation.)

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2_dev/test_parameterised2_2.py

Testing JavaScript
------------------

.. sidebar:: Running tests with Selenium

   If you installed Reahl[all], as per :ref:`our introductory instructions
   <install-reahl-itself>`, you should have all the necessary testing
   packages installed, including Selenium and WebTest.

   Using Selenium's WebDriver module with Chromium takes a bit more
   effort at the time of this writing. Since Chromium is the browser
   used by the Reahl :class:`~reahl.tofu.Fixture`\ s, this may trip you up when running the
   test above.

   In order to make it work, you will have to also install
   `ChromeDriver
   <http://code.google.com/p/selenium/wiki/ChromeDriver>`_ as per the
   instructions for your platform. 

   (:doc:`See our instructions for installing chromedriver in Ubuntu <install-ubuntu>`.)


The :class:`~reahl.webdev.tools.Browser` class used above cannot be used for all tests, since it
cannot execute javascript.  If you want to test something which makes
use of javascript, you'd need the tests (or part of them) to execute
in something like an actual browser. Doing this requires Selenium, and
the use of the web server started by :class:`~reahl.webdev.fixtures.BrowserSetup` for exactly this
eventuality.

:class:`~reahl.webdev.tools.DriverBrowser` is a class which provides a thin layer over Selenium's
WebDriver interface. It gives a programmer a similar set of methods
to those provided by the :class:`~reahl.webdev.tools.Browser`, as used above. An instance of it is
available on the :class:`~reahl.web_dev.fixtures.WebFixture` via its `.driver_browser` attribute.

The standard :class:`~reahl.tofu.Fixture`\s that form part of Reahl use Chromium by default
in order to run tests, and they expect the executable for chromium to
be in '/usr/lib/chromium-browser/chromium-browser'.

You can change which browser is used by creating a new :class:`~reahl.tofu.Fixture` that inherits
from :class:`~reahl.web_dev.fixtures.WebFixture`, and overriding its `.new_driver_browser()` method.  

When the following is executed, a browser will be fired up, and
Selenium used to test that the validation provided by :class:`~reahl.component.modelinterface.EmailField` works
in javascript as expected. Note also how javascript is enabled for the
web application upon creation:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2_dev/test_parameterised2_3.py


