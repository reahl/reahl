.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Using Reahl in Vagrant
======================

We prefer to install all development tools specific to a project
inside a virtual machine managed by `Vagrant
<https://www.vagrantup.com>`_.

Reahl provides a vagrant box with many tools we use installed and ready to go.

If you know Vagrant and have it set up on your machine, you can skip
all Reahl installation instructions and instead just do the following:

* Create a directory somewhere with the following VagrantFile:

  .. literalinclude:: ../../../vagrant/Vagrantfile.example

* Then do:

  .. code-block:: bash

     vagrant up

If you do not know Vagrant, installing and learning it will serve you well for other things too. You'll need to install:
 * `Virtualbox <https://www.virtualbox.org/>`_ (on linux, just install virtualbox from your distribution's repositories); and
 * `Vagrant itself <https://www.vagrantup.com/docs/installation/>`_ (preferably always use the instructions on www.vagrantup.com).

