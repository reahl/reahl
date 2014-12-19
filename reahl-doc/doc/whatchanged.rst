.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
What changed in version 3.1
===========================


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

