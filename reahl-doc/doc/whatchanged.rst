.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.




What changed in version 5.0
===========================

.. |PrimitiveInput| replace:: :class:`~reahl.web.ui.PrimitiveInput`
.. |HTMLWidget| replace:: :class:`~reahl.web.ui.HTMLWidget`
.. |refresh_widget| replace:: the `refresh_widget` keyword argument of :meth:`~reahl.web.ui.PrimitiveInput`
.. |enable_refresh| replace:: :meth:`~reahl.web.ui.HTMLElement.enable_refresh`
.. |Widget| replace:: :class:`~reahl.web.fw.Widget`
.. |Input| replace:: :class:`~reahl.web.ui.Input`
.. |ButtonInput| replace:: :class:`~reahl.web.bootstrap.forms.ButtonInput`
.. |XPath| replace:: :class:`~reahl.webdev.tools.XPath`
.. |DriverBrowser| replace:: :class:`~reahl.webdev.tools.DriverBrowser`
.. |type| replace:: :meth:`~reahl.webdev.tools.DriverBrowser.type`
.. |click| replace:: :meth:`~reahl.webdev.tools.DriverBrowser.click`
.. |TransactionVeto| replace:: :class:`~reahl.sqlalchemysupport.sqlalchemysupport.TransactionVeto`
.. |nested_transaction| replace:: :meth:`~reahl.sqlalchemysupport.sqlalchemysupport.SqlAlchemyControl.nested_transaction`
.. |should_commit| replace:: :attr:`~reahl.sqlalchemysupport.sqlalchemysupport.TransactionVeto.should_commit`
.. |exposed| replace:: :class:`~reahl.component.modelinterface.exposed`
.. |FieldIndex| replace:: :class:`~reahl.component.modelinterface.FieldIndex`
.. |Field| replace:: :class:`~reahl.component.modelinterface.Field`
.. |Migration| replace:: :class:`~reahl.component.migration.Migration`
.. |with_discriminator| replace:: :meth:`~reahl.component.modelinterface.Field.with_discriminator`
.. |Layout| replace:: :class:`~reahl.web.fw.Layout`
.. |HTML5Page| replace:: :class:`~reahl.web.bootstrap.page.HTML5Page`
.. |ReahlWSGIApplication| replace:: :class:`~reahl.web.fw.ReahlWSGIApplication`
.. |Table.with_data| replace:: :meth:`reahl.web.ui.Table.with_data`
.. |bootstrap.Table.with_data| replace:: :meth:`reahl.web.bootstrap.tables.Table.with_data`
.. |DomainException| replace:: :class:`~reahl.component.exceptions.DomainException`
.. |ValidationException| replace:: :class:`~reahl.web.fw.ValidationException`
.. |Form| replace:: :class:`~reahl.web.ui.Form`
.. |FormLayout| replace:: :class:`reahl.web.ui.FormLayout`
.. |bootstrap.FormLayout| replace:: :class:`reahl.web.bootstrap.forms.FormLayout`
.. |add_alert_for_domain_exception| replace:: :meth:`~reahl.web.bootstrap.forms.FormLayout.add_alert_for_domain_exception`
.. |Alert| replace:: :class:`~reahl.web.bootstrap.ui.Alert`


Upgrading
---------

To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc
   

Backwards-incompatible changes
------------------------------
                                
Since this version is a major version update it is not
backwards-compatible with previous versions.  Everything that was
deprecated in older versions is removed, and some new backwards-incompatible
changes have been added.

@exposed
  Previously, if you marked a method with |exposed|, its returned |FieldIndex| did not take into account
  possible methods higher up in the inheritance hierarchy. This has been changed - |exposed| now always
  calls each method higher up in a hierarchy, thus the resultant |FieldIndex| now contains all |Field|\s
  added by overridden methods in the hierarchy.

Python 2 support
   Since `Python 2 is now officially retired <https://www.python.org/doc/sunset-python-2/>`_, this release 
   drops support for Python < 3.5.

ButtonInput
   |ButtonInput| now creates its own layout upon construction. Instead of setting your own |Layout| 
   on an already-created |ButtonInput|, use one or more of |ButtonInput|\'s new keyword arguments upon
   construction: `style`, `outline`, `size`, `active`, `wide` or `text_wrap`

Unique input names and IDs
   The name of an |Input| is derived from the name of its |Field|. Previously |Input| names used to be adapted
   automatically so as to prevent name clashes between different |Input|\s on a |Form|. This is no 
   longer the case: an Input that has a name clash with another is now explicitly disambiguated by passing 
   it a |Field| with a modified name (see |with_discriminator|).

   Every Input is also now generated with a name and an ID that include the |Form|\'s ID and hence are 
   unique on the entire page.

