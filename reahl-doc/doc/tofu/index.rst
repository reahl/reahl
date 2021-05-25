.. Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.

Tofu
----

.. automodule:: reahl.tofu


Test Fixtures
^^^^^^^^^^^^^

Fixture
"""""""

.. autoclass:: reahl.tofu.Fixture
   :members:

scenario
""""""""

.. autoclass:: reahl.tofu.scenario
   :members:
.. autoclass:: reahl.tofu.fixture.Scenario
   :members:

set_up
""""""

.. autoclass:: reahl.tofu.set_up
   :members:
.. autoclass:: reahl.tofu.fixture.SetUp
   :members:

tear_down
"""""""""

.. autoclass:: reahl.tofu.tear_down
   :members:
.. autoclass:: reahl.tofu.fixture.TearDown
   :members:


Integration with pytest
^^^^^^^^^^^^^^^^^^^^^^^

with_fixtures
"""""""""""""

.. autoclass:: reahl.tofu.with_fixtures
   :members:
.. autoclass:: reahl.tofu.pytestsupport.WithFixtureDecorator
   :members:

uses
""""

.. autofunction:: reahl.tofu.uses


scope
"""""

.. autofunction:: reahl.tofu.scope


Testing for exceptions
^^^^^^^^^^^^^^^^^^^^^^

expected
""""""""

.. autofunction:: reahl.tofu.expected

NoException
"""""""""""

.. autoclass:: reahl.tofu.NoException

check_limitation
""""""""""""""""

.. autofunction:: reahl.tofu.check_limitation


Temporary files and directories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

file_with
"""""""""

.. autofunction:: reahl.tofu.file_with

temp_dir
""""""""

.. autofunction:: reahl.tofu.temp_dir

temp_file_name
""""""""""""""

.. autofunction:: reahl.tofu.temp_file_name

temp_file_with
""""""""""""""

.. autofunction:: reahl.tofu.temp_file_with

AutomaticallyDeletedDirectory
"""""""""""""""""""""""""""""

.. autoclass:: reahl.tofu.AutomaticallyDeletedDirectory
   :members:


