.. Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Configuration| replace:: :class:`~reahl.component.config.Configuration`


XML reference for .reahlproject
===============================

.. warning::

   We still use a limited subset of .reahlproject functionality internally. We recommend that you :ref:`switch over to
   using a setup.cfg with reahl-component-metadata instead of using a .reahlproject <define_component>`.

   This information stays here for the moment until users have migrated away from a .reahlproject.

   
The `.reahlproject` file in the root of your project is an XML file containing all kinds of information about your
project. It is used to create a `setup.py` on the fly. It contains other information such as how to find the 
|Configuration| for your project.

.. note::

   Run `reahl info` in the root of your project to see information about your project.

Project basics and dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _xml_project:

<project type="egg">
""""""""""""""""""""

  The project element is the top-level element in a .reahlproject file. It requires one attribute: `type`, which 
  should be the string "egg". 

.. _xml_version:

<version>
"""""""""

  Each released minor version of the project is listed using a <version> tag inside a <project> tag. It requires
  the `version_number` attribute which should be a string of the form major.minor where major and minor are
  integer numbers.  (Alpha versions can include a patch, and are handled as if they are the next minor version.)

  Inside this tag, there should be a <deps purpose="run"> to declare the dependencies of this version of the project.

  This tag is used mainly for computing migrations and dependencies. A database or dependency change thus counts
  as at least a minor version change.

.. _xml_deps:

<deps>
""""""

  A list of other eggs on which this project is dependent. It requires one attribute: `purpose`, which should
  the string "run" or "test" to indicate whether the listed dependencies are runtime dependencies, or that they
  are only needed for testing. (Runtime dependencies are available when testing too.)
  
  Each dependency is listed as a child of a `<deps>` element, using the `<egg>` or `<thirdpartyegg>` elements.

  <deps purpose="run"> is treated specially. It can only occur inside a <version> tag.

.. _xml_thirdpartyegg:

<thirdpartyegg>
"""""""""""""""

  Used to list a single dependency within a `<deps>` element. It requires one attribute: `name`, which should
  be set to the name of the egg referred to.
  
  **Use this element to refer to any project, even if you are not the developer**. Version information for such
  dependencies have to be specified explicitly. This is done using the `maxversion` and `minversion` attributes
  to this element.
  
<egg>
"""""

  Used to list a single dependency within a `<deps>` element. It requires one attribute: `name`, which should
  be set to the name of the egg referred to. Two more attributes are optional:  `version` can be specified (as
  a string) to pin down the version of the dependency manually to what is specified here; `ignoreversion`
  (a boolean value) can be specified as False to indicate that the dependency can be on any version of the
  specified egg.

  **Use this element only for other projects in your workspace**, under your control. Version information for such
  dependencies is automatically derived from the metainfo in your workspace.

  **Changed in 3.0**: The optional `name` and `version` attributes were added.


Component functionality
^^^^^^^^^^^^^^^^^^^^^^^

.. _locator-attribute:

locator attribute
"""""""""""""""""

  Several elements make use of an attribute named `locator`. The value of this attribute is a string used to 
  locate a Python object (a class, function, classmethod etc) which was defined in module scope. The string 
  has the form 'package.module:name' where the part before the colon is a dot-separated package path to the 
  module concerned. The part after the colon is the name of the object to import. It can be a simple name, 
  but for class attributes it can also be dot-separated (ie, 'MyClass.method_name').

.. _xml_configuration:

<configuration>
"""""""""""""""

  Used to indicate the :class:`~reahl.component.config.Configuration` class to be used for this component. It
  requires a :ref:`locator-attribute`.

.. _xml_persisted:

<persisted>
"""""""""""

  Used to list all the classes in this component that are persisted, using an ORM and hence need special handling.
  Each class is listed in-order using a `<class>` element.

.. _xml_class:

<class>
"""""""

  Used to list one class in this component as part of either the `<persisted>` list of classes,
  or the `<migrations>` list. It requires a :ref:`locator-attribute`.


