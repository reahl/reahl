.. Copyright 2013, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Tools for unit testing
======================

Fixture overview
^^^^^^^^^^^^^^^^

.. uml:: ../../../reahl-web/reahl/web_dev/fixtures.puml


Basic fixtures
^^^^^^^^^^^^^^

.. automodule:: reahl.dev.fixtures

ContextAwareFixture
"""""""""""""""""""

.. autoclass:: reahl.dev.fixtures.ContextAwareFixture
   :members:

ReahlSystemSessionFixture
"""""""""""""""""""""""""

.. autoclass:: reahl.dev.fixtures.ReahlSystemSessionFixture
   :members:

ReahlSystemFixture
""""""""""""""""""

.. autoclass:: reahl.dev.fixtures.ReahlSystemFixture
   :members:

Managing a SqlAlchemy database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SqlAlchemyFixture
"""""""""""""""""

.. autoclass:: reahl.sqlalchemysupport_dev.fixtures.SqlAlchemyFixture
   :members:

Web development fixtures
^^^^^^^^^^^^^^^^^^^^^^^^

WebServerFixture
""""""""""""""""

.. autoclass:: reahl.web_dev.fixtures.WebServerFixture
   :members:


WebFixture
""""""""""

.. autoclass:: reahl.web_dev.fixtures.WebFixture
   :members:




Testing tools
^^^^^^^^^^^^^

WidgetTester
""""""""""""

.. autoclass:: reahl.webdriver.webdriver.WidgetTester
   :members:
   :inherited-members:

Browser
"""""""

.. autoclass:: reahl.webdriver.webdriver.Browser
   :members:
   :inherited-members:

DriverBrowser
"""""""""""""

.. autoclass:: reahl.webdriver.webdriver.DriverBrowser
   :members:
   :inherited-members:
      
XPath
"""""

.. autoclass:: reahl.webdriver.webdriver.XPath
   :members:

ReahlWebServer
""""""""""""""

.. autoclass:: reahl.webdev.webserver.ReahlWebServer
   :members:


