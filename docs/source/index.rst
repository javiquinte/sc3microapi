.. sc3microapi documentation master file, created by
   sphinx-quickstart on Mon Jul  3 10:39:39 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to sc3microapi's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Installation
============

The code is hosted in the following repository: https://git.gfz-potsdam.de/javiquinte/sc3microapi.git

To get the code and deploy it you can execute the following commands: ::

  git clone https://git.gfz-potsdam.de/javiquinte/sc3microapi.git
  cd sc3microapi
  cp sc3microapi.cfg.sample sc3microapi.cfg

In order to run `sc3microapi` you will need a recent version of python3 and the cherrypy package.
The latter can be easily installed with pip. ::

  pip3 cherrypy

Using Apache to proxy the requests
==================================

blah, blah...

Starting the service
====================

Once the application has been deployed it can be started by means of the following command: ::

  cherryd -d -i sc3microapi

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