.. _xml_translations:

<translations>
""""""""""""""

  Used to indicate the Python package in this component used to ship language catalogues for 
  internationalisation purposes. It requires a :ref:`locator-attribute`. Note that since it
  indicates a package only, the `locator` should not include a colon at all.

<migrations>
""""""""""""

  Used to list all the :class:`~reahl.component.migration.Migration` classes for a specific <version> of
  this component. Each class is listed in-order using a `<class>` element.

.. _xml_schedule:

<schedule>
""""""""""

  Used to indicate a function or class method to be called every time ``reahl runjobs``
  is run. It requires a :ref:`locator-attribute` for the relevant function or class method.

<namespace>
"""""""""""

  Used to list a number of Python packages that are `namespace packages 
  <http://pythonhosted.org/distribute/setuptools.html#namespace-packages>`_ : A namespace package is a
  Python package of which some modules are contained in separate eggs. Each package is listed using
  the `<package>` element.
  
<package>
"""""""""
  
  Lists a single Python package by name as being a namespace package (see `<namespace>`). It requires
  one attribute, `name` which is the name of the Python package.

<export>
""""""""

  Exports the class given by the :ref:`locator-attribute` using the `name` attribute
  as a name. The export is done under the entry point named in `entrypoint`.

<script>
""""""""

  Exports the class method or function named by the :ref:`locator-attribute` as a script
  with the name given by the `name` attribute.

Development and packaging
^^^^^^^^^^^^^^^^^^^^^^^^^

.. _xml_metadata:

<metadata>
""""""""""

  This section is used to provide metadata about the project. Each piece of metadata needed by a project
  is specified using an `<info>` element. A metadata element requires one attribute, the `type` which
  should be set to the string "reahlproject". This indicates that the metadata is hardcoded in the 
  `.reahlproject` file. (The implementation is designed to be extensible to use metadata from other sources
  as well.
  
  The following `<info>` elements are required: version, description, long_description, maintainer_name, 
  maintainer_email. 

  All of these elements are strings, but version should adhere to a subset of 
  `PEP0440 <https://www.python.org/dev/peps/pep-0440/>`:  `N(.N)*[{a|b|rc}N]` with only three dotted N's 
  allowed. For example: '1.2.3' for major.minor.patch versions.

  If this section is not present, the following defaults are used:

  project_name
    the name of the current directory

  version
    0.0    (This can include a patch version, eg. 1.0.3)

  ... with `'No {} provided'.format(name)` for all the others.

<info>
""""""

  Use an `<info>` element inside a <metadata> element to supply one piece of metadata for a project. The 
  `<info>` element requires a `name` attribute which indicates which bit of information it supplies. The 
  text contents of the `<info>` element contains the actual information.

<sourcecontrol>
"""""""""""""""

  If the `<sourcecontrol>` of a project is specified, it is used to infer the status of a project in development.
  For example, if you run ``reahl list -s`` a status is shown for each project listed. See ``reahl explainlegend``
  for more information.
  
  Currently two types of source control system are supported: Bazaar and Git. Use an attribute `type` set to the string
  "git" or "bzr" to indicate which source control system the project uses.

<distpackage>
"""""""""""""

  Use `<distpackage>` to indicate a package that should be built for distributing your project. 
  The following package type are supported:

   - sdist: a Python egg source tarball.
   - wheel: a Python wheel (universal).

  Set the `type` attribute of distpackage tag to one of the types above.  
  
  To build your distribution packages as per the .reahlproject file, run ``reahl build``. Such packages
  are not yet uploaded.

<packageindex>
""""""""""""""

  Can be specified as child of a `<distpackage>` to indicate that the package should be uploaded to this
  repository. A `<packageindex>` represents a PyPi repository. It requires an attribute named `repository`
  which should be set to the URL of the repository (for example: https://pypi.org/project/reahl-workspace/).
  
  A particular `<distpackage>` may be uploaded to several different repositories, each named in a 
  `<packageindex>` element.


