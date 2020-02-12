# sc3microapi

![](https://img.shields.io/pypi/v/sc3microapi.svg) ![](https://img.shields.io/pypi/pyversions/sc3microapi.svg) ![](https://img.shields.io/pypi/format/sc3microapi.svg) ![](https://img.shields.io/pypi/status/sc3microapi.svg)

Micro web service for SeisComP3 systems

Overview
--------

In order to integrate systems running SeisComP3 with other systems or tools
is important to expose at least some basic information related to the system
in operation. For instance, which networks and stations are present in the
inventory with some attributes that are not visible through the FDSN Station-WS.

Some other internal data, like access control lists, are important for other
systems providing data. Thus, the permissions can be managed in SC3 and used in
many other places, offering the operator a single management point.

API Specification
-----------------

Full OpenAPI specification can be seen [here](https://generator.swagger.io/?url=https://raw.githubusercontent.com/javiquinte/sc3microapi/master/swagger.yaml).
