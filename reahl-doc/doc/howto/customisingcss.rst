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

You can of course also add your own CSS on top of that too.

Once you have compiled your customised theme, you need to package the
resultant CSS and JavaScript and make it part of your site.

For packaging, we use `npm <https://www.npmjs.com/>`_ and `webpack
<https://webpack.js.org/>`_, both of which need the `nodeJS
<https://nodejs.org/>`_ interpreter installed on your development
environment.

In order to make the packaged CSS and JavaScript part of your site,
you create a custom |Library| (see also :ref:`shipping_js_css`).


Install JavaScript and CSS build tools for you project
------------------------------------------------------

Install nodeJS (it includes npm):

.. code: bash

   sudo snap install --classic node

.. note::
   If you know docker and want to use node in a docker container instead, do:
          
   .. code: bash

      alias npm='docker run --rm  -v ${PWD}:/app -w /app node:15.7.0 npm'


Install bootstrap sources and packaging tools in your project:

.. code: bash

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

Define your theme by `setting bootstrap variables
<https://getbootstrap.com/docs/4.5/getting-started/theming/>`_ (or
custom CSS) in `theme.scss` in the webpack directory:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsass/webpack/theme.scss


Create a file `webpack.config.js` to instruct webpack to package your theme sources:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsass/webpack.config.js

Edit `package.json` to make npm aware of webpack:

- Add, at the top level:

  .. code:: json

     "main": "webpack.config.js",  

- Under "scripts", before "test", add:

  .. code:: json

    "build": "webpack",

     
Build your custom SCSS
----------------------

Still in your project root, run:

.. code:: bash

   npm run build


This command creates a ./dist directory with the packaged CSS and
JavaScript files needed by your site.


Configure your application to use your customisation
----------------------------------------------------

Create a |Library| for the files created in `./dist` as part of your source code:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsass/bootstrapsass.py
   :pyobject: CompiledBootstrap


Create configuration that includes all the necessary Reahl libraries
as well as your customised library, in the correct order:

.. literalinclude:: ../../reahl/doc/examples/howtos/bootstrapsass/etc/web.config.py


Congratulations!
----------------

You should now be able to serve your application as usual, but with a
custom theme.
