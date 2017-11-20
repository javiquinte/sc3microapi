#!/usr/bin/env python3
#
# sc3microapi WS - prototype
#
# (c) 2017 Javier Quinteros, GEOFON team
# <javier@gfz-potsdam.de>
#
# ----------------------------------------------------------------------

"""sc3microapi WS - prototype

   :Platform:
       Linux
   :Copyright:
       GEOFON, GFZ Potsdam <geofon@gfz-potsdam.de>
   :License:
       GNU General Public License v3

.. moduleauthor:: Javier Quinteros <javier@gfz-potsdam.de>, GEOFON, GFZ Potsdam
"""

##################################################################
#
# First all the imports
#
##################################################################


import cherrypy
import os
import json
import MySQLdb

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class NetworksAPI(object):
    """Object dispatching methods related to networks."""

    def __init__(self, conn):
        """Constructor of the IngestAPI class."""
        self.conn = conn

    @cherrypy.expose
    def index(self):
        """List available networks in the system.

        :returns: Data related to the available networks.
        :rtype: utf-8 encoded string
        :raises: cherrypy.HTTPError
        """
        cherrypy.response.headers['Content-Type'] = 'application/json'
        try:
            self.cursor = self.conn.cursor()
            self.cursor.execute('select code, start, end, netClass, archive, restricted from network')
            return json.dumps(self.cursor.fetchall()).encode('utf-8')
        except:
            # Send Error 404
            messDict = {'code': 0,
                        'message': 'Could not read the list of available templates'}
            message = json.dumps(messDict)
            cherrypy.log(message, traceback=True)
            raise cherrypy.HTTPError(404, message)

        # Save the templates specification to be returned
        result = list()
        return json.dumps(result).encode('utf-8')


class SC3MicroApi(object):
    """Main class including the dispatcher."""

    def __init__(self, conn):
        """Constructor of the Provgen object."""
        config = configparser.RawConfigParser()
        here = os.path.dirname(__file__)
        config.read(os.path.join(here, 'sc3microapi.cfg'))

        # Save connection
        self.conn = conn
        self.network = NetworksAPI(conn)

    @cherrypy.expose
    def index(self):
        cherrypy.response.headers['Content-Type'] = 'text/html'

        # TODO Create an HTML page with a minimum documentation for a user
        try:
            with open('help.html') as fin:
                texthelp = fin.read()
        except:
            texthelp = """<html>
                            <head>sc3microapi</head>
                            <body>
                              Default help for the sc3microapi service (GEOFON).
                            </body>
                          </html>"""

        return texthelp

    @cherrypy.expose
    def version(self):
        """Return the version of this implementation.

        :returns: Version of the system
        :rtype: string
        """
        version = '0.1a1'
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return version


"""Establishing the connection to the DB."""
config = configparser.RawConfigParser()
here = os.path.dirname(__file__)
config.read(os.path.join(here, 'sc3microapi.cfg'))

# Read connection parameters
host = config.get('mysql', 'host')
user = config.get('mysql', 'user')
password = config.get('mysql', 'password')
db = config.get('mysql', 'db')

conn = MySQLdb.connect(host, user, password, db)

server_config = {
    'global': {
        'tools.proxy.on': True,
    	'server.socket_host': '127.0.0.1',
    	'server.socket_port': 7000,
    	'engine.autoreload_on': False
    }
}
# Update the global CherryPy configuration
cherrypy.config.update(server_config)
cherrypy.tree.mount(SC3MicroApi(conn), '/sc3microapi')

if __name__ == "__main__":
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()