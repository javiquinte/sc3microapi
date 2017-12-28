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
import io
import csv
import json
import MySQLdb
import logging
import datetime

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

@cherrypy.expose
@cherrypy.popargs('net')
class NetworksAPI(object):
    """Object dispatching methods related to networks."""

    def __init__(self, conn):
        """Constructor of the IngestAPI class."""
        self.conn = conn

    @cherrypy.expose
    def index(self, net=None, format=json, restricted=None):
        """List available networks in the system.

        :param net: Network code
        :param type: str
        :returns: Data related to the available networks.
        :rtype: utf-8 encoded string
        :raises: cherrypy.HTTPError
        """
        cherrypy.response.headers['Content-Type'] = 'application/json'

        # Check parameters
        if restricted is not None:
            try:
                restricted = int(restricted)
                if restricted not in [0, 1]:
                    raise Exception
            except:
                # Send Error 400
                messDict = {'code': 0,
                            'message': 'Restricted does not seem to be 0 or 1.'}
                message = json.dumps(messDict)
                cherrypy.log(message, traceback=True)
                raise cherrypy.HTTPError(400, message)

        try:
            if format not in ['json', 'text']:
                raise Exception
        except:
            # Send Error 400
            messDict = {'code': 0,
                        'message': 'Wrong value in the "format" parameter.'}
            message = json.dumps(messDict)
            cherrypy.log(message, traceback=True)
            raise cherrypy.HTTPError(400, message)

        try:
            self.cursor = self.conn.cursor()
            query = 'select code, start, end, netClass, archive, restricted from Network'

            whereClause = []
            if net is not None:
                whereClause.append('code="%s"' % net)

            if restricted is not None:
                whereClause.append('restricted=%d' % restricted)

            if len(whereClause):
                query = query + ' where ' + ' and '.join(whereClause)

            self.cursor.execute(query)

            if format == 'json':
                return json.dumps(self.cursor.fetchall(), default=datetime.datetime.isoformat).encode('utf-8')
            elif format == 'text':
                fout = io.StringIO("")
                writer = csv.writer(fout, delimiter='|')
                writer.writerows(self.cursor.fetchall())
                fout.seek(0)
                return fout.read().encode('utf-8')
        except:
            # Send Error 404
            messDict = {'code': 0,
                        'message': 'Could not query the available networks'}
            message = json.dumps(messDict)
            cherrypy.log(message, traceback=True)
            raise cherrypy.HTTPError(404, message)


class SC3MicroApi(object):
    """Main class including the dispatcher."""

    def __init__(self, conn):
        """Constructor of the SC3MicroApi object."""
        # config = configparser.RawConfigParser()
        # here = os.path.dirname(__file__)
        # config.read(os.path.join(here, 'sc3microapi.cfg'))

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

        return texthelp.encode('utf-8')

    @cherrypy.expose
    def version(self):
        """Return the version of this implementation.

        :returns: Version of the system
        :rtype: string
        """
        version = '0.1a1'
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return version.encode('utf-8')


def main():
    """Establishing the connection to the DB."""
    config = configparser.RawConfigParser()
    here = os.path.dirname(__file__)
    config.read(os.path.join(here, 'sc3microapi.cfg'))
    
    # Logging configuration
    verbo = config.get('Logging', 'verbose') if config.has_option('Logging', 'verbose') else 'INFO'
    verboNum = getattr(logging, verbo.upper(), 30)
    logging.basicConfig(level=verboNum)

    # Read connection parameters
    host = config.get('mysql', 'host')
    user = config.get('mysql', 'user')
    password = config.get('mysql', 'password')
    db = config.get('mysql', 'db')
    
    conn = MySQLdb.connect(host, user, password, db)
    
    server_config = {
        'global': {
            'tools.proxy.on': True,
            'server.socket_host': 'st27dmz.gfz-potsdam.de',
            'server.socket_port': 7000,
            'engine.autoreload_on': False
        }
    }
    # Update the global CherryPy configuration
    cherrypy.config.update(server_config)
    cherrypy.tree.mount(SC3MicroApi(conn), '/sc3microapi')
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == "__main__":
    main()
    # cherrypy.engine.signals.subscribe()
    # cherrypy.engine.start()
    # cherrypy.engine.block()
