.. Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Tofu -- Test Fixtures and other handy testing utilities (reahl.tofu)
--------------------------------------------------------------------

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


Integration with nose
^^^^^^^^^^^^^^^^^^^^^

@test
"""""

.. autoclass:: reahl.tofu.test
   :members:
.. autoclass:: reahl.tofu.nosesupport.IsTestWithFixture
   :members:

set_run_fixture
"""""""""""""""

.. autofunction:: reahl.tofu.nosesupport.set_run_fixture


RunFixturePlugin
""""""""""""""""

.. autoclass:: reahl.tofu.nosesupport.RunFixturePlugin
   :members:

LongOutputPlugin
""""""""""""""""

.. autoclass:: reahl.tofu.nosesupport.LongOutputPlugin
   :members:

MarkedTestsPlugin
"""""""""""""""""

.. autoclass:: reahl.tofu.nosesupport.MarkedTestsPlugin
   :members:

TestDirectoryPlugin
"""""""""""""""""""

.. autoclass:: reahl.tofu.nosesupport.TestDirectoryPlugin
   :members:

LogLevelPlugin
""""""""""""""

.. autoclass:: reahl.tofu.nosesupport.LogLevelPlugin
   :members:

SetUpFixturePlugin
""""""""""""""""""

.. autoclass:: reahl.tofu.nosesupport.SetUpFixturePlugin
   :members:

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

vassert
"""""""

.. autoclass:: reahl.tofu.vassert


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
   
   
