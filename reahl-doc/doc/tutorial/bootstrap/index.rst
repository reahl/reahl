.. Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.

Layout and styling using Bootstrap (experimental)
=================================================

.. sidebar:: Behind the scenes

   Reahl uses the `Bootstrap 4 framework <http://getbootstrap.com/>`_ to deal
   with layout and styling issues.


In this version of Reahl, we introduce Widgets and Layouts that are
based on `Bootstrap <http://getbootstrap.com/>`_\.

At the time of release of Reahl 3.2, Bootstrap version 4 was still in
alpha and under heavy development. For this reason, the bootstrap
support here is *not* enabled by default and is seen as experimental.

In Reahl 4.0, these Bootstrap versions of Widgets and Layouts will
become the only out-of-the-box styled Widgets supported -- our current
home-grown styled Widgets will disappear.

The experimental support for Bootstrap 4 is included here so that we
can gain experience with these ideas so long, and so that you can
start using them to see how they work.

The version of Bootstrap included in this version is a vanilla version
of Bootstrap 4 alpha. There is no supported way to change Bootstrap
variables and recompile using Sass. That will change in future. There
are ways around this limitation if you know what you're doing. Please
`talk to us on the mailing list
<https://groups.google.com/forum/?#!forum/reahl-discuss>`_ if you want
to push past this boundary.


Details:

.. toctree::
   :maxdepth: 1

   enabling
   forms   
   pagelayout
   differences


