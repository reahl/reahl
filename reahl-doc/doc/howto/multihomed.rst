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
theme as explained in :doc:`bootstrapsass`.


Create multiple themes and configure webpack to package them
------------------------------------------------------------

Create a webpack directory containing an `index.js` which includes the
bootstrap sources:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/webpack/index.js

For each of your sites, create a <site_name>.scss file in the
`webpack` directory with `customised SCSS sources
<https://getbootstrap.com/docs/4.5/getting-started/theming/>`_ for
that site:

sitea.com.scss:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/webpack/sitea.com.scss

siteb.com.scss:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/webpack/siteb.com.scss


List all your sites in `webpack.config.js`:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/webpack.config.js


     
Build your custom SCSS
----------------------

In your project root, run:

.. code:: bash

   npm run build


This command creates a ./dist directory with the packaged CSS for each of your site's domain names.


Configure your application to use your customisation
----------------------------------------------------

Create a |Library| which serves the correct CSS file depending on the current hostname in the request:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/bootstrapsassmultihomed.py
   :pyobject: CompiledBootstrap


Create configuration that includes all the necessary Reahl libraries
as well as your customised library, in the correct order:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsassmultihomed/etc/web.config.py


Congratulations!
----------------

To be able to see the different themes in a development environment,
you will have to visit the application using the actual domain names.

Visiting http://localhost:8000 will not match sitea.com or siteb.com.

In Ubuntu you can simulate this by adding names to /etc/hosts:

.. code:: bash

   sudo bash -c "echo '127.0.1.1 sitea.com siteb.com' >> /etc/hosts"





