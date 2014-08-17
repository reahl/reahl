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

SqlAlchemy had to be upgraded to 0.9 (instead of 0.7). Unfortunately
Elixir does not support these newer versions of SqlAlchemy, prompting
us to implement the framework and all examples using `SqlAlchemy's declarative 
extension instead <http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/declarative.html>`_.

This is a major change which is necessary to make Python 3 support possible. 
The switch from Elixir to Declarative impacts model code built on previous versions of Reahl,
using Elixir.

We provide two upgrade paths for users with code based on Elixir:

 1. Reahl 3.0 can be used in conjunction with a few components of
    Reahl 2.1: the Elixir implementation itself, and its small number 
    of dependencies. Following this path means there are no code changes 
    on your part, but you have to stay on Python 2.7 yourself. 

    In order to follow this route, specify the elixir keyword to 
    easy_install when upgrading or installing reahl, eg::

       easy_install reahl[web,elixir,sqlite] --upgrade

 2. Change your own code to use Declarative instead of Elixir. The 
    declarative implementation provided with Reahl 3.0 includes 
    migrations that change older database schemas created by the
    Elixir implementation to work with the current, Declarative 
    implementation.
    

:doc:`Elixir to Declarative migration guide <declarativemigration>`
-------------------------------------------------------------------

For any of your own code that gets changed over from Elixir to
Declarative, you will have to write migrations yourself.

Please see the :doc:`declarativemigration` for details on how to do this,
or discuss on `the mailing list <https://groups.google.com/forum/#!forum/reahl-discuss>`_.



