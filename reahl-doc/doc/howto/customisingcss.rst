.. Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.

.. |Library| replace:: :class:`~reahl.web.libraries.Library`

Customising CSS using SASS
==========================

.. sidebar:: Examples in this section

   - howtos.bootstrapsass

   Get a copy of an example by running:

   .. code-block:: bash

      reahl example <examplename>



The web packaging ecosystem
---------------------------

Reahl styling is implemented using `Bootstrap
<https://getbootstrap.com/>`_\. In order to customise your styling,
you need to compile Bootstrap sources using `SASS
<https://sass-lang.com/guide>`_ after changing `its input variables
<https://getbootstrap.com/docs/4.5/getting-started/theming/>`_ to suit
your needs.

You can of course also add your own CSS(see :ref:`your_own_css`) on top of that too.

Once you have compiled your customised theme, you need to package the
resultant CSS and JavaScript and make it part of your site.

For packaging, use `npm <https://www.npmjs.com/>`_ and `webpack
<https://webpack.js.org/>`_, both of which need the `Node.js
<https://nodejs.org/>`_ runtime installed in your development
environment.

In order to make the packaged CSS and JavaScript part of your site,
you create a custom |Library| (see also :ref:`shipping_js_css`).


Install JavaScript and CSS build tools for your project
-------------------------------------------------------
   
`Install Node.js <https://nodejs.org/en/download/>`_  and npm:

.. code-block:: bash

   sudo apt-get install nodejs npm

.. note::

   If you know docker, you might prefer using it for executing Node.js
   commands instead of installing Node.js. If you do this, execution
   of the `npm` commands are done on your main machine even if
   you are using :doc:`the Reahl docker development container
   <../devmanual/devenv>` for development, from the root of your
   source code.

   To use docker, on your main machine, do:
          
   .. code-block:: bash

      alias npm='docker run --rm  -v ${PWD}:/app -w /app node:15.7.0 npm'

      
Install bootstrap sources and packaging tools in your project:

.. code-block:: bash

   cd bootstrapsass
   npm init -y
   npm install bootstrap@4.5.2 --save
   npm install autoprefixer css-loader mini-css-extract-plugin sass postcss-loader sass-loader style-loader webpack webpack-cli --save-dev


This creates `package.json` and `package-lock.json` files in the root
of your project which state what packages your project needs. It also
downloads and installs all these dependencies in the directory
`node_modules`.

Configure webpack
-----------------

Create a webpack directory containing an `index.js` which includes the
bootstrap sources:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsass/webpack/index.js
    :language: js


Define your theme by `setting bootstrap variables
<https://getbootstrap.com/docs/4.5/getting-started/theming/>`_ (or
custom CSS) in `theme.scss` in the webpack directory:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsass/webpack/theme.scss
    :language: scss


Create a file `webpack.config.js` to instruct webpack to package your theme sources:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsass/webpack.config.js
    :language: js

Edit `package.json` to make npm aware of webpack:

- Add, at the top level:

  .. code-block:: json-object

     "main": "webpack.config.js",  

- Under "scripts", before "test", add:

  .. code-block:: json-object

    "build": "webpack",

     
Build your custom SCSS
----------------------

Still in your project root, run:

.. code-block:: bash

   npm run build


This command creates a `dist` directory which contains the packaged CSS and
JavaScript files needed by your site.


Configure your application to use your customisation
----------------------------------------------------

Create a |Library| for the files created in `dist` as part of your source code:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsass/bootstrapsass.py
   :pyobject: CompiledBootstrap


Create configuration that includes all the necessary Reahl libraries
as well as your customised library, in the correct order:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsass/etc/web.config.py


Congratulations!
----------------

You should now be able to serve your application as usual, but with a
custom theme.
