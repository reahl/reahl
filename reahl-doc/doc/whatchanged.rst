.. Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
 
What changed in version 3.1
===========================

Improved support for layout
---------------------------

The main feature of this release is changes related to dealing more efficiently with 
layout of Widgets.

Using Pure instead of Yui
~~~~~~~~~~~~~~~~~~~~~~~~~

The Yui 2 CSS grids project has quite a while ago been succeeded by
Yui3, and more recently Yui3 has been succeeded by the Pure CSS
library. In this release of Reahl, we switched to using Pure CSS
instead.

Backwards compatibility (for Widgets dependend on Yui2) is maintained, but not the default.
Using Yui2 and thus Widgets depending on it, requires the following line of code to be
added in your `reahl.web.config.py` file:

.. code-block:: python

   web.frontend_libraries.use_deprecated_yui()

Yui2 and Pure cannot be used concurrently in the same project, and the
default library used is Pure.

Several Widgets are deprecated for this reason because their
functionality is now provided in a slightly different way (see the
next section), via :mod:`reahl.web.pure`::

 - :class:`reahl.web.ui.YuiDoc`
 - :class:`reahl.web.ui.YuiGrid`
 - :class:`reahl.web.ui.YuiBlock`
 - :class:`reahl.web.ui.YuiUnit`
 - :class:`reahl.web.ui.TwoColumnPage`:

Switching over to Pure also changed the look of a site slightly. This
change has to do with Pure's reliance on Modernize.js which only
selectively clears styling of elements instead of Yui2's approach of
clearing all styling from elements. 

A new Layout concept
~~~~~~~~~~~~~~~~~~~~

A simple, yet powerful new concept was introduced to help deal with
the issue of layout. This makes it possible for us to wrap the
functionality of advanced layout engines in Python in future.

Any :class:`reahl.web.fw.Widget` can now optionally use a :class:`reahl.web.fw.Layout`. 

The Layout is attached to its Widget immediately after the Widget is
constructed, by means of the :meth:`reahl.web.fw.Widget.use_layout` method.

For example:

.. code-block:: python

   menu = Menu.from_bookmarks(view, bookmarks).use_layout(HorizontalLayout())

