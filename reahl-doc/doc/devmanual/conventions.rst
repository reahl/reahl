.. Copyright 2017 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Coding and design conventions
=============================

This is what we do to keep the Reahl project consistent,
understandable and organised.

Coding style
------------

We follow `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ with
some slight exceptions and additions.

Deviations to PEP8
~~~~~~~~~~~~~~~~~~

We use max line length of 120 instead of the 79 in PEP8.

Imports
~~~~~~~

Imports are grouped into paragraphs, and these paragraphs are in a
particular order: first are the "from future" import and six. Second
are imports of the standard library (possibly via six). This is
followed by imports of third party packages and finally a paragraph
with imports of our own modules.

String quotes
~~~~~~~~~~~~~

We use single quotes consistently for Python strings, so that we can
easily write html-level quotes inside them using double quotes.

Design values and principles
----------------------------

We adhere to object oriented design principles. Understanding these is
a life-long journey, but for the record we use the following as
guidelines:

- `Object-oriented Methods: a Foundation <https://books.google.co.za/books/about/Object_oriented_Methods.html?id=JotQAAAAMAAJ/>`_
- `Refactoring: Improving the Design of Existing Code <https://books.google.co.za/books?id=HmrDHwgkbPsC/>`_

We do not believe that generic slogans and rules can absolutely
dictate design: real understanding of an actual situation and
necessary trade-offs is needed. That said, we're 'fond of' the
following values:

Naming things
~~~~~~~~~~~~~
- Class names mean something, are usually nouns, never things like BaseXXX or HelperXXX or UtilityXXX.
- Method names mean something, are verbs and their arguments must make sense in terms of the method name.

On the use of inheritance
~~~~~~~~~~~~~~~~~~~~~~~~~
- We do not use multiple inheritance or mixins.
- Wherever possible we prefer composition over inheritance.
- If a class inherits from another, it must *conceptually be* a <whatever its superclass it called>.
- If you override a method, it should generalise or specialise the one it overrides.

About optimisation
~~~~~~~~~~~~~~~~~~
- Optimise for design clarity first, optimise for speed and memory when needed, but *profile* first.

Some acronyms we also ascribe to
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- YAGNI
- KISS
- DRY
   
Important design invariants
---------------------------

Things that are always done a certain way make designs easier. Here are some that we have adopted:

Special method names and behaviour
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Methods named `add_*` will always return the thing that was
  added. For example :meth:`~reahl.web.fw.Widget.add_child` always
  returns the child passed in. This makes it possible to write concise
  code such as::

     paragraph = Div(view).add_child(P(text='some text in a paragraph'))

- Methods named `define_*` create something based on whatever arguments
  they take, possibly do some housekeeping of the created instance, and
  then return the created instance. See: :meth:`~reahl.web.fw.UserInterface.define_view`.
     
- Methods named `with_*` / `without_*` will always return a copy of
  the object that differs only as specified by the with/without
  method. For example :meth:`~reahl.web.fw.Bookmark.with_description`
  or
  :meth:`~reahl.web.bootstrap.grid.ColumnLayout.with_justified_content`.
   
- Methods named `as_*` mostly return something else representing the
  instance. For example
  :meth:`~reahl.component.modelinterface.Field.as_input`
  :meth:`~reahl.web.fw.ViewFactory.as_bookmark`. In some rare cases,
  `as_*` methods are also used like the `with_*` methods because they
  just read better, for example:
  :meth:`~reahl.web.fw.Url.as_locale_relative` or
  :meth:`~reahl.component.modelinterface.Field.as_required`.
   
- Keyword arguments with defaults that should not be globally shared
  are given as None. They are then set inside the method to the
  actual default. For example::

     def do_something(a_dict=None):
         a_dict = a_dict or {}
         # or, alternatively
         do_something_else(a_dict or {})


The context
~~~~~~~~~~~

Often, you need access to something from many places in code. Examples
of this is: the configuration of the system, the current database
transaction or the current web request.

Our solution is to accept that code executes within a current
ExecutionContext which contains some important global-ish elements.

The ExecutionContext is not supposed to be extended. It contains a few
very specific things that get set up by the framework:

- The configuration of the system;
- Ways to manage databases, persistence and database transactions;
- The current user session; and
- The current web request.

The idea of such a global context is criticised because it can make
testing difficult: you may want to test code that is dependent on such
a magic context. We mitigate this problem in the following way:

- context is stack-based
- ContextAwareFixture ensures all tests always have a context and that setup/teardown/singleton methods happen inside the right context
- We have a Context within which all tests and the participating web server runs
- We have a Context (a copy) within which each test runs, but which does not carry over side-effects

If you understand above mentioned context stuff, you can pretty much live in testing world without much bother.


Testing
-------

We write tests that:

- Serve as a summary of how we understand our problem domain.
- Each test has a docstring stating that summary in words.
- The test itself may elaborate more details or show that summary in code.
- We do not aim for complete coverage of code execution paths, but good enough coverage of problem domain understanding.
- We organise tests into a hierarchy of directories resembling an outline of the topics covered by the component the tests are for.
- We do not necessarily write tests first; but we always write them before we're done and make sure they fit into the above.

In order to be able to write tests the way we want to, we have
developed a supporting testing infrastructure with an accompanying set
of Fixtures.



