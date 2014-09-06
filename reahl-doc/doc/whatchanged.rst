.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
What changed in version 3.0
===========================

.. toctree::
   :hidden:
 
   declarativemigration

Python 3 support
----------------

This version of Reahl runs on Python 3 (>= 3.3) as well on Python 2.7. In 
order to achieve this, some major changes were necessary.


Updated dependencies
--------------------

Many of the versions of other packages Reahl 2.1 depends on do not
support Python 3. Thus, almost all dependencies were upgraded to 
versions compatible with Python 3. Most of these should go unnoticed
to users of Reahl, barring the exception discussed next.

The minor upgrades are:

   ================= ============= ========================
    Name              Old version   New version 
   ================= ============= ========================
    Babel             0.9           1.3  
    python-dateutil   1.5           2.2  
    docutils          0.8           0.12  
    psycopg2          2.4           2.5  
    alembic           0.5           0.6  
    lxml              3.2           3.3  
    WebTest           1.4           2.0  
    selenium          2.25          2.42  
    pillow            1.7.8         2.5  
    cssmin            0.1           0.2  
    BeautifulSoup     3.2           BeautifulSoup4 4.3  
    webob             3.2           4.3  
   ================= ============= ========================
  

SqlAlchemy and Elixir/Declarative
---------------------------------

SqlAlchemy was upgraded from version 0.7 to 0.9. Unfortunately Elixir
does not support these newer versions of SqlAlchemy, prompting us to
implement the framework, domain code and all examples using
`SqlAlchemy's declarative extension instead
<http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/declarative.html>`_.

Elixir has not been maintained for a while now, while Declarative is
actively maintained as part of SqlAlchemy. Declarative follows a more
conservative approach though, which means that you have to specify
much more SQL-related info in your Python code than is needed when
using Elixir. While it would be great to be able to circumvent the
verbosity of Declarative, specifying things explicitly involves quite
a bit less magic "under the hood" and getting rid of that magic has
quite a few positive effects. The better support one gets on mailing
lists of SqlAlchemy for Declarative (as opposed to Elixir being
largely defunct) is also a major plus.

This is a major change which is necessary to make Python 3 support
possible.  The switch from Elixir to Declarative impacts model code
built on previous versions of Reahl, using Elixir.

We provide two upgrade paths for users with code based on Elixir:

 1. **Use Reahl 3.0, but stay on Elixir**:

    Reahl 3.0 can be used in conjunction with a few components of
    Reahl 2.1: the Elixir implementation itself, and its small number 
    of dependencies. Following this path means there are no code changes 
    on your part, but you have to stay on Python 2.7 yourself. 

    In order to follow this route, specify the elixir keyword to 
    easy_install when upgrading or installing Reahl, eg::

       easy_install reahl[web,elixir,sqlite] --upgrade

 2. **Switch to using Declarative**:

    If you do not have any of your own code written using Elixir,
    following this route is simple. Just specify the declarative
    keyword to easy_install when upgrading or installing Reahl::

       easy_install reahl[web,declarative,sqlite] --upgrade

    *If you do have code of your own written in terms of Elixir*, you
    will have to change that code to use Declarative instead.  In
    order to understand what you need to do, there is no better guide
    than `Declarative's own documentation
    <http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/declarative.html>`_.

    If you have a database running in production that was made with
    your own code written in terms of Elixir, you will also have to
    provide database migrations to change the underlying schema
    from what it was using Elixir, to what it is using Declarative.
    

:doc:`Elixir to Declarative database migration guide <declarativemigration>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have a database running in production, and you want to upgrade
that to a newer version of Reahl, you should always migrate that
database schema (and possibly data) to be compatible with the newer
versions of components you will be using going forward. With the
change from Elixir to Declarative, Reahl includes quite a large number
of such database migrations.

.. note::
   
   The Sqlite database itself does not support migration of existing
   data very well, and as a result migration is only possible on
   PostgreSQL databases. See these posts for more information on
   the issue: `one of the last bullets of goals of alembic
   <https://bitbucket.org/zzzeek/alembic>`_ and `Christopher Allan's
   post about the issue <http://dustycloud.org/blog/sqlite-alter-pain/>`_.

If you decide to make the switch from Elixir to Declarative and you
*did not* have any of your own code written in terms of Elixir, you
can simply migrate such an existing database with the command::

   reahl-control migratedb /path/to/config/directory

(In fact, you should always run this command when upgrading Reahl for
a project with an existing database.)

If you do have code of your own written in terms of Elixir, and you
decide to make the switch with us, you will have to write code to make
such database migration possible for your own code.

Please see the :doc:`declarativemigration` for details on how to do
this, or feel free to ask for help on `the mailing list
<https://groups.google.com/forum/#!forum/reahl-discuss>`_.


Other changes
-------------

Moved modules
~~~~~~~~~~~~~

As a rule, a component named reahl-xxx would contain a package
reahl.xxx, with possibly sub modules, such as reahl.xxx.yyy. For a
small number of components, this is not true. Specifically,
reahl-domain includes reahl.partymodel, reahl.workflowmodel and
reahl.systemaccountmodel that do not fit this structure.

In this version, these have been moved to reahl.domain.partymodel,
reahl.domain.workflowmodel and reahl.domain.systemaccountmodel
respectively. Older imports will continue to work for now, but 
will eventually be removed.

Session scoped classes
~~~~~~~~~~~~~~~~~~~~~~

Classes that are @session_scoped used to have an attribute
'session'. This has been renamed to 'user_session'.

The relationship between a Party and a SystemAccount
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Previously, a Party always had a SystemAccount. It makes more sense to
be able to have Party objects with or without SystemAccounts. Hence,
the relationship was changed. Now, a Party does not have any knowledge
of a SystemAccount, but a SystemAccount has an 'owner', which is a
Party.

Behind-the-scenes changes to UploadedFile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`reahl.component.modelinterface.UploadedFile` instances are
constructed by the framework, not user code. Previously it was
constructed with a file-like object from which it effectively could
read the contents of the file from the client-connected socket. It is
now constructed with the entire contents of the file. The file
contents are always handled as bytes with no attempt to deduce
character encoding.

A naming convention for database objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The new SqlAlchemy provides a mechanism for dictating the naming
convention used to name database objects (constraints, etc). Using
this means the same conventions will be used across different
database backends -- something that will make migrations easier in
future. Reahl 3.0 now uses these conventions. The
:module:`reahl.sqlalchemysupport.sqlalchemysupport` module includes a
few functions that compute the names for such database objects
according to the new naming convention. This is helpful during 
database migrations.
