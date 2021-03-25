.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Library| replace:: :class:`~reahl.web.libraries.Library`

Theming a multi-homed site
==========================

.. sidebar:: Examples in this section

   - howtos.bootstrapsassmultihomed

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>



A multi-homed example
---------------------

This example shows how to create a single site that is themed
differently depending on which hostname you use to access to it.

This example assumes you know the basics of creating a customised
theme as explained in :doc:`customisingcss`.

To prepare for this example, follow :doc:`the steps in <customisingcss>` to
configure `package.json` and install the node modules.


Create multiple themes and configure webpack to package them
------------------------------------------------------------

Create a webpack directory containing an `index.js` which includes the
bootstrap sources:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/webpack/index.js
    :language: js

For each of your sites, create a <site_name>.scss file in the
`webpack` directory with `customised SCSS sources
<https://getbootstrap.com/docs/4.5/getting-started/theming/>`_ for
that site:

sitea.com.scss:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/webpack/sitea.com.scss
    :language: scss

siteb.com.scss:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/webpack/siteb.com.scss
    :language: scss


List all your sites in `webpack.config.js`:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/webpack.config.js
    :language: js


     
Build your custom SCSS
----------------------

In your project root, run:

.. code-block:: bash

   npm run build


This command creates a `dist` directory which contains the packaged CSS for each of your site's domain names.


Configure your application to use your customisation
----------------------------------------------------

Create a |Library| which serves the correct CSS file depending on the current hostname in the request:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/bootstrapsassmultihomed.py
   :pyobject: CompiledBootstrap


Create configuration that includes all the necessary Reahl libraries
as well as your customised library, in the correct order:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/etc/web.config.py


Try it out!
-----------

Serving your multihomed project on http://localhost:8000 will not
match the theme for sitea.com or siteb.com. You have to visit
http://sitea.com:8000 or http://siteb.com:8000 for that to work.

However, sitea.com and siteb.com quite likely do not resolve to your
development machine.

In order to see the changes in a development environment on http://localhost:8000, you can
change `web.config.py` used in development to force your `CompiledBootstrap` to display a
specific theme by passing `force_theme`::

  CompiledBootstrap(force_theme='sitea.com')


.. note::

    If you are technically minded, you can also add aliases for your
    localhost to your local `hosts` file so that http://sitea.com:8000 or http://siteb.com:8000
    resolve to http://localhost:8000.
