.. Copyright 2020 Reahl Software Services (Pty) Ltd. All rights reserved.
 
Developing using Reahl in Docker
================================

Reahl provides a `Docker <https://www.docker.com>`_ image with Reahl itself 
pre-installed as well as the necessary tools ready to go.

Put the following docker-compose.yaml file in your development directory:

.. literalinclude:: ../../../docker-compose.yaml


Then do:

.. code-block:: bash

   docker-compose up

For detailed instructions on how to use this container, see: :doc:`../devmanual/devenv`.


