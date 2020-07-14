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
.. |Layout| replace:: :class:`~reahl.web.fw.Layout`
.. |HTML5Page| replace:: :class:`~reahl.web.bootstrap.page.HTML5Page`
.. |ReahlWSGIApplication| replace:: :class:`~reahl.web.fw.ReahlWSGIApplication`


Upgrading
---------

To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc
   

Backwards-incompatible changes
------------------------------
                                
Since this version is a major version update it is not
backwards-compatible with previous versions.  Everything what was
deprecated in older versions is removed now.

@exposed
  Previously, if you marked a method with |exposed|, its returned |FieldIndex| did not take into account
  possible methods higher up in the inheritance hierarchy. This has been changed - |exposed| now always
  calls each method higer up in a hierarchy, thus the resultant |FieldIndex| now contains all |Field|\s
  added by overridden methods in the hierarchy.

Python 2 support
   Since `Python 2 is now officially retired <https://www.python.org/doc/sunset-python-2/>`_, this release 
   drops support for Python < 3.5.

ButtonInput
   |ButtonInput| now creates its own layout upon construction. Instead of setting your own |Layout| 
   on an already-created |ButtonInput|, use one or more of |ButtonInput|\'s new keyword arguments upon
   construction: `style`, `outline`, `size`, `active`, `wide` or `text_wrap`

Unique input names and IDs
   Inputs used to automatically adapt their names so as to prevent name clashes on a form. This is no 
   longer the case: Inputs that have name clashes now have to be explitly disambiguated (see |PrimitiveInput|).
   Every Input now also is generated with an ID that is unique on the page.

Changes to nested_transaction
   |nested_transaction| used to yield the transaction object. It now yields a |TransactionVeto| object which
   can be used to force the transaction to be committed or not by setting |should_commit| to True or False.

Moved |HTML5Page|
   |HTML5Page| used to be in :mod:`reahl.web.bootstrap.ui`, but now resides in :mod:`reahl.web.bootstrap.page` 
   due to unavoidable dependency issues. Code need to be changed to import it from the new module.
   


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

- ignore some |Input|\s from such a check; or
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

Widget changes
--------------

Table and Column to allow for table footer content

FormLayout.all_alert_for_domain_exception


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
- Bootstrap to 4.5.0
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