Changes to nested_transaction
   |nested_transaction| used to yield the transaction object. It now yields a |TransactionVeto| object which
   can be used to force the transaction to be committed or not by setting |should_commit| to True or False.

Moved |HTML5Page|
   |HTML5Page| used to be in :mod:`reahl.web.bootstrap.ui`, but now resides in :mod:`reahl.web.bootstrap.page` 
   due to unavoidable dependency issues. Code need to be changed to import it from the new module.

Project metadata changes
   In a `.reahlproject` file, the runtime dependencies of a project used to be declared at the top-level
   with a ```<deps purpose="run">``` tag. The format of this file has now changed. Each released minor version
   of the project is now listed in a separate ```<version>``` tag, and the runtime dependencies are now stated inside
   the ```version``` tag for which those dependencies hold. In keepoing with this change, |Migration|\s no longer have 
   a ```version``` attribute to indicate which version they are for.


Changing contents in response to a changing Input
-------------------------------------------------

The major goal of this release was to incorporate more javascript
logic into pages, but still hide that behind Python.

We've done that by adding |refresh_widget|. When constructing a
|PrimitiveInput| you can pass an |HTMLWidget| as the `refresh_widget`
of the |PrimitiveInput|. When the |PrimitiveInput| is changed, it will
trigger a refresh of its `refresh_widget`. As before, it is necessary
to call |enable_refresh| on such an |HTMLWidget| for this to work.

Two examples were added to explain usage of this feature:

- :doc:`tutorial/whathappenedtoajax`
- :doc:`howto/responsivedisclosure`


Optimistic locking
------------------

This release adds functionality that guards against one user
overwriting changes made concurrently to the same data by another
user.

Consider, for example, the following sequence of events:

- user A opens page X
- user B opens page X
- user A changes input on a form on page X, and clicks on a |ButtonInput| that submits it
- the database is changed as a result of user A's changes in such a way that page X would not render the same anymore
- yet, user B still has the old page X open, and now makes similar changes on that page and clicks on a |ButtonInput| that submits the info

Without intervention in the above scenario user B's changes might
overwrite those of user A or the application could break - depending
on how the code was written.

Reahl now computes a hash of all the input values on a form on a
page. When the page is submitted, this hash is sent back to the server
which recomputes the hash. If any differences are picked up, the user
is shown an error message explaining that someone else has changed the
same data and given the chance to refresh the values and try again.

This mechanism can also be customised to:

- ignore some |Input|\s in this check; or
- to include arbitrary |Widget|\s in the check

For more info, see the HOWTO:

- :doc:`howto/optimisticlocking`
  

Error pages
-----------

Previously if an application encountered an unexpected exception, it
would return an HTTP 5xx error code to the browser, which typically
displays an unhelpful, unattractive error page.

In this release introduces the concept of a `default_error_view`.

The effect of this is that error messages can be rendered within the
general look, feel and layout of your application. This happens by
default, but the mechanism can also be customised at several different
levels of your application.

For more info, see the HOWTO:

- :doc:`howto/customisingerrorpages`


Database schema evolution
-------------------------

Previously, if you had a database with schema for a particular version
of Reahl components (and your own), you could migrate said schema (and
your data) to the next new version of Reahl components. For example,
if you were using Reahl 3.0, you could upgrade to 3.1.

You could not do an upgrade that jumped versions. For example if your
app's version 1.0 depended on Reahl 3.0, you could not migrate
successfully to a version 2.0 of your app which used Reahl 5.0.

The database migration machinery in this version was extensively
overhauled to be able to handle any upgrade scenario we could
imagine. (This includes scenarios where, for example, dependencies of
components change amongst different versions of a component.)

Each Reahl component still only carries knowledge of its own
|Migration|\s so that a diverse set of components can be used together
in the same database without knowledge of one another. |Migration|\s
are still written the exact same way they always have been.

What has changed is what metadata is kept of a project. Instead of
only stating a project's current version and its dependencies, you now
have to list all released versions of the form major.minor. For each
such version also state its dependencies and migrations.

For more info, see the tutorial example:

- :doc:`tutorial/schemaevolution.rst`


Widget changes
--------------

Table footers
  |Table.with_data| and |bootstrap.Table.with_data| gained
  a `footer_items` keyword argument. This allows one to supply
  content for the table footer.

