.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
What changed in version 4.0
===========================

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |Fixture| replace:: :class:`~reahl.tofu.Fixture`
.. |ExecutionContext| replace:: :class:`~reahl.component.context.ExecutionContext`                       

Bootstrap
---------

As promised with the release of Reahl 3.2, all the |Widget|\s in this
release are based on `Bootstrap <http://getbootstrap.com>`_.

The basic |Widget|\s in :mod:`reahl.web.ui` represent basic HTML, and
thus are unstyled but the complicated |Widget|\s only have
Bootstrap-based versions. It is recommended to import even basic HTML
|Widget|\s from :mod:`reahl.web.bootstrap.ui`.


Tofu - pytest instead of nosetests
----------------------------------

A lot of changes in this release happened behind the scenes, and in
our development environment. One such change is that our tests run on
`pytest <https://docs.pytest.org/en/latest/>`_ now, instead of on
`nosetests <http://nose.readthedocs.io/en/latest/>`_.

Tofu changed extensively to make this possible.

Support for nose has now been dropped from
|Fixture|\s, and instead we now support `pytest
<https://docs.pytest.org/en/latest/>`_.

A |Fixture| should *not* to be confused with
pytest.fixture. Whereas a pytest.fixture is a factory function that
pytest calls at appropriate times to create a single resource needed
by one or more tests, a |Fixture| is still a
collection of test resources that are used together by a test.

|Fixture|\s further differ from pytest.fixture in that you import them
where needed--there is no magic to how they are named or reused.
       
The old idea of a run fixture (built by means of a nose plugin) has
been removed. Instead |Fixture|\s now have scope similar to the scope
of pytest.fixtures.


Here is an example of how to use a |Fixture| with pytest::

  from reahl.tofu import Fixture, with_fixtures

  class MyFixture(Fixture):
     def new_thing(self):
         return 'thing'

  @with_fixtures(MyFixture)
  def test_something(f):
      assert f.thing == 'thing'


Previously a test could only have a single |Fixture|. That has been
changed: multiple |Fixture|\s can be used. Note that the argument
names declared with the test function are not important. |Fixture|\s
are assigned to arguments based on position only::

  from reahl.tofu import Fixture, with_fixtures

  class MyFixture(Fixture):
     def new_thing(self):
         return 'thing'

  class OtherFixture(Fixture):
     def new_thing(self):
         return 'other thing'

  @with_fixtures(MyFixture, OtherFixture)
  def test_something(f, f2):
      assert f.thing == 'thing'
      assert f2.thing == 'other thing'

|Fixture|\s can also depend on other |Fixture|\s. In this case use
:func:`~reahl.tofu.uses` to decorate the |Fixture| class, stating
which other |Fixture| classes it depends on, and what to name
these. At runtime, each |Fixture| is created and assigned to an
attribute on the |Fixture| that depends on it::

  from reahl.tofu import Fixture, with_fixtures, uses

  class MyFixture(Fixture):
     def new_thing(self):
         return 'thing'

  @uses(my_fix=MyFixture)
  class OtherFixture(Fixture):
     def new_thing(self):
         return 'other %s' % self.my_fix.thing

  @with_fixtures(OtherFixture)
  def test_something(f):
      assert f.thing == 'other thing'
  
By default, a |Fixture| has 'function' scope, meaning it is created
and set up before a test function, and torn down after the test
function ran. :func:`~reahl.tofu.scope` is used as decoration on the
|Fixture| class to change the scope. Currently, only 'function' and
'session' scopes are supported. A |Fixture| that has 'session' scope
is set up only once per test process, and torn down when the test
process ends::

  from reahl.tofu import Fixture, with_fixtures, uses

  @scope('session')
  class MyFixture(Fixture):
     def new_thing(self):
         return 'thing'

  @with_fixtures(MyFixture)
  def test_something(f):
      assert f.thing == 'other thing' # f here is the same instance in all tests

  @with_fixtures(MyFixture)
  def test_something_else(f):
      assert f.thing == 'other thing' # f here is the same instance in all tests


Tofu - other changes
---------------------

Some change in |Fixture| is not related to the pytest move.


Previously, you could add a method with name starting with 'del_' if
you needed to tear down one of the |Fixture| attributes created with a
corresponding 'new_' method. Support for these 'del_' methods have now
been removed. Instead, tear down can now happen inside the 'new_'
method which creates the instance by making use of a yield statement::

  from reahl.tofu import Fixture

  class MyFixture(Fixture):
     def new_thing(self):
         thing = 'thing'
         yield thing
         # tear down thing here

|Fixture| previously also had a default contextmanager, assumed to be
created with a `new_context` method on the fixture. This was present
because of our use of an |ExecutionContext| and our need to make sure
test code always ran within an appropriate |ExecutionContext|.

The idea of |ExecutionContext| does not belong in the domain of
|Fixture|\s, however, and it was really impossible to explain why a
|Fixture| should have an additional context manager without invoking
|ExecutionContext|.

For these reasons, |Fixture| now does not support or need an extra
contextmanager.  Instead, a new
:class:`~reahl.web_dev.fixtures.ContextAwareFixture` was added--as
part of :package:`reahl.web_dev`\--making the design of a |Fixture|
simpler.
         
Vagrant
-------

Development on Reahl itself now happens on a `Vagrant
<https://www.vagrantup.com//>`_ image. Using a publicly available box,
called `reahl/xenial64`.  This may be useful for projects using Reahl
as well. An example Vagrantfile for your projects is supplied in file
`vagrant/Vagrantfile.example` in the Reahl source code.


Git vs Bzr
----------

We have switched internally to use `git <https://git-scm.com/\>`_ and
`GitHub <https://github.com/reahl/reahl\>`. Previously, we needed to
provide our own `file_finder` function so that setuptools would know
which source files to include in a distribution, based on whether the
wile was added to `Bzr <http://bazaar.canonical.com/en/\>`_. Since
we're not using Bzr anymore, the Bzr `file_finder` was removed. If you
still use Bzr, `you can easily roll your own
<http://code.activestate.com/recipes/577910-bazaar-as-a-setuptools-file-finder/\>`_.


Devpi
-----

We have also stopped using `Devpi <http://doc.devpi.net/latest/\>`_
internally and hence removed the `devpitest` and `devpipush` commands
from the `reahl` commandline tool.


Updated dependencies
--------------------

Some thirdparty JavaScript libraries were updated:

  - JQueryUI to 1.12.1 - but our distribution includes *only* the widget factory, nothing else.
  - JQuery.validation was updated to 1.17.0
  - jquery-metadata plugin was removed

The versions of some external dependencies were updated:

  - BeautifulSoup to version 4.4
  - wheel to version 0.29
  - setuptools to version 32.3








