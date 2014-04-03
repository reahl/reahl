.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Developing your own component
=============================

.. sidebar:: Examples in this section

   - tutorial.componentconfig
   - tutorial.migrationexample
   - tutorial.jobs

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

This section is relevant to anyone building a 'just a' web
application: Remember, when you program using Reahl, every bit of code
ends up being packaged somewhere as part of a component. This is true
for a web application as well, even if you do not want to re-use the
application in other applications. Code needs to be packaged and
distributed, and these packages are what we refer to as components.

There are some important issues addressed via this underlying
component model, and this section provides a brief introduction to
some of them. 

Making a component configurable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each Reahl component can have its own configuration. As explained in
:doc:`gettingstarted`, when an application starts up, the
configuration for each component that forms part of the application is
read from a separate file, from a shared configuration directory. We
have covered how to specify the configuration settings required by
other components before. It is time now to show how to make your own
code configurable using this mechanism.

To illustrate, we made slight changes to the simple address book
application presented in :doc:`uibasics`. The application consists of
a single :class:`~reahl.web.fw.View`. Amongst other things, that :class:`~reahl.web.fw.View` contains a heading with
the text "Addresses". In the example presented here, we give the
original example a twist: here, whether that heading is shown or not
is based on the value of a configuration setting.

To make a component configurable, you have to provide a class that
governs configuration for your component. The component infrastructure
also has to be made aware of this class, by registering the class in the
`.reahlproject` file of your component. Registering the configuration
class is the easy part. Just include a configuration element in your
`.reahlproject`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/componentconfig/.reahlproject
   :start-after:   The added configuration
   :end-before:   <persisted>

.. note:: Remember to run ``reahl setup -- develop -N`` after editing
	  the `.reahlproject` file so that those edits can take effect.

Config files are evaluated as Python code, but variable names are made
available in these files so that a config file basically looks like a
list of assignments to some predefined settings. For example, a config
file for our example would contain:

.. literalinclude:: ../../reahl/doc/examples/tutorial/componentconfig/etc/componentconfig.config.py

When the component framework reads the configuration for your
component, an instance of the registered configuration class is
created and assigned to a variable name while the config file is
evaluated. In this case, an instance of AddressConfig is assigned to
the `componentconfig` variable while the config file is evaluated.

Thus, setting config in this file amounts to setting attributes on an
instance of your registered configuration class. In that class, you
specify the name of the config file of the component (which by
convention ends on `.config.py`) and the name of the variable to which
an instance of your :class:`~reahl.component.config.Configuration` class will be assigned. Each of the
config settings for your component are also defined here.

The configuration class itself inherits from :class:`~reahl.component.config.Configuration` (in
`reahl.component.config`). Here is AddressConfig:

.. literalinclude:: ../../reahl/doc/examples/tutorial/componentconfig/componentconfig.py
   :pyobject: AddressConfig

As you can see, `filename` and `config_key` respectively specify the
file name of the config file and the name of the variable to which an
instance of AddressConfig will be assigned while evaluating that
file. To declare a specific configuration setting, a ConfigSetting is
created and assigned to the name the setting should have, as is shown
in the code.

It is good practice to always provide a default value for a
setting. If all your settings have sensible defaults, your application
can be started up and run without any config file present at
all -- something a new user will appreciate. Similarly, the description
is used to enable useful output when you run, for example:

.. code-block:: bash

   reahl-control listconfig -i etc/

Defining what configuration is needed by your component is only part
of the story. Actually using the configuration is the other part. A
programmer can get to the configuration for the currently running
application from anywhere in code. Just obtain the current
:class:`~reahl.component.context.ExecutionContext`, and ask it for the `.config`. There's an attribute
on this global config for each `config_key` of each :class:`~reahl.component.config.Configuration`
read, so that reading the config looks pretty much similar to setting
it. See how it is done in this example:

