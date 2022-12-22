.. Copyright 2022 Reahl Software Services (Pty) Ltd. All rights reserved.

Other tools
===========


There is a loose collection of other tools which we mostly use
internally, but some of these are important to a developer using Reahl
as well:

Commands provided by reahl-dev
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you install reahl-dev, it adds a number of sub commands to the
`reahl` commandline tool.

Some of these we use internally to be able to deal with a project that
is, in turn, composed of many smaller projects. We use these to manage
the reahl project itself, which consists of reahl-web,
reahl-component, etc.

These commands allow you to define a selected set of projects, and run
certain commands on a selection (or all of) your projects, etc.

Each such command also just works for a single project when run inside
of it. Documenting commands specific to dealing with many projects is
outside the scope of this document, we just use them internally.

The commands (from reahl-dev) useful for running on a single project
are:

i18n commands
"""""""""""""

These are all related to managing strings in your code that are
translated into different human languages.  See :doc:`the i18n section
of the tutorial <../tutorial/i18n>` for an in depth introduction.

 - reahl extractmessages
 - reahl mergetranslations
 - reahl compiletranslations
 - reahl addlocale

reahl servesmtp
"""""""""""""""

The `reahl servesmtp` command starts up a fake mail (SMTP) server
which listens for SMTP connections, and just prints out the emails
sent via SMTP.

See :doc:`the tutorial for an example of use
<../tutorial/loggingin>`.



Commands provided by reahl-webdev
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installing `reahl-webdev` adds a few useful commands specifically
related to web development:

`reahl serve` starts a development webserver for the current
project. See `reahl serve -h` for more info.

`reahl createconfig` is a script that creates a typical configuration
for a project by prompting the user for information. See `reahl
createconfig -h` for more info.



Fixtures
^^^^^^^^

There are a number of Fixture classes we use for Reahl development,
and that could be useful for any developer using Reahl.  These are
introduced in more detail in :doc:`../devmanual/testing`.


Docker container
^^^^^^^^^^^^^^^^

The easiest way to develop using Reahl is to :doc:`use our pre-built
docker image <../devmanual/devenv>`.

  
