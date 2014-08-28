.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Testing
=======

.. sidebar:: Behind the scenes

   The Reahl testing tools are mostly wrappers and extensions of other
   testing tools out there. `Nosetests
   <https://nose.readthedocs.org/en/latest/>`_ has already been
   mentioned. The other important tools are: `WebTest
   <http://webtest.pythopaste.org>`_ and `Selenium
   <https://pypi.python.org/pypi/selenium>`_ (the latter is used with
   `chromedriver
   <http://code.google.com/p/selenium/wiki/ChromeDriver>`_).

Tests are central to our development process and hence some
understanding of how testing is done will also help you to understand
Reahl -- and the rest of this tutorial.

Here's how we like to think of tests: if you had to explain a system
to a newcomer from scratch, you'd explain a number of facts -- some
facts also build upon on other facts that have already been
explained. We try to identify these explanatory facts, and write a
test *per fact*. The code of the test itself provides an example
and/or more detail about that fact. Tests are thus a specification of
the requirements of the system, and can be used to explain the system
to someone.

In order to facilitate these ideas, some testing tools grew with
Reahl. This section gives a brief introduction.

Fixtures
--------

.. sidebar:: Examples in this section

   - tutorial.testbasics
   - tutorial.parameterised2

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

In order to test something, you usually need to create a number of
related objects first for use in the test itself. Creating these
objects can be tedious -- especially if they depend on each other.

Such a collection of objects used together by a test is called a test
:class:`~reahl.tofu.Fixture`. Reahl allows one to write a :class:`~reahl.tofu.Fixture` as a separate
class. Defining a :class:`~reahl.tofu.Fixture` separately from the test that is using it
allows for the :class:`~reahl.tofu.Fixture` to be re-used by different tests, and even by
other :class:`~reahl.tofu.Fixture` classes. Separating the :class:`~reahl.tofu.Fixture` also helps keep the test
itself to read more like a requirements specification and less like
code.

Here's how :class:`~reahl.tofu.Fixture`\ s work: For each object that will form part of the
:class:`~reahl.tofu.Fixture`, a programmer writes a method on the :class:`~reahl.tofu.Fixture` class which will
create the object when called.  The name of the method is "`new_`"
prefixed to the name of the object.  (Assuming an object named
`my_object`, you would add a method to the fixture named
`new_my_object`.) In order to use a :class:`~reahl.tofu.Fixture` with a specific test,
decorate the test using the `@test()` decorator, passing the :class:`~reahl.tofu.Fixture`
class to `@test()`.  The test method or function should also
expect a single argument in its signature: the :class:`~reahl.tofu.Fixture` instance.

The first time a program references `.my_object` on the :class:`~reahl.tofu.Fixture`
instance, the corresponding `new_` method will be called behind the
scenes to create the object. Subsequent accesses of `.my_object` will
always bring back the same instance which was created on the first
access.

Here is a simple test which illustrates how :class:`~reahl.tofu.Fixture`\ s work:

.. literalinclude:: ../../reahl/doc/examples/tutorial/testbasics.py
   :end-before: # ------- dependent setup objects example


:class:`~reahl.tofu.Fixture`\ s are all about objects that depend on one another. The
following example shows a :class:`~reahl.tofu.Fixture` with two objects: a `.name`, and a
`.user`. The User object is initialised using the `.name` which
accompanies it on the :class:`~reahl.tofu.Fixture`. For simplicity, the actual code of User
is just included in the test. Note also how SimpleFixture is reused
here, by deriving from it:

.. literalinclude:: ../../reahl/doc/examples/tutorial/testbasics.py
   :start-after: # ------- dependent setup objects example
   :end-before: # ------- using new_ methods directly

Things can get more interesting though. A useful convention is to
create `new_*` methods with keyword arguments.  This way one can use
the `new_*` method to create slightly modified versions of the default
object available on the :class:`~reahl.tofu.Fixture`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/testbasics.py
   :start-after: # ------- using new_ methods directly