.. literalinclude:: ../../reahl/doc/examples/tutorial/componentconfig/componentconfig.py
   :pyobject: AddressBookPanel


Database schema evolution
~~~~~~~~~~~~~~~~~~~~~~~~~

.. sidebar:: Behind the scenes

   Important parts of the database migration functionality in Reahl is
   done using the `Operations` object of the `Alembic
   <https://pypi.python.org/pypi/alembic>`_ project.

Right at the end of :doc:`models` we show how one registers all
persistent classes of your component in a `.reahlproject` file, and
that the `reahl-control` script uses this information when you run
``reahl-control createdbtables etc``. These mechanisms are adequate
for managing a database when you develop a brand new application, or
an example. What happens much more commonly is making changes to the
code of an application that is already running somewhere, with
existing data in its database. Changes to the code of that application
frequently require changes to the underlying database schema as well,
and such changes to the schema need to be done without losing the data
that's already in the database. Reahl provides some infrastructure to
help you deal with such ":class:`~reahl.component.migration.Migration`\ s".

To show how :class:`~reahl.component.migration.Migration`\ s are handled, we have another example. This
example is again a variation of the simplest AddressBook application
developed in :doc:`uibasics`. This time, we extend Address to
include the date when the Address was first added. The date is simply
displayed next to an Address when listed.

In order to simulate a program that changes over time, the real
`added_date` is commented out in the example, leaving a hardcoded
'TODO' in its place. This makes it possible to run the application
with a database schema that does not include `added_date` at first. A
new schema will be needed when the actual `added_date` is uncommented,
without the need for other code changes:

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexample/migrationexample.py
   :pyobject: Address

As you know, each Reahl component has a version number. When you
install a new application, you will create the initial database schema
using ``reahl-control createdbtables etc``. While creating the schema
Reahl will make a note (in the database) of which version of your
component the schema was created for. When you work on a new version
of your component, you have to write one or more "migrations". A
:class:`~reahl.component.migration.Migration` is one change that needs to be made to the schema (and
perhaps data) of the previous version, in order to bring the schema in
line with the new version of the component. A migration can be as
simple as adding a single column. :class:`~reahl.component.migration.Migration`\ s can also require more
complicated code specific to your problem domain that does many
database changes in a specific sequence to get the schema changed
without damaging the data. In extreme cases, one needs more than one
:class:`~reahl.component.migration.Migration` to be done in a specific order.

After installing a new version of your component, you need to run the
following in order to migrate the old schema, using your provided :class:`~reahl.component.migration.Migration`\ s:

.. code-block:: bash

   reahl-control migratedb etc

The `migratedb` command first checks to see which version of your
component the current database schema corresponds with. All :class:`~reahl.component.migration.Migration`\ s
for your component are then inspected, and only the necessary ones are
run, in order, to bring the schema up to date with the currently
installed version of your component.

The code of each migration you write must include the (new) version
of the component it is for. Each migration should also be registered
in the `.reahlproject` of your component -- in the order in which
migrations should be run. :class:`~reahl.component.migration.Migration`\ s should not be coded using any
other code in your component, because all the :class:`~reahl.component.migration.Migration`\ s you write
will stay in your component forever, as is, even if the code of the
actual component itself changes over time.

A :class:`~reahl.component.migration.Migration` is a class which inherits from :class:`~reahl.component.migration.Migration`. It should have a
class attribute, `version`, which states which version of your
component it is for. The actual upgrading of the schema done by the
:class:`~reahl.component.migration.Migration` happens in its `.upgrade()` method. After all :class:`~reahl.component.migration.Migration`\ s of
all the components in the system have been run, each :class:`~reahl.component.migration.Migration`'s
`.upgrade_cleanup()` method is run. Complex :class:`~reahl.component.migration.Migration`\ s sometimes need
such a cleanup phase. 

Here is the :class:`~reahl.component.migration.Migration` for adding our `added_date` column:

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexample/migrationexample.py
   :pyobject: AddDate

