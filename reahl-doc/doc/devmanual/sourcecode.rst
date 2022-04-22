.. Copyright 2017 Reahl Software Services (Pty) Ltd. All rights reserved.

Reahl source code
=================

Reahl source is hosted on `github <https://github.com/reahl/reahl>`_.

Reahl components
----------------

Reahl consists of several distinct components, each separately
installable with pip. The Reahl github project contains the source of
all of these. They are all released together and carry the same
version number.

Each of our `components` is packaged as a `distribution package
<https://packaging.python.org/glossary/#term-distribution-package>`_.


The root directory
------------------

The root of the source tree contains the component called
'reahl'. This component has the correct dependencies to all the
versions of the other components that are designed to work
together. In the source code, it contains:

 - the source code of all the other components that contain actual code
 - the metadata used to provide information about all the components
 - the current version of all components

To make :doc:`our development environment <devenv>` manageable and
reproducible, the root directory contains a **docker-compose.yaml**, 
**docker-compose.override.yaml** and a few useful scripts in the 
`scripts/` subdirectory.

It also contains a `debian/` directory from which we derive the
version numbers of projects and other metadata, such as project
descriptions. This is referred to from the `.reahlproject` in the
root.


Other components
----------------

The other components each reside in a subdirectory starting with
`reahl-<unique name>`.

Each such directory is dealt with as if it is a project in its own
right. Each component has:

 - its own `.reahlproject`;
 - its own `setup.cfg`;
 - a `Python namespace package <https://packaging.python.org/guides/packaging-namespace-packages/>`_ called `reahl`;
 - a `Python package <https://packaging.python.org/glossary/#term-import-package>`_ containing its production code; and
 - a `Python package <https://packaging.python.org/glossary/#term-import-package>`_ containing its testing code and data.

The package with code is named the same as the `<unique name>` part of the subdirectory of its component.

The package with testing code is named the same as the one with production code, but with `_dev` appended.

.. _making_sense:

Making sense of code
--------------------

.. sidebar:: Note on tools

   Plantuml is not installed in our Docker dev container, since we use it via
   plugins to our IDEs while editing code. These IDEs are installed outside
   of the Docker dev container.

   We'd love to replace Freeplane with something that graphically
   shows the `_dev` directory structure, and each file or subdirectory
   in it as a node in the presented outline. This way we won't
   duplicate information.

We use tests and UML designs to serve as a summary of the requirements
for a component. These are all located in the `_dev` package of a
component. In some cases there's also an outline of such requirements
which serves as table of contents.

Our table of contents is called `contents.mm` and `can be viewed using
the Freeplane mind mapping tool
<https://sourceforge.net/projects/freeplane/>`_. The structure of this
outline should resemble the directory structure if the `_dev` package.

Each subdirectory or `test_*.py` file represent some topic in the
table of contents. Inside
each test file there are test functions. Each test function has a
docstring that explains something about that topic. The test expresses
that "fact" in code and provides more detail.

In fact, the docstrings of our tests are an attempt at explaining (in
summarised fashion) everything a newcomer would need to know to
understand the system. The code of the test itself provides an example
or more detail about that fact. The table of contents give meaningful
structure to this body of knowledge.

There can also be `*.puml` files in the `_dev` package. Each one of
these contains a UML diagram which elucidates some topic as well. The
`*.puml` files `can be viewed graphically with any tool that supports
Plantuml format <http://plantuml.com/>`_.