Set_up, tear_down, and run fixtures
-----------------------------------

Since :class:`~reahl.tofu.Fixture`\ s mostly consist of a bunch of `new_` methods, they
usually do not need traditional methods for settting up a fixture, or
tearing the fixture down afterwards. In some rare cases this is still
needed though. One may want to start a web server before a test, and
stop it afterwards, for example. Any method on a :class:`~reahl.tofu.Fixture` can be run
before or after the test it is used with. Just annotate the method
with `@set_up` or `@tear_down` respectively.

Sometimes such setup can take a long time and would slow down tests if
it happens for each and every test. When testing web applications, for
example, you may want to fire up a browser before the test -- something
that takes quite a long time.  For this reason Reahl provides an
extension to nosetests to which you can specify a "run :class:`~reahl.tofu.Fixture`". A run
:class:`~reahl.tofu.Fixture` is used for all tests that are run together. It is set up
before all the tests are run, and torn down at the end of all test
runs.  Normal :class:`~reahl.tofu.Fixture`\ s that are attached to individual tests also have
access to the current run :class:`~reahl.tofu.Fixture`.

To specify which run :class:`~reahl.tofu.Fixture` should be used for a test run, use
the ``--with-run-fixture`` (or -F) argument to nosetests.


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

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2_dev/parameterised2tests1.py

The test should be run with nosetests,
using ``--with-run-fixture=reahl.webdev.fixtures:BrowserSetup``.

There are a number of :class:`~reahl.tofu.Fixture`\ s available as part of Reahl to help you
test applications. Explaining all of them is outside of the scope of
this introductory section. For this test, it is useful to know some of
the things that :class:`~reahl.webdev.fixtures.BrowserSetup` does: Before the tests start to run, it
creates an empty database with the complete schema of your
application. The Elixir/Sqlalchemy classes used by your application
are also initialised properly (no need to create_all/setup_all, etc).

The test is run with a :class:`~reahl.web_dev.fixtures.WebFixture`. :class:`~reahl.web_dev.fixtures.WebFixture` depends on the presence
of a :class:`~reahl.webdev.fixtures.BrowserSetup` run :class:`~reahl.tofu.Fixture` -- that's why :class:`~reahl.webdev.fixtures.BrowserSetup` should be
specified to nosetests when run.

The only obvious feature of :class:`~reahl.web_dev.fixtures.WebFixture` used in this little test is the
creation of a WSGI application. `WebFixture.new_wsgi_app()` can create a
WSGI application in various different ways. This example shows how to
create a ReahlWSGIApplication from a supplied :class:`~reahl.web.fw.UserInterface`. By default javascript
is not turned on (although, as you will see later, this can be
specified as well).

Behind the scenes, :class:`~reahl.web_dev.fixtures.WebFixture` also has the job of starting a new
database transaction before each test, and rolling it back after each
test. Hence no real need to tear down anything...

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

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2_dev/parameterised2tests2.py

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

The standard :class:`~reahl.tofu.Fixture`\ s that form part of Reahl use Chromium by default
in order to run tests, and they expect the executable for chromium to
be in '/usr/lib/chromium-browser/chromium-browser'.

You can change which browser is used by creating a new run :class:`~reahl.tofu.Fixture` that inherits
from :class:`~reahl.webdev.fixtures.BrowserSetup`, and overriding its `.web_driver()` method.  Some
details regarding how the browser is configured (such as the binary
location of the browser) can similarly be changed by overriding the
relevant `.new_` method of that class.

When the following is executed, a browser will be fired up, and
Selenium used to test that the validation provided by :class:`~reahl.component.modelinterface.EmailField` works
in javascript as expected. Note also how javascript is enabled for the
web application upon creation:

.. literalinclude:: ../../reahl/doc/examples/tutorial/parameterised2/parameterised2_dev/parameterised2tests3.py