The code doing the changes to the schema is written in terms of
SqlAlchemy's migration tool: `Alembic
<https://pypi.python.org/pypi/alembic>`_. Alembic typically is also
used to keep track of versioning of schemas and migration
scripts. Reahl does not use those parts of Alembic since Reahl has to
keep track of versions of components already. Reahl also deals with
the fact that a single application contains many components, each one
of which has its own schema, :class:`~reahl.component.migration.Migration`\ s and versions. When :class:`~reahl.component.migration.Migration`\ s are run,
however, Alembic is set up in the Reahl environment for a programmer
to just use the `alembic.op` module as any Alembic programmer
normally would do.

Registering the AddDate class in the `.reahlproject` file is similar
to registering persistent classes, it just happens in a `<migrations>`
tag, and the :class:`~reahl.component.migration.Migration`\ s are listed in the correct order:

.. literalinclude:: ../../reahl/doc/examples/tutorial/migrationexample/.reahlproject
   :start-after:   <migrations>
   :end-before:   </migrations>
   :prepend:   <migrations>
   :append:   </migrations>

To appreciate the example, you'd have to get your own copy of it (via
``reahl example tutorial.migrationexample``), and run everything you need to
in order to get its database tables created: ``reahl setup --
develop -N`` and ``reahl-control createdbtables etc``. Then run the
application and add a few Addresses. Doing all of this simulates an
application that ran somewhere for a while, with some data in its
database. 

The next step is to change the application:

- comment out the 'TODO' version of `added_date`, and uncomment the
  new implementation
- edit the `.reahlproject` file and increase the version of the
  component (in this example the version is hardcoded in the
  `.reahlproject` file precisely so that you can edit it).

After editing `.reahlproject`, remember to run, as usual:

.. code-block:: bash

   reahl setup -- develop -N

Finally, to change the database schema, run:

.. code-block:: bash

   reahl-control migratedb etc
 


Housekeeping jobs
~~~~~~~~~~~~~~~~~

Sometimes one needs some code to run at certain times to do some
regular housekeeping tasks. You can ship such jobs with your component
and register them with the component infrastructure. Remember, your
application is composed of many components, some of which you are not
the author of. Running the following will run all the scheduled jobs
of all the components that are part of your application:

.. code-block:: bash

   reahl-control runjobs etc

As an example, we've modified the AddressBook example in
:doc:`uibasics` again. This time, we've added a boolean flag in the
database for each Address that is true if the Address was added
today. When an Address is added to the database, this flag is set to
True. Address also has a class method, `.clear_added_flags()` which
sets all flags back to False. If this method is run once every day,
the flag would be True on newly added Addresses only.

.. literalinclude:: ../../reahl/doc/examples/tutorial/jobs/jobs.py
   :pyobject: Address

To register this job with the Reahl component infrastructure, add a
`<schedule>` tag in the `.reahlproject` file:

.. literalinclude:: ../../reahl/doc/examples/tutorial/jobs/.reahlproject
   :start-after:   </persisted>
   :end-before:   <alias

When you try out the example, do everything you need to do in order to
be able to start the application. Then add some Addresses using the
application. All Addresses will be shown as new. At this point, you
can run:

.. code-block:: bash
 
   reahl-control runjobs etc

Then refresh the home page of the application again, and you will see
that the Addresses are not listed as being new anymore.

This example is perhaps not a very good one... because not all jobs of
all the components used by your application will need running only
once a day! A job, such as `Address.clear_added_flags()` should
include code that makes sure it only does its work when necessary. You
can then use your operating system tools (such as cron) to run
``reahl-control runjobs etc`` very regularly -- say once every 10
minutes. Each scheduled job will now be invoked regularly, and can
check at each invocation whether it is time for it to do its work, or
whether it should ignore the current run until a future time.  This
way, all jobs can get a chance to be run, and be in control of when
they should run.
