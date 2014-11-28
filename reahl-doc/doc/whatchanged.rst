.. Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
 
What changed in version 3.1
===========================


LoginSession and related dependencies
-------------------------------------

The Reahl web framework (reahl-web) is dependent on a small number
of classes that are implemented using a specific persistence
technology. The reahl-web-declarative component is such an
implementation which is done using SqlAlchemy's declarative syntax.

These classes are kept separate in order to minimize the work needed
to use the framework in conjunction with a different persistence
technology.  Previously one of these classes, the UserSession,
contained logic regarding the logging in of users etc. This
functionality in turn was dependent on a whole host of other code in
reahl-domain, defeating the purpose of keeping the implementation
separate: To provide the implementation of the framework on a
different technology, one had to implement a large body of
functionality.

For this reason, functionality pertaining to logging users into the
system was split our into its own class, LoginSession. As a result, 
UserSession is no longer dependent on reahl-domain, and the
reahl-web-declarative implementation as a whole is no longer dependent
on all the functionality of reahl-domain.

Some repercussions:

  - This change impacts the interface one needs to provide in order to
    provide an implementation of the framework using a different
    persistence technology. As a result, this version of Reahl cannot
    be used with the older Elixir implementation anymore.

  - :class:`reahl.domain.systemaccountmodel.LoginSession` is
    introduced, which keeps track of who is currently logged on.

  - The following methods on UserSession have changed:

      - UserSession.is_secured() was added. It answers whether the user is communicationg 
        via secure channel without considering whether a user is logged in or not.

      - UserSession.is_logged_in() was moved to LoginSession. A version of UserSession.is_logged_in() 
        was left on UserSession, but deprecated in order to maintain backwards compatibility 
        for the 3.x series.

      - The functionality provided by UserSession.is_secure() was moved to LoginSession.is_logged_in(secured=True).
        Ie.: with secured=True, is_logged_in checks whether the user is logged in *while* connected
        via secure channel. A version of UserSession.is_secure() was left on UserSession, 
        but deprecated in order to maintain backwards compatibility for the 3.x series.




Other changed dependencies
--------------------------

The reahl-tofu component used to be dependent on reahl-component on
nose. These dependencies were unnecessary and forced someone who only
wanted to install reahl-tofu to also install reahl-component and
nose. These dependencies have been removed.
