.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

Scaffolding for development (reahl-dev)
=======================================

The `reahl-dev` component provides commands used with components in development, as well as some scaffolding we mainly use to deal with
development of Reahl itself (which itself exists of many components that are versioned together and live in the same source tree).

.. seealso::

   :doc:`XML reference for .reahlproject <xmlref>`.

        
Reahl command line
------------------

The Reahl command line is installed when you install `reahl-component` and is invoked with the command `reahl`. The set
of commands it offers depends on other Reahl components you install.

To see the available commands, run::

  reahl help-commands

  
Below is a list of which commands some components add:

`reahl-dev`
  Commands to work with components in development. This includes commands like `extractmessages` used in development
  for internationalisation (i18n). It also includes commands like `shell` and `setup` for working with projects
  that are defined using a `.reahlproject` file.

`reahl-commands`
  Commands for working with the extra functionality provided by Reahl components in production. This includes managing databases, schemas
  and performing migrations as well as dealing with things like internationalisation and configuration.

`reahl-workstation`
  When using :doc:`the Reahl development Docker image <../devmanual/devenv>` install `reahl-workstation` on your
  host machine to provide commands to share terminal access via `Ngrok <https://ngrok.com>`_ or GUI windows with
  `Xpra <https://xpra.org>`_.

`reahl-webdev`
  Helpful commands when doing web development using the Reahl web framework (`reahl-web`).

`reahl-doc`
  Commands for working with examples included in the overall Reahl documentation.


The .reahlproject file
----------------------

You can use a .reahlproject file instead of having a `setup.py` (and in addition to having a `setup.cfg`).

Using a .reahlproject file means that a `setup.py` is generated for you from it with certain metadata
computed on the fly. Since we mainly intend for it to be used internally it is not documented here any longer.



