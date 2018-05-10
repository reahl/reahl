.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.




What changed in version 4.0
===========================

.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |ReahlWSGIApplication| replace:: :class:`~reahl.web.fw.ReahlWSGIApplication`
.. |Fixture| replace:: :class:`~reahl.tofu.Fixture`
.. |ExecutionContext| replace:: :class:`~reahl.component.context.ExecutionContext`
.. |ColumnLayout| replace:: :class:`~reahl.web.bootstrap.grid.ColumnLayout`
.. |ColumnOptions| replace:: :class:`~reahl.web.bootstrap.grid.ColumnOptions`
.. |ResponsiveSize| replace:: :class:`~reahl.web.bootstrap.grid.ResponsiveSize`
.. |Menu| replace:: :class:`~reahl.web.bootstrap.navs.Menu`
.. |Nav| replace:: :class:`~reahl.web.bootstrap.navs.Nav`
.. |Menu.add_a| replace:: :meth:`~reahl.web.bootstrap.navs.Menu.add_a`
.. |Menu.add_bookmark| replace:: :meth:`~reahl.web.bootstrap.navs.Menu.add_bookmark`
.. |Nav.add_dropdown| replace:: :meth:`~reahl.web.bootstrap.navs.Nav.add_dropdown`
.. |forms.CheckboxInput| replace:: :class:`~reahl.web.bootstrap.forms.CheckboxInput`
.. |ui.CheckboxInput| replace:: :class:`~reahl.web.ui.CheckboxInput`
.. |ui.CheckboxSelectInput| replace:: :class:`~reahl.web.ui.CheckboxSelectInput`
.. |forms.RadioButtonSelectInput| replace:: :class:`~reahl.web.bootstrap.forms.RadioButtonSelectInput`
.. |ui.RadioButtonSelectInput| replace:: :class:`~reahl.web.ui.RadioButtonSelectInput`
.. |ViewFactory| replace:: :class:`~reahl.web.fw.ViewFactory`
.. |UserInterface.define_view| replace:: :meth:`~reahl.web.fw.UserInterface.define_view`
.. |ViewFactory.set_slot| replace:: :meth:`~reahl.web.fw.ViewFactory.set_slot`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |Field.with_validation_constraint| replace:: :meth:`~reahl.component.modelinterface.Field.with_validation_constraint`
.. |Field.without_validation_constraint| replace:: :meth:`~reahl.component.modelinterface.Field.without_validation_constraint`
.. |BooleanField| replace:: :class:`~reahl.component.modelinterface.BooleanField`
.. |MultiChoiceField| replace:: :class:`~reahl.component.modelinterface.MultiChoiceField`
.. |DomainException| replace:: :class:`~reahl.component.exceptions.DomainException`
.. |UserInputProtocol| replace:: :class:`~reahl.web.interfaces.UserInputProtocol`




Upgrading
---------

This release has been a long time in the making and comes with many
changes. Various changes have been made to the underlying database
schema. To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc
   
                                
Bootstrap
---------

All the |Widget|\s in this release are based on `Bootstrap
<http://getbootstrap.com>`_. The older home-rolled |Widget| styling we
had was removed.

The basic |Widget|\s in :mod:`reahl.web.ui` represent basic HTML and
thus are unstyled. These are not really meant to be used directly.
More interesting |Widget|\s only have Bootstrap-based versions and
they live in modules inside :doc:`the reahl.web.bootstrap
package <web/bootstrap/index>`.

If you develop a site and use basic HTML |Widget|\s, like
:class:`~reahl.web.bootstrap.ui.P`, import all of them from from:
:mod:`reahl.web.bootstrap.ui`.


Backwards-incompatible changes
------------------------------

Since this version is a major version update it is not
backwards-compatible with previous versions.  Everything what was
deprecated in older versions is removed now.


Infrastructure
 :code:`ReahlApplication` (which is used to fire up you app via WSGI) was renamed to |ReahlWSGIApplication|.
 
Internationalisation
  :code:`Translator` was renamed to :class:`~reahl.component.i18n.Catalogue`.

Layout
 The way one creates a |ColumnLayout| and specifies options for
 creating columns has changed. A new class, |ColumnOptions| is now 
 used to specify various options relating to a specific column. This
 includes the offset of the column, which previously used to be
 specified as part of its |ResponsiveSize|.

 The arguments to :meth:`~reahl.web.bootstrap.grid.ColumnLayout` that
 define the columns can now be one of:
 
    - either just the column name as a string (which assumes default
      |ColumnOptions|); or
    - a tuple with the column name and a |ColumnOptions| object
      (previously this had to be a |ResponsiveSize|).

      
Basic Widgets
 A single checkbox is used fetch boolean input from a user, but a list
 of related checkboxes lets the user choose from a list of
 choices.

 The |forms.CheckboxInput| is a high-level construct which can be
 used for either purpose, depending on whether it is used with a
 |BooleanField| or a |MultiChoiceField|.

 :code:`reahl.web.bootstrap.forms.RadioButtonInput` is now named
 |forms.RadioButtonSelectInput| and `reahl.web.ui.RadioButtonInput` is
 :code:now named |ui.RadioButtonSelectInput|.
 
 Amongst the plain HTML |Widget|\s, |ui.CheckboxInput| serves
 the first purpose; |ui.CheckboxSelectInput| was added for the
 second. 
 

