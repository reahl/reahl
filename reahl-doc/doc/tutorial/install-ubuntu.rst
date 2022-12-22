.. Copyright 2014, 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Preparing for installation on Ubuntu
====================================

1. Python and basic development tools

   .. code-block:: bash

      sudo apt-get install python3-dev gcc cython3 python-virtualenv


2. Additional necessary packages for a Reahl installation


   .. code-block:: bash

      sudo apt-get install libxml2-dev libxslt-dev zlib1g-dev libsqlite3-0



   The next step is to :ref:`create a virtualenv <install-reahl-itself>`.


3. Geckodriver and Firefox (optional)

   If you want to run your own automated selenium tests, install Firefox 
   and geckodriver(firefox-geckodriver: https://github.com/mozilla/geckodriver/releases ) as well.

   .. code-block:: bash

      sudo apt-get install firefox

