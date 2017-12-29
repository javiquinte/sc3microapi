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


def str2date(dStr):
    """Transform a string to a datetime.

    :param dStr: A datetime in ISO format.
    :type dStr: string
    :return: A datetime represented the converted input.
    :rtype: datetime
    """
    # In case of empty string
    if not len(dStr):
        return None

    dateParts = dStr.replace('-', ' ').replace('T', ' ')
    dateParts = dateParts.replace(':', ' ').replace('.', ' ')
    dateParts = dateParts.replace('Z', '').split()
    return datetime.datetime(*map(int, dateParts))


@cherrypy.expose
class AccessAPI(object):
    """Object dispatching methods related to access to streams."""

    def __init__(self, conn):
        """Constructor of the AccessAPI class."""
        self.conn = conn

    @cherrypy.expose
    def index(self, nslc, starttime, endtime, email):
        """Check if the user has access to a stream.

        :param nslc: Network.Station.Location.Channel
        :param type: str
        :returns: Data related to the available networks.
        :rtype: utf-8 encoded string
        :raises: cherrypy.HTTPError
        """
        cherrypy.response.headers['Content-Type'] = 'text/plain'

        # Check parameters
        try:
            nslc2 = nslc.split('.')
            if len(nslc2) != 4:
                raise Exception
        except:
            # Send Error 400
            messDict = {'code': 0,
                        'message': 'Wrong formatted NSLC code (%s).' % nslc}
            message = json.dumps(messDict)
            cherrypy.log(message, traceback=True)
            raise cherrypy.HTTPError(400, message)

        try:
            startt = str2date(starttime)
        except:
            # Send Error 400
            messDict = {'code': 0,
                        'message': 'Error converting the "starttime" parameter (%s).' % starttime}
            message = json.dumps(messDict)
            cherrypy.log(message, traceback=True)
            raise cherrypy.HTTPError(400, message)

        try:
            endt = str2date(endtime)
        except:
            # Send Error 400
            messDict = {'code': 0,
                        'message': 'Error converting the "endtime" parameter (%s).' % endtime}
            message = json.dumps(messDict)
            cherrypy.log(message, traceback=True)
            raise cherrypy.HTTPError(400, message)

        try:
            self.cursor = self.conn.cursor()
            query = 'select restricted from Network where code="%s" and start<="%s" and (end>="%s" or end is NULL)' \
                    % (nslc2[0], starttime, endtime)
            self.cursor.execute(query)
            result = self.cursor.fetchone()

            if (result is not None) and (result[0] == 0):
                return ''.encode('utf-8')

            query = ('select count(*) from Access where networkCode="{}" and stationCode="{}" and locationCode="{}" '
                     'and streamCode="{}" and "{}" LIKE concat("%", user, "%")').format(nslc2[0], nslc2[1], nslc2[2],
                                                                                        nslc2[3], email)
            self.cursor.execute(query)
            result = self.cursor.fetchone()

            if (result is not None) and (result[0] > 0):
                return ''.encode('utf-8')

            query = ('select count(*) from Access where networkCode="{}" and stationCode="{}" and locationCode="{}" '
                     'and streamCode="" and "{}" LIKE concat("%", user, "%")').format(nslc2[0], nslc2[1], nslc2[2],
                                                                                      email)
            self.cursor.execute(query)
            result = self.cursor.fetchone()

            if (result is not None) and (result[0] > 0):
                return ''.encode('utf-8')

            query = ('select count(*) from Access where networkCode="{}" and stationCode="{}" and locationCode="" '
                     'and streamCode="" and "{}" LIKE concat("%", user, "%")').format(nslc2[0], nslc2[1], email)
            self.cursor.execute(query)
            result = self.cursor.fetchone()

            if (result is not None) and (result[0] > 0):
                return ''.encode('utf-8')

            query = ('select count(*) from Access where networkCode="{}" and stationCode="" and locationCode="" '
                     'and streamCode="" and "{}" LIKE concat("%", user, "%")').format(nslc2[0], email)
            self.cursor.execute(query)
            result = self.cursor.fetchone()

            if (result is not None) and (result[0] > 0):
                return ''.encode('utf-8')

            # Send Error 403
            messDict = {'code': 0,
                        'message': 'Access to {} denied for {}.'.format(nslc, email)}
            message = json.dumps(messDict)
            cherrypy.log(message, traceback=True)
            raise cherrypy.HTTPError(403, message)

        except:
            # Send Error 404
            messDict = {'code': 0,
                        'message': 'Error while querying the access to data.'}
            message = json.dumps(messDict)
            cherrypy.log(message, traceback=True)
            raise cherrypy.HTTPError(404, message)


@cherrypy.expose
@cherrypy.popargs('net')
class NetworksAPI(object):
    """Object dispatching methods related to networks."""

    def __init__(self, conn):
        """Constructor of the IngestAPI class."""
        self.conn = conn

    @cherrypy.expose
    def index(self, net=None, outformat='json', restricted=None, archive=None,
              netclass=None, starttime=None, endtime=None):
        """List available networks in the system.

        :param net: Network code
        :type net: str
        :param outformat: Output format (json, text)
        :type outformat: str
        :param restricted: Restricted status of the Network ('0' or '1')
        :type restricted: str
        :param archive: Institution archiving the network
        :type archive: str
        :param netclass: Tpye of network (permanent 'p' or temporary 't')
        :type netclass: str
        :param starttime: Start time in isoformat
        :type starttime: str
        :param endtime: End time in isoformat
        :type endtime: str
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

        if starttime is not None:
            try:
                startt = str2date(starttime)
            except:
                # Send Error 400
                messDict = {'code': 0,
                            'message': 'Error converting the "starttime" parameter (%s).' % starttime}
                message = json.dumps(messDict)
                cherrypy.log(message, traceback=True)
                raise cherrypy.HTTPError(400, message)

        if endtime is not None:
            try:
                endt = str2date(endtime)
            except:
                # Send Error 400
                messDict = {'code': 0,
                            'message': 'Error converting the "endtime" parameter (%s).' % endtime}
                message = json.dumps(messDict)
                cherrypy.log(message, traceback=True)
                raise cherrypy.HTTPError(400, message)

        try:
            self.cursor = self.conn.cursor()
            query = 'select code, start, end, netClass, archive, restricted from Network'

            whereclause = []
            if net is not None:
                whereclause.append('code="%s"' % net)

            if restricted is not None:
                whereclause.append('restricted=%d' % restricted)

            if archive is not None:
                whereclause.append('archive="%s"' % archive)

            if netclass is not None:
                whereclause.append('netClass="%s"' % netclass)

            if starttime is not None:
                whereclause.append('start>="%s"' % starttime)

            if endtime is not None:
                whereclause.append('end<="%s"' % endtime)

            if len(whereclause):
                query = query + ' where ' + ' and '.join(whereclause)

            self.cursor.execute(query)

            if outformat == 'json':
                return json.dumps(self.cursor.fetchall(), default=datetime.datetime.isoformat).encode('utf-8')
            elif outformat == 'text':
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
        self.access = AccessAPI(conn)

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
