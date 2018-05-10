.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Preparing for installation on Ubuntu
====================================

1. Python and basic development tools

   .. code-block:: bash

      sudo apt-get install python3-dev gcc cython python-virtualenv


2. Additional necessary packages for a Reahl installation


   .. code-block:: bash

      sudo apt-get install libxml2-dev libxslt-dev zlib1g-dev libsqlite3-0



   The next step is to :ref:`create a virtualenv <install-reahl-itself>`.


3. Chromedriver (optional)

   You do not need to install chromedriver in order to follow this
   tutorial. However, if you are going to use chromium for testing, you
   will need chromedriver.

   .. code-block:: bash

      sudo apt-get install chromium-chromedriver

   You also need to adjust your PATH so that /usr/lib/chromium-browser is
   included. In your .bashrc, add the line:

   .. code-block:: bash

      export PATH=$PATH:/usr/lib/chromium-browser

   .. note::

       In Ubuntu 14.4, the chromedriver binary is installed in
       `/usr/lib/chromium-browser/chromedriver`, but it neglects setting
       the LD_LIBRARY_PATH for it to work correctly. To correct this,
       create the file `/etc/ld.so.conf.d/chrome_lib.conf`, with the
       following contents:

       .. code-block:: bash

          /usr/lib/chromium-browser/libs

       Finally, run:

       .. code-block:: bash

          sudo ldconfig