Fields and app construction
 The `slot_definitions` kwarg no longer exists on
 |UserInterface.define_view|. Rather call |ViewFactory.set_slot| on
 the returned |ViewFactory| to define the contents of the new view.
 
 The methods :code:`as_with_validation_constraint` and
 :code:`as_without_validation_constraint` on |Field| have been renamed
 to |Field.with_validation_constraint| and
 |Field.without_validation_constraint| for consistency with :doc:`our coding
 conventions <devmanual/conventions>`.

 
Menus
 |Menu| was moved to :mod:`reahl.web.bootstrap.navs`. It is not
 meant to be used directly, rather use |Nav|.  The :code:`.add_item`
 and :code:`.add_submenu` methods were removed in favour of the
 consistently named variants for adding items: |Menu.add_a|,
 |Menu.add_bookmark| and |Nav.add_dropdown|.


Declarative implementation
 An issue was discovered regarding the correct handling of
 |MultiChoiceField|\s when a |DomainException| occurred. In order to
 correctly save the input provided by a user, the methods on
 |UserInputProtocol| were changed to take an extra argument,
 `entered_input_type`.

   
Passwords
---------

Previous releases used md5 to encrypt passwords in the database. This
practice is no longer viewed as being secure. This release uses
`pbkdf2_sha512` password hashes `via passlib <https://passlib.readthedocs.io/en/stable/>`_.

Older passwords will automatically be changed to `pbkdf2_sha512` upon
a successful login.


Commandline tools
-----------------

The `reahl` and `reahl-control` tools have both been rolled into a
single `reahl` commandline tool. The commands it has vary depending
on which parts of Reahl you have installed. With reahl-dev installed,
for example, it will include commands only used in development.


Development environment
-----------------------

Development on Reahl itself now happens on a `Vagrant
<https://www.vagrantup.com//>`_ image using a publicly available box,
called `reahl/bionic64`.  This may be useful for projects using Reahl
as well. An example Vagrantfile for your projects is supplied in file
`vagrant/Vagrantfile.example` in the Reahl source code.

See :doc:`devmanual/devenv` for details.

As part of the move to develop in a Vagrant machine, we added a new
component, `reahl-workstation`.  You can `pip install
reahl-workstation` on your actual host. This gives you a simple
`reahl` commandline outside of the vagrant machine which helps with a
few simple things such as attaching to the xpra display running
inside. 

Mysql
-----

In addition to `PostgreSQL <https://www.postgresql.org>`_ and `Sqlite
<https://www.sqlite.org>`_ we now support `MySql
<https://www.mysql.com>`_ as well. Include `reahl-mysqlsupport` in
your dependencies to be able to use mysql as a backend.


Tofu - pytest instead of nosetests
----------------------------------

A lot of changes in this release happened behind the scenes and in
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
changed: multiple |Fixture|\s can be used now. Note that the argument
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

Some changes in |Fixture| is not related to the pytest move.


Previously, you could add a method with name starting with 'del\_' if
you needed to tear down one of the |Fixture| attributes created with a
corresponding 'new\_' method. Support for these 'del\_' methods have now
been removed. Instead, tear down can now happen inside the 'new\_'
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
|Fixture| should have an additional context manager without explaining
|ExecutionContext|.

For these reasons, |Fixture| now does not support or need an extra
contextmanager.  Instead, a new
:class:`~reahl.dev.fixtures.ContextAwareFixture` was added--as
part of :mod:`reahl.dev.fixtures`\--making the design of a |Fixture|
simpler.
         

Git vs Bzr
----------

We have switched internally to use `git <https://git-scm.com/>`_ and
`GitHub <https://github.com/reahl/reahl/>`_. Previously, we needed to
provide our own `file_finder` function so that setuptools would know
which source files to include in a distribution, based on whether the
file was added to `Bzr <http://bazaar.canonical.com/en/>`_. Since
we're not using Bzr anymore, the Bzr `file_finder` was removed. If you
still use Bzr, `you can easily roll your own
<http://code.activestate.com/recipes/577910-bazaar-as-a-setuptools-file-finder//>`_.


Devpi
-----

We have also stopped using `Devpi <http://doc.devpi.net/latest//>`_
internally and hence removed the `devpitest` and `devpipush` commands
from the `reahl` commandline tool.


Updated dependencies
--------------------

Some included thirdparty JavaScript and CSS libraries were updated:

  - JQuery to 3.3.1 with JQuery-migrate 3.0.1.
  - JQueryUI to 1.12.1 - but our distribution includes *only* the widget factory, nothing else.
  - JQuery.validation was updated to 1.17.0 (and patched).
  - jquery-metadata plugin was removed.
  - Bootstrap to 4.0.0.
  - JQuery BBQ to 1.3pre (patched).
  - JQuery-form to 4.2.2.
  - HTML5shiv to 3.7.3.

Some were added:

  - Added Popper 1.12.9.

The versions of some external dependencies were updated:

  - BeautifulSoup to 4.6.
  - Wheel to 0.29.
  - setuptools to 32.3.
  - Lxml version to 3.8.
  - SqlAlchemy to 1.2.0.
  - Alembic to 0.9.6.
  - Twine to 1.11.
  - Lxml to 4.2.




