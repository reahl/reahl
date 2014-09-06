.. Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
 
XML reference for .reahlproject
===============================

Project basics and dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

<project type="egg">
""""""""""""""""""""

  The project element is the top-level element in a .reahlproject file. It requires one attribute: `type`, which 
  should be the string "egg". An "egg" project is packaged as a Python egg.

<deps>
""""""

  A list of other eggs on which this project is dependent. It requires one attribute: `purpose`, which should
  the string "run" or "test" to indicate whether the listed dependencies are runtime dependencies, or that they
  are only needed for testing. (Runtime dependencies are available when testing too.)
  
  Each dependency is listed as a child of a `<deps>` element, using the `<egg>` or `<thirdpartyegg>` elements.
  
<egg>
"""""

  Used to list a single dependency within a `<deps>` element. It requires one attribute: `name`, which should
  be set to the name of the egg referred to. Two more attributes are optional:  `version` can be specified (as
  a string) to pin down the version of the dependency manually to what is specified here; `ignoreversion` 
  (a boolean value) can be specified as False to indicate that the dependency can be on any version of the
  specified egg.
  
  Use this element only for other projects in your workspace, under your control. Version information for such
  dependencies can be obtained from the metainfo in your workspace.

  **Changed in 3.0**: The optional `name` and `version` attributes were added.

<thirdpartyegg>
"""""""""""""""

  Used to list a single dependency within a `<deps>` element. It requires one attribute: `name`, which should
  be set to the name of the egg referred to.
  
  Use this element to refer to any project, even if you are not the developer. Version information for such
  dependencies have to be specified explicitly. This is done using the `maxversion` and `minversion` attributes
  to this element.
  

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

<configuration>
"""""""""""""""

  Used to indicate the :class:`~reahl.component.config.Configuration` class to be used for this component. It
  requires a :ref:`locator-attribute`.

<persisted>
"""""""""""

  Used to list all the classes in this component that are persisted, using an ORM and hence need special handling.
  Each class is listed in-order using a `<class>` element.

<class>
"""""""

  Used to list one class in this component as part of either the `<persisted>` list of classes,
  or the `<migrations>` list. It requires a :ref:`locator-attribute`.


<translations>
""""""""""""""

  Used to indicate the Python package in this component used to ship language catalogues for 
  internationalisation purposes. It requires a :ref:`locator-attribute`. Note that since it
  indicates a package only, the `locator` should not include a colon at all.

<migrations>
""""""""""""

  Used to list all the :class:`~reahl.component.migration.Migration` classes in this component.
  Each class is listed in-order using a `<class>` element.

<schedule>
""""""""""

  Used to indicate a function or class method to be called every time ``reahl-control runjobs``
  is run. It requires a :ref:`locator-attribute` for the relevant function or class method.

<attachedfiles>
"""""""""""""""

  Use this element to list a number of JavaScript or CSS files that are shipped inside this component.
  These files are concatenated at runtime into one big JavaScript or CSS file. Each file is listed
  using the `<file>` element.
  
  It requires an attribute named `filetype` which can only be the string "js" or "css" to indicate the
  types of files listed.

<file>
""""""

  Used to list a single file in an `<attachedfiles>` list.  It requires a single attribute, `path`: the 
  filename of the file, relative to the root of this module. Always use '/' as directory separator,
  regardless of the platform you are on.

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

<metadata>
""""""""""

  This section is used to provide metadata about the project. Each piece of metadata needed by a project
  is specified using an `<info>` element. A metadata element requires one attribute, the `type` which
  should be set to the string "reahlproject". This indicates that the metadata is hardcoded in the 
  `.reahlproject` file. (The implementation is designed to be extensible to use metadata from other sources
  as well.
  
  The following `<info>` elements are required: version, description, long_description, maintainer_name, 
  maintainer_email.

<info>
""""""

  Use an `<info>' element inside a <metadata> element to supply one piece of metadata for a project. The 
  `<info>` element requires a `name` attribute which indicates which bit of information it supplies. The 
  text contents of the `<info>` element contains the actual information.

<sourcecontrol>
"""""""""""""""

  If the `<sourcecontrol>` of a project is specified, it is used to infer the status of a project in development.
  For example, if you run ``reahl list -s`` a status is shown for each project listed. See ``reahl explainlegend``
  for more information.
  
  Currently only one type of source control system is supported: Bazaar. Use an attribute `type` set to the string 
  "bzr" to indicate that this project is maintained using Bazaar.

<distpackage>
"""""""""""""

  Use `<distpackage>` to indicate a package that should be built for distributing your project. Currently,
  only one package format is supported, a Python egg source tarball. To have your project packaged in this way, 
  set the `type` attribute to the string "sdist".
  
  To build your distribution packages as per the .reahlproject file, run ``reahl build``. Such packages
  are not yet uploaded.

<packageindex>
""""""""""""""

  Can be specified as child of a `<distpackage>` to indicate that the package should be uploaded to this
  repository. A `<packageindex>` represents a PyPi repository. It requires an attribute named `repository`
  which should be set to the URL of the repository (for example: http://pypi.python.org/pypi).
  
  A particular `<distpackage>` may be uploaded to several different repositories, each named in a 
  `<packageindex>` element.

<alias>
"""""""

  The `<alias>` element is used to define an alias for a command just for this project. The alias
  is for a command that the `reahl` script can perform, but it may include arguments. It is useful
  to, for example, declare ``reahl unit`` in different ways for different projects to run the
  unit tests of each project.
  
  This element requires a `name` attribute -- the name that will be used to invoke the alias. It
  also required a `command` attribute -- the full command that will be specified when invoked
  including all arguments.