The Layout is responsible for changing the Widget in subtle ways (such
as adding CSS classes to it which would make it render in a particular
way.  The Layout can also add children Widgets to its Widget, either
just after construction of the Widget, or by special methods a
programmer can call on a Widget.

For example:

It is possible to build, say a StackedFormLayout which allows a
programmer to add inputs that stack on top of one another inside any
Form using this Layout. Here is how that would look:

.. code-block:: python

   form = Form(view).use_layout(StackedFormLayout())
   form.layout.add_stacked(TextInput(view, address.fields.name))


The concept of a Layout has made the following classes unnecessary, and thus deprecated:

 - :class:`reahl.web.ui.TwoColumnPage`:

   This class was nothing more than an :class:`reahl.web.ui.HTML5Page`
   to which certain children were added with CSS that made it display
   in columns. The much more powerful
   :class:`reahl.web.pure.PageColumnLayout` was added which can be
   applied to an
   :class:`reahl.web.ui.HTML5Page`. :class:`reahl.web.pure.PageColumnLayout`
   is more flexible than :class:`reahl.web.ui.TwoColumnPage`, allowing
   you more control over the number of columns.

 - :class:`reahl.web.ui.HMenu` and :class:`reahl.web.ui.VMenu`:

   These classes were made obsolete by the new
   :class:`reahl.web.ui.HorizontalLayout` and
   :class:`reahl.web.ui.VerticalLayout` classes that can be applied to
   any :class:`reahl.web.ui.Menu` or one of its subclasses.



LoginSession and related dependencies
-------------------------------------

The Reahl web framework (reahl-web) is dependent on a small number
of classes that are implemented using a specific persistence
technology. The reahl-web-declarative component contains our current
implementation of these -- done using SqlAlchemy's declarative layer.

These classes are kept separate in order to minimize the work needed
to use the framework in conjunction with a different persistence
technology.  Previously one of these classes, the UserSession,
contained functionality regarding the logging in of users, and keeping track
of who is logged in. This functionality in turn was dependent on a
whole host of other code in reahl-domain, defeating the purpose of
keeping the implementation separate: to provide the implementation of
the framework on a different technology, one had to implement a large
body of code.

For this reason, functionality pertaining to logging users into the
system is now split out into its own class, :class:`reahl.domain.systemaccountmodel.LoginSession`. 
LoginSession is part of reahl-domain, meaning it is part of extra niceties
that are not needed for the core framework to work. As a result, 
UserSession is no longer dependent on reahl-domain, and the
reahl-web-declarative implementation as a whole is no longer dependent
on the functionality of reahl-domain.

Some repercussions:

  - This change impacts the interface one needs to provide in order to
    provide an implementation of the framework using a different
    persistence technology (now only reahl.web.interfaces). As a result, 
    this version of Reahl cannot be used with the older
    Elixir implementation anymore. The Elixir implementation implements
    the older interface.

  - :class:`reahl.domain.systemaccountmodel.LoginSession` is
    introduced, which keeps track of who is currently logged on, but does
    not form part of the core web framework any longer.

  - The following methods on :class:`reahl.web.interfaces.UserSessionProtocol` have changed:

      - :meth:`reahl.web.interfaces.UserSessionProtocol.is_secured` was added. It answers whether the user is communicationg 
        via secure channel without considering whether a user is logged in or not.

      - UserSessionProtocol.is_logged_in() was moved to
        :class:`reahl.domain.systemaccountmodel.LoginSession`.  A
        version of UserSession.is_logged_in() was left on UserSession,
        but deprecated in order to maintain backwards compatibility
        for the 3.x series.

      - The functionality previously provided by
        UserSession.is_secure() was moved to
        :meth:`reahl.domain.systemaccountmodel.LoginSession.is_logged_in`,
        when used with secured=True.  With secured=True, is_logged_in
        checks whether the user is logged in *while* connected via
        secure channel. A version of UserSession.is_secure() was left
        on UserSession, but deprecated in order to maintain backwards
        compatibility for the 3.x series.


Wheels
------

We now build and distribute packages using Python Wheels instead of a source 
distribution. While Reahl packages at present are all pure Python packages, many
of the projects that Reahl depends on need compiling. Using wheels sets us on the
path to easier installation of these packages once they provide wheels too.


Other changed dependencies
--------------------------

The reahl-tofu component used to be dependent on reahl-component on
nose. These dependencies were unnecessary and forced someone who only
wanted to install reahl-tofu to also install reahl-component and
nose. These dependencies have been removed.



Development infrastructure
--------------------------

Several internal changes were made internally, and so some development infrastructure
to be able to use tools such as devpi and tox, which were not available when we started 
out. These resulted in a number of small changes that are visible to users:

  - The `reahl upload` command has two new options:
    `--ignore-release-checks` and `--ignore-upload-check`. The
    `--ignore-release-checks` option allows one to upload a package
    even if some release check (such as it not being committed) fails.
    The `--ignore-upload-check` allows an upload even when the package has
    already been uploaded previously.

    These switches make it possible to upload packages repeatedly to a devpi
    staging server before an actual release.

  - The `reahl upload` command now also does a register before it uploads to a pypi-like
    repository, so that a separate register step is not necessary anymore.

  - The `reahl shell` command gained the `--generate-setup-py` option. The `setup.py`
    file of a Reahl project is generated from its `.reahlproject` file. Sometimes
    one needs to execute a command (tox is an example) which is dependent on the
    `setup.py`. This switch allows execution via `reahl shell`. For example, the
    following command generates an up-to-date `setup.py`, runs tox, and then removes
    the generated `setup.py` again:

    .. code-block:: bash

       reahl shell --generate-setup-py -- tox

  - Two commands were added to the `reahl` script: `devpitest` and `devpipush`. These run
    `devpi test` and `devpi push` on the current project, respectively, but with suitable
    arguments for the exact version of the current project. The `devpi test` command, for 
    example, needs to be passed an spec, such as: `reahl-doc==3.1.0` to test the exact version
    that is under development. We need to be able to run such a command for all components
    making up Reahl, each with a different spec. This is now possible via, for example:

    .. code-block:: bash

       reahl devpitest -sX

    or:

    .. code-block:: bash

       reahl devpipush -sX -- pypi:pypi

  - In order to use nosetests in a more natural way (from a nose perspective), we have
    added two features to reahl.tofu.nosesupport:

    - We like to do tests slightly differently to how they are done
      generally: we put all tests in a single directory and we do not
      want to use naming conventions for test discovery. The :class:`reahl.tofu.nosesupport.MarkedTestsPlugin` 
      (`--with-marked-tests`) allows this. It changes nose test discovery
      to apply the naming conventions to *files only*, and inside those files
      it only sees something as a test if it has been marked with the @istest, or 
      tofu's @test() decorators.

      `--with-marked-tests` plays well with other nose plugins, and supercedes the 
      older `--with-test-directory` which does not play well with other nose plugins.

    - Using a run fixture per project (via the `--with-run-fixture`
      plugin) is not very "nose". The "nose" way of doing things is to
      have a setup and teardown methods in, say the `__init__.py` of
      the package where such batch setup should apply.

      The function :func:`reahl.tofu.nosesupport.set_run_fixture`
      was added to deal with this situation. It can be called in an
      `__init__.py` to add setup and teardown methods there as nose
      expects.  The effect of this is to make the run fixture apply
      for the duration of tests in that package.

