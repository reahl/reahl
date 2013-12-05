.. Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Overview
========

Introductory material
---------------------

In order to get an idea of what Reahl is, please :doc:`take a tour of
its features <features/index>`.  Several defining features are listed
there, with links to pages with more detail and examples.

The :doc:`Getting started guide <tutorial/gettingstarted>` will enable you to
start experimenting and working with Reahl.

To start learning Reahl in earnest, you can work through the :doc:`web
application tutorial <tutorial/index>`.

.. The :doc:`programmer's guide <devmanual/index>` contains information
   on how we work and how the internals of Reahl is structured.

Reference material
------------------

The Reahl web framework is built in terms of a collection of useful
components geared for the development of server applications in
Python.

The main components of Reahl are illustrated in the figure below:

.. figure:: overview.png
   :width:  90%



Component framework
~~~~~~~~~~~~~~~~~~~

The component framework contains the infrastructure that enables
Reahl's brand of component-based development. It also allows a
programmer to build domain models that are annotated with information
used by user interface code.

The core of the Reahl component framework is implemented in
`reahl-component`.  Interfaces for concepts defined by the Reahl
component framework (but not implemented by it) are in
`reahl-interfaces`. Support for different databases or ORM tools is
implemented in separate components: `reahl-postgresqlsupport`,
`reahl-sqlalchemysupport` and `reahl-sqllitesupport`.

All of these components are discussed under the heading of
:doc:`component/index`.


Web framework
~~~~~~~~~~~~~

The web framework provides the tools for developing applications with
web-based user interfaces.

The core of the web framework is written such that it is independent
of the technology used for object persistence. This core is in the
`reahl-web` component. The web framework does use some objects that
are persisted though -- an implementation of these using Elixir is
provided in `reahl-web-elixirimpl`.

These components are discussed under :doc:`web/index`.

End-user functionality
~~~~~~~~~~~~~~~~~~~~~~

The end-user functionality included in the distribution of Reahl is
split into two components: `reahl-domain` and `reahl-domainui`.

The `reahl-domain` component contains the domain models and logic,
whereas `reahl-domainui` provides the related web user interfaces.

Simple support for sending emails is provided by `reahl-mailutil`.

All these are discussed in :doc:`domain/index`.

Development tools
~~~~~~~~~~~~~~~~~

The `reahl-tofu` component contains an extension to the `Nose
<https://nose.readthedocs.org/en/latest/>`_ unit test framework as
well as a small collection of other test utilities which can be used
with any test framework. Its reason for being is that it allows one to
separate a test fixture from tests themselves.

Stubble (in `reahl-stubble`) enables one to write stub classes that
will break if the interfaces of the classes they stub should change.

Infrastructure is provided in `reahl-dev` and `reahl-webdev` for
dealing with Reahl components using an extensible command line
tool. This includes a web server for development purposes and a number
of special tofu Fixtures that are useful when developing Reahl.

The development tools are discussed in detail in :doc:`devtools/index`
