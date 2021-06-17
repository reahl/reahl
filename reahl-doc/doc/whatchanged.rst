.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.




What changed in version 5.1
===========================

.. |PrimitiveInput| replace:: :class:`~reahl.web.ui.PrimitiveInput`
.. |type| replace:: :meth:`~reahl.browsertools.browsertools.DriverBrowser.type`
.. _AGPL: http://www.gnu.org/licenses/agpl-3.0.html
.. _LGPL: http://www.gnu.org/licenses/lgpl-3.0.html



Upgrading
---------

To upgrade a production system, install the new system in a
new virtualenv, then migrate your database:

.. code-block:: bash

   reahl migratedb etc
   

Split out projects
------------------

The main focus of this release of Reahl is that we rearranged documentation to highlight the companion components
that could be used without the Reahl web framework. We have also split out a new project (reahl-browsertools) so it
also can easily be used without installing the rest of the Reahl components or reahl-web.

:doc:`reahl-component <component/introduction>`
  The Reahl component framework was always an independent component, but the documentation has been rewritten to make
  sure it is explained in its own right.

:doc:`reahl-browsertools <browsertools/introduction>`
  Web testing tools used in the development of Reahl is now split out into its own component so that it can be used
  when developing applications using any web framework.

:doc:`reahl-tofu <tofu/introduction>`
  Tofu provides class based Fixtures used in tests. Documentation of Tofu has been rearranged to be consistent with
  our other projects.

:doc:`reahl-stubble <stubble/introduction>`
  Stubble helps you write stub classes that cannot mask changes to the classes they stand in for. Documentation
  of Stubble has been rearranged to be consistent with the other projects.


Licensing changes
-----------------

Since its inception all parts of Reahl have been licensed using the AGPL_. At the time, we felt that a strict license
is a good idea for a project that still needs to mature. The time has now come to selectively ease up on the license.

The licensing of supporting components for development have been changed from AGPL_ to LGPL_. These components
(reahl-stubble, reahl-tofu and the newly split out reahl-browsertools) are meant to be used in development only,
so the more restrictive license did not make sense for them.

A lot of unique functionality is contained in reahl-component. We have decided to change its license
to LGPL_ in order to make it easier for others to use in their environment.

The rest of the components (reahl-web and related components) are still AGPL_ licensed.

Your code that imports our code that is LGPL_ licensed, does not need to be licensed using a copyleft license.
If the public can access your web application which uses our AGPL_ code, then your code also needs to use a compatible
license.

If you want to use any part of Reahl without the restrictions of these licenses, we are quite open to
negotiate exceptions to the relevant licenses with individual clients. We fund the development of Reahl using such
agreements.

HOWTOs
------

Some HOWTO examples were added:

howtos.bootstrapsass
   How to change your styling using a custom compile of bootstrap's SASS sources.
howtos.bootstrapsassmultihomed
   Run one site accessed by many customers, with each customer having its own domain name and the site styled
   differently depending on the domain.
howtos.hellodockernginx
   How to host your web application in a docker container.

The howtos.helloapache example was removed.


Support for Python 3.5
----------------------

This version drops support for Python 3.5 which has reached its end-of-life and stopped receiving security updates in 2020.
   

Updated dependencies
--------------------

Some included thirdparty JavaScript and CSS libraries were updated:

- Bootstrap to 4.5.3
- JQuery.validate was updated to 1.19.3 (and patched).
- JQuery.form to 4.3.0
- Popper to 1.16.1
- holder to 2.9.9
- underscore 1.13.1 (fixes CVE-2021-23358)
