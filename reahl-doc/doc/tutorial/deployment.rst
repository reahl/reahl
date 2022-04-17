.. Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.

Deploying a production site
===========================

.. sidebar:: Examples in this section

   - tutorial.helloanywhere
   - howto.hellonginx

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>

The easiest way to run your application is at PythonAnywhere_. :doc:`See our howtos <../howto/index>` for more options.


Your PythonAnywhere account
---------------------------

Head over to PythonAnywhere_ and create a
free account. The user name you choose for this account will become
the name of your web application. For example if you use `myname`,
your app will be accessable on something like
`http://myname.pythonanywhere.com` (assuming `myname` is the name you
registered with).

.. _build:

Build and upload the `helloanywhere` example
--------------------------------------------

Back home on your own machine, check out the `tutorial.helloanywhere`
example.  Build a distribution package archive for the example by
running (from the example's directory):

.. code-block:: bash

   python -m build --wheel


This `builds a wheel <https://pythonwheels.com/>`_ in the dist/ subdirectory
of your project.

.. note::
   To use this command, you have to have the `build project <https://pypi.org/project/build/>`_ installed:
   ``python -m pip install build``

In your browser on PythonAnywhere_, go to the
"Files" tab. Add a directory named `dist` in your home directory and
upload the wheel into `dist`.


Install
-------

Head over to the "Consoles" tab on PythonAnywhere_ and start a new
`bash` console. In the console, create a virtualenv for python
3:

.. code-block:: bash

   mkvirtualenv -p python3 helloanywhere

Notice that your prompt should now start with `(helloanywhere)` to
indicate the new virtualenv is activated.

Install your app inside the activated virtualenv:

.. code-block:: bash

   pip install -f ~/dist/ helloanywhere


Configure
---------

An application in production should not have any "dangerous default"
settings. The helloanywhere example contains the necessary production
config in its `prod/etc` directory.

Head over to PythonAnywhere_ again, to the
"Files" tab and create an `etc` directory inside your home
directory. Upload the config files from the example's `prod/etc`
to that new directory.


Create a database
-----------------

Head back to the PythonAnywhere_ "Consoles" tab,
and from there to the previously created bash console.

In the console, create the database:

.. code-block:: bash

  reahl createdb etc
  reahl createdbtables etc


Serve your app
--------------

The last step is to point PythonAnywhere_ to your app.

Go to the "Web" tab, and click on the "Add new web app" button. You will be asked to make a few choices:

- When asked to choose a web framework, choose "Manual config" (and do not forget to recommend Reahl for inclusion in the list!).
- On the next step choose a Python newer than 3.5.

Once the web app is created, scroll down to the "Code" section and
click on the WSGI configuration file. Delete everything in that file
and replace it with the contents of `helloanywherewsgi.py`:

.. literalinclude:: ../../reahl/doc/examples/tutorial/helloanywhere/helloanywherewsgi.py

Go back to the bash console you created before, and check what the virtualenv path is:

.. code-block:: bash

   echo $VIRTUAL_ENV

Copy the output of the command above and head back to the created web app. In the "Virtualenv"
section, paste this path in the input asking you to "enter path to
virtualenv if desired".

Click on the green "Reload" button right at the beginning of the web app configuration page.

Your site is now live! Click on the link in the heading "Configuration for..." to visit it.


.. _PythonAnywhere: https://www.pythonanywhere.com/?affiliate_id=0017b17d