Domain exceptions and exception Alerts
  |DomainException| was changed to hold onto a list of possible error
  messages via its new `detail_messages` keyword argument. This is used,
  for example, by |ValidationException| where a |ValidationException|
  signals that there were validation errors and its `detail_messages`
  provide a list of all the specific validation failures.

  If an exception is present on a |Form| you should display it. Previously
  displaying its message in an |Alert| would have been enough, but with
  the list of `detail_messages` now included, one should really display
  that list as well - and with it all styled better.

  To do this |add_alert_for_domain_exception| was added to |bootstrap.FormLayout|\.
  This provides an easy way to add an error message in cases where there
  is an exception present on a |Form|. The |Alert| added by |add_alert_for_domain_exception|
  also includes a way for a user to react to the case where it is detected
  that another user made concurrent changes to underlying data.

Simple FormLayout
  |FormLayout| was added to provide similar functionality to |bootstrap.FormLayout|
  on a lower level. This is especially used in tests.
 

A more expressive and composable XPath
--------------------------------------

|XPath| has been changed significantly to make it more useful and expressive in tests.

You can now construct an |XPath| by chaining and composition. For
example, you can find a `div` with a specific css class like this::

    XPath.div().including_class('myclass')

|XPath| instances can be further composed in terms of one another::

   XPath.button_labelled('Save').inside_of(XPath.div().including_class('myclass'))
  

A more Ajax-friendly DriverBrowser
----------------------------------
   
When one generally tests an application, it is to be expected that
user actions could trigger ajax refreshes or generally refer to
elements that aren't visible on the page yet - hut that have to be
waited for to appear.

Test code that continually triggers such events and waits for the
results can obfuscate the intent of a test.

For this reason several |DriverBrowser| methods have been changed to
automatically do "the right thing" in such circumstances.

Methods like |type| and |click|\, for example, now always trigger a
`blur` event on the |PrimitiveInput| targeted and then wait for any
ajax that might have been triggered in response to finish before
returning.

This default behaviour can be overridden using keyword arguments where
appropriate.


Commandline tools
-----------------

Creating a new project
  You can now start a new project by checking out one of our examples,
  but with a different name. In such checked-out code module, package,
  and various other names are renamed appropriately.
  (See `reahl example -h`)

Help with configuration
  You can also create a fresh new configuration directory with configuration
  based on having answered a few questions interactively.
  (See `reahl createconfig -h`)

Hosting static file
  Sometimes you need to host static files directly via a proxy such as nginx.
  You can now get to all those static files by running `reahl exportstatic`.
  (See `reahl exportstatic`)


Docker instead of Vagrant
-------------------------

Maintaining our Vagrant boxes for development became a bit cumbersome. With
this release we have switched to using a Docker image for that purpose.

Downloading the Docker dev image is the quickest way to get started with Reahl
because in it Reahl is installed in a clean venv ready for use.

The Docker development image is not meant for production use. It comes with
Reahl as well as a bunch of development tools installed. 

More info on using it can be found in: :doc:`devmanual/devenv`.


ReahlWSGIApplication start_on_first_request
-------------------------------------------


When `running your app under uwsgi <https://uwsgi-docs.readthedocs.io/en/latest/>`_, the 
uWSGI server first imports your application and then forks several worker processes. If 
you start your application at module level (so that it is started after uwsgi imported 
your application) your application is also already connected to
its database...and the forked processes inherit these established connections.

Such database connections are not thread-safe and cannot be shared between processes.

The `start_on_first_request=True` of |ReahlWSGIApplication| ensures that your application 
need not be started when created. Instead, it will be started when it receives its first 
request and avoid this problem:

.. literalinclude:: ../reahl/doc/examples/tutorial/helloanywhere/helloanywherewsgi.py



Updated dependencies
--------------------

Some included thirdparty JavaScript and CSS libraries were updated:

- JQuery to 3.5.1
- Bootstrap to 4.5.2
- JQueryUI to 1.12.1 - but our distribution includes *only* the widget factory with :focusable and :tabbable, nothing else.
- JQuery.validate was updated to 1.19.1 (and patched).
- JQuery.form to 4.2.2
- JQuery.blockUI to 2.70.0
- js.cookie to 1.4.1
- Popper to 1.16
- holder to 2.9.7

Unchanged:

- JQuery BBQ 1.3pre (patched).
- JQuery-form 4.2.2.
- HTML5shiv to 3.7.3

The versions of some external dependencies were updated:

- alembic to 0.9.6
- Babel to 2.8
- beautifulsoup4 to 4.6
- docutils to 0.14
- lxml to 4.2
- mysqlclient to 1.3
- Pillow to 2.5
- ply to 3.8
- prompt_toolkit to 2.0.10
- psycopg2-binary to 2.7
- Pygments to 2.1.0
- python-dateutil to 2.8
- selenium to 2.42
- setuptools-git to 1.1
- SQLAlchemy to 1.2.0
- twine to 1.15.0
- tzlocal to 2.0.0
- watchdog to 0.8.3
- WebOb to 1.4
- wheel to 0.34.0
- wrapt to 1.10.2


