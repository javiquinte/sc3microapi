.. sc3microapi documentation master file, created by
   sphinx-quickstart on Mon Jul  3 10:39:39 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Sc3microapi's documentation!
============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Installation
============

The code is hosted in the following repository: https://github.com/javiquinte/sc3microapi.git

Requirements
------------
Some libraries external to the python environment are needed for this to work. For instance,
the MySQL client libraries. If you are installing this on an Ubuntu distribution, just run ::

   $ apt install python3-dev default-libmysqlclient-dev build-essential

If you want to deploy it in a Mac ::

   $ # Assume you are activating Python 3 venv
   $ brew install mysql-client pkg-config
   $ export PKG_CONFIG_PATH="$(brew --prefix)/opt/mysql-client/lib/pkgconfig"

Recommended installation (Pypi)
-------------------------------

The easiest way to install sc3microapi is through pip. ::

  $ pip sc3microapi

That was easy! :-)

Installing from the sources
---------------------------

To get the code and install it you have to execute the following commands: ::

  git clone https://github.com/javiquinte/sc3microapi.git
  cd sc3microapi
  cp sc3microapi.cfg.sample sc3microapi.cfg

Using Apache to proxy the requests
==================================

blah, blah...

Starting the service
====================

Once the application has been deployed it can be started by means of the following command: ::

  $ python -m uvicorn sc3microapi:app --reload

