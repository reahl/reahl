.. Copyright 2013, 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.


.. |Migration| replace:: :class:`~reahl.component.migration.Migration`
.. |Configuration| replace:: :class:`~reahl.component.config.Configuration`
.. |ExecutionContext| replace:: :class:`~reahl.component.context.ExecutionContext`


Regular scheduled jobs
======================

.. sidebar:: Examples in this section

   - tutorial.jobsbootstrap

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

Any component used by your application can have jobs that need to be
run at regular intervals. Executing the following runs all jobs that
are scheduled to run:

.. code-block:: bash

   reahl runjobs etc


The `tutorial.jobsbootstrap` example needs its
`Address.clear_added_flags()` to run automatically, once a day.

.. literalinclude:: ../../reahl/doc/examples/tutorial/jobsbootstrap/jobsbootstrap.py
   :pyobject: Address


To register this job with the component, list it in :ref:`the "schedule" entry <setup_cfg_schedule>` of
the `component` option of your `setup.cfg` file:

.. literalinclude:: ../../reahl/doc/examples/tutorial/jobsbootstrap/setup.cfg
   :start-after:  # Register the job:


A job, such as `Address.clear_added_flags()` should
include code that makes sure it only does its work when necessary. You
can then use your operating system tools (such as cron) to run
``reahl runjobs etc`` very regularly -- say once every 10
minutes. Each scheduled job will now be invoked regularly, and can
check at each invocation whether it is time for it to do its work, or
whether it should ignore the current run until a future time.  This
way, all jobs can get a chance to be run, and be in control of when
they should run.


